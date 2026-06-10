"""CoachPlanGenerator - deterministyczny generator planu 14-dniowego (Prompt 4.2).

Wejście: profil obszarów (ScoringResult) + cel + budżet czasu. Wyjście: stały plan
(te same wejścia → ten sam plan; determinizm = pełna testowalność, spec §6.1).

Reguła progowa (spec §6.2): obszar oceniony z wynikiem > próg (baza 60, KONFIGUROWALNA
stała per obszar) staje się priorytetowy. Dla B-F generujemy mikro-działania z
biblioteki, dopasowane do budżetu. **Obszar A jest inny (spec §7):** wysoki wynik A
NIE generuje mikro-działań - ustawia `escalation_flag` i kieruje do ścieżki specjalnej
(eskalacja + safety-net). Aplikacja nie udaje, że 14 dni ćwiczeń rozwiązuje mobbing.
"""

from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from domain.coaching.actions import OBSZARY_DZIALAN, CoachActionLibrary
from domain.common import AreaStatus, Goal
from domain.survey import ScoringResult

PLAN_DAYS = 14
BASE_THRESHOLD = 60.0
OBSZAR_ESKALACJI = "A"

# Stała informacja dołączana do każdego planu (spec §6.2 - wymóg tonu).
SAFETY_NOTE = (
    "Jeśli objawy są nasilone lub utrzymują się, rozważ kontakt ze specjalistą."
)


class PlannedAction(BaseModel):
    """Mikro-działanie przypisane do konkretnego dnia planu."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    day: int
    action_id: str
    area: str
    action_type: str
    minutes: int
    text: str


class CoachPlan(BaseModel):
    """Wynik generatora: plan 14-dniowy + flaga eskalacji + nota bezpieczeństwa."""

    model_config = ConfigDict(frozen=True)

    based_on_session_id: str | None
    goal: Goal
    daily_time_budget: int
    focus_areas: tuple[str, ...]
    escalation_flag: bool
    actions: tuple[PlannedAction, ...]
    safety_note: str = SAFETY_NOTE


class CoachPlanGenerator:
    def __init__(self, library: CoachActionLibrary) -> None:
        self._library = library

    def generate(
        self,
        result: ScoringResult,
        *,
        goal: Goal,
        daily_time_budget: int,
        based_on_session_id: str | None = None,
        thresholds: Mapping[str, float] | None = None,
    ) -> CoachPlan:
        prog = self._progi(thresholds)

        # Obszary priorytetowe = ocenione z wynikiem > próg.
        priorytetowe = {
            a.category_id: a.score
            for a in result.area_scores
            if a.status is AreaStatus.RATED
            and a.score is not None
            and a.score > prog.get(a.category_id, BASE_THRESHOLD)
        }

        escalation = OBSZAR_ESKALACJI in priorytetowe

        # Obszary generujące działania: tylko B-F (A wykluczone regułą §7).
        obszary_dzialan = sorted(
            (a for a in priorytetowe if a in OBSZARY_DZIALAN),
            key=lambda a: (-priorytetowe[a], a),
        )

        actions = self._rozloz_dzialania(
            obszary_dzialan, goal=goal, budget=daily_time_budget
        )

        return CoachPlan(
            based_on_session_id=based_on_session_id,
            goal=goal,
            daily_time_budget=daily_time_budget,
            focus_areas=tuple(obszary_dzialan),
            escalation_flag=escalation,
            actions=actions,
        )

    # --- szczegóły ---

    @staticmethod
    def _progi(thresholds: Mapping[str, float] | None) -> dict[str, float]:
        progi = {obszar: BASE_THRESHOLD for obszar in ("A", *OBSZARY_DZIALAN)}
        if thresholds:
            progi.update(thresholds)
        return progi

    def _rozloz_dzialania(
        self, obszary: list[str], *, goal: Goal, budget: int
    ) -> tuple[PlannedAction, ...]:
        if not obszary:
            return ()

        # Kandydaci per obszar: dopasowani do budżetu, z preferencją celu (cel
        # pasujący najpierw - sort stabilny zachowuje porządek -czas,id z biblioteki).
        # Obszary bez pasujących działań (np. budżet mniejszy niż najkrótsze
        # działanie) są pomijane - chroni przed dzieleniem przez zero.
        kandydaci: dict[str, list] = {}
        aktywne: list[str] = []
        for obszar in obszary:
            baza = list(self._library.for_area_and_budget(obszar, budget))
            baza.sort(key=lambda a: 0 if a.goal == goal else 1)
            if baza:
                kandydaci[obszar] = baza
                aktywne.append(obszar)

        if not aktywne:
            return ()

        liczniki = {obszar: 0 for obszar in aktywne}
        n = len(aktywne)
        planned: list[PlannedAction] = []
        for dzien in range(1, PLAN_DAYS + 1):
            obszar = aktywne[(dzien - 1) % n]
            lista = kandydaci[obszar]
            akcja = lista[liczniki[obszar] % len(lista)]
            liczniki[obszar] += 1
            planned.append(
                PlannedAction(
                    day=dzien,
                    action_id=akcja.id,
                    area=akcja.area,
                    action_type=akcja.action_type,
                    minutes=akcja.minutes,
                    text=akcja.text,
                )
            )
        return tuple(planned)
