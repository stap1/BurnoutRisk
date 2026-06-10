"""Biblioteka mikro-działań coachingu (Prompt 4.1) - encje domenowe, zero I/O.

Działania pokrywają obszary B-F (spec §6.2). Obszar A świadomie NIE ma działań -
wysoki wynik A uruchamia ścieżkę specjalną (eskalacja), nie mikro-coaching (§7).
Wczytanie z `coach_actions.json` to zadanie infrastruktury; tu żyje struktura i jej
walidacja oraz proste zapytania używane przez generator.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from domain.common import Goal

# Obszary, dla których w ogóle generujemy mikro-działania (A wykluczone regułą §7).
OBSZARY_DZIALAN = ("B", "C", "D", "E", "F")
DOZWOLONE_BUDZETY = (5, 10, 15)


class CoachAction(BaseModel):
    """Pojedyncze mikro-działanie z biblioteki."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    area: str
    action_type: str
    minutes: int
    goal: Goal | None
    text: str


class CoachActionLibrary(BaseModel):
    """Zbiór mikro-działań + walidacja pokrycia obszarów i budżetów."""

    model_config = ConfigDict(frozen=True)

    actions: tuple[CoachAction, ...]

    @model_validator(mode="after")
    def _waliduj(self) -> CoachActionLibrary:
        if not self.actions:
            raise ValueError("Biblioteka działań jest pusta.")

        ids = [a.id for a in self.actions]
        if len(ids) != len(set(ids)):
            raise ValueError("Identyfikatory działań nie są unikalne.")

        for a in self.actions:
            if a.area not in OBSZARY_DZIALAN:
                raise ValueError(
                    f"Działanie {a.id}: obszar {a.area!r} spoza B-F "
                    f"(obszar A nie generuje mikro-działań - §7)."
                )
            if a.minutes not in DOZWOLONE_BUDZETY:
                raise ValueError(
                    f"Działanie {a.id}: czas {a.minutes} spoza {DOZWOLONE_BUDZETY}."
                )
            if not a.text.strip():
                raise ValueError(f"Działanie {a.id}: pusta treść.")

        # Pokrycie: każdy obszar B-F ma działanie w każdym budżecie (gwarancja, że
        # generator zawsze dobierze coś pod wybrany budżet czasu).
        for obszar in OBSZARY_DZIALAN:
            dostepne = {a.minutes for a in self.actions if a.area == obszar}
            brak = set(DOZWOLONE_BUDZETY) - dostepne
            if brak:
                raise ValueError(
                    f"Obszar {obszar} nie ma działań dla budżetów: {sorted(brak)}."
                )

        return self

    @classmethod
    def from_dict(cls, raw: dict) -> CoachActionLibrary:
        if not isinstance(raw, dict) or not isinstance(raw.get("dzialania"), list):
            raise ValueError("Definicja biblioteki wymaga listy 'dzialania'.")
        try:
            actions = tuple(
                CoachAction(
                    id=d["id"],
                    area=d["obszar"],
                    action_type=d["typ"],
                    minutes=d["czas"],
                    goal=Goal(d["cel"]) if d.get("cel") else None,
                    text=d["tresc"],
                )
                for d in raw["dzialania"]
            )
        except KeyError as exc:
            raise ValueError(f"Działanie pozbawione pola: {exc}.") from exc
        return cls(actions=actions)

    def for_area(self, area: str) -> tuple[CoachAction, ...]:
        return tuple(a for a in self.actions if a.area == area)

    def for_area_and_budget(self, area: str, minutes: int) -> tuple[CoachAction, ...]:
        """Działania danego obszaru mieszczące się w budżecie (czas <= budżet).

        Posortowane malejąco po czasie (najpierw najpełniej wykorzystujące budżet),
        z deterministycznym rozstrzygnięciem po id.
        """
        pasujace = [
            a for a in self.actions if a.area == area and a.minutes <= minutes
        ]
        pasujace.sort(key=lambda a: (-a.minutes, a.id))
        return tuple(pasujace)
