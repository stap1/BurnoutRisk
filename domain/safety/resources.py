"""Zasoby wsparcia (safety-net) - encje domenowe (Prompt 5.1).

Zgodnie ze spec §8.2: tylko zweryfikowane numery, BEZ sztywnych godzin w treści
(odsyłamy do strony organizacji). Data weryfikacji (`verified_at`) służy regule
okresowej re-weryfikacji - część zasobów jest finansowana z programów o określonym
horyzoncie. Wczytanie pliku to zadanie infrastruktury; brak/niepoprawność danych =
błąd blokujący (safety-net MUSI działać, §12.6).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class CrisisResource(BaseModel):
    """Pojedynczy punkt kontaktu wsparcia."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    number: str
    name: str
    description: str
    link: str


class CrisisResources(BaseModel):
    """Komplet zasobów wsparcia + metadane."""

    model_config = ConfigDict(frozen=True)

    version: str
    verified_at: str
    framing_message: str
    resources: tuple[CrisisResource, ...]

    @model_validator(mode="after")
    def _waliduj(self) -> CrisisResources:
        if not self.resources:
            raise ValueError("Brak zasobów wsparcia - safety-net nie może być pusty.")
        if not self.framing_message.strip():
            raise ValueError("Brak komunikatu ramowego safety-netu.")
        for r in self.resources:
            if not r.number.strip() or not r.name.strip() or not r.link.strip():
                raise ValueError(f"Niepełny zasób wsparcia: {r!r}.")
        return self

    @classmethod
    def from_dict(cls, raw: dict) -> CrisisResources:
        if not isinstance(raw, dict) or not isinstance(raw.get("zasoby"), list):
            raise ValueError("Definicja zasobów wymaga listy 'zasoby'.")
        try:
            resources = tuple(
                CrisisResource(
                    number=z["numer"],
                    name=z["nazwa"],
                    description=z["opis"],
                    link=z["link"],
                )
                for z in raw["zasoby"]
            )
            return cls(
                version=raw["wersja"],
                verified_at=raw["zweryfikowano"],
                framing_message=raw["komunikat"],
                resources=resources,
            )
        except KeyError as exc:
            raise ValueError(f"Zasób/metadane pozbawione pola: {exc}.") from exc
