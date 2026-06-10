"""Encje treści edukacyjnych (Prompt 5.2) - domena, zero I/O.

Fakty w treści zostały zweryfikowane u źródła (model trójczynnikowy Maslach;
WHO ICD-11: wypalenie jako zjawisko zawodowe, nie choroba). Ton: nie diagnozuje,
nie nazywa „wypalonym", nie przypisuje „etapu" (spec §9.3). Quiz sprawdza
zrozumienie treści, NIE jest narzędziem samooceny stanu.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

QUIZ_PYTANIA_NA_TEMAT = 5


class QuizQuestion(BaseModel):
    """Pytanie mini-quizu (sprawdzenie zrozumienia treści)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    question: str
    options: tuple[str, ...]
    correct_index: int

    @model_validator(mode="after")
    def _waliduj(self) -> QuizQuestion:
        if len(self.options) < 2:
            raise ValueError("Pytanie quizu wymaga co najmniej 2 odpowiedzi.")
        if not 0 <= self.correct_index < len(self.options):
            raise ValueError("Indeks poprawnej odpowiedzi poza zakresem.")
        return self


class EducationSection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    heading: str
    body: str


class EducationTopic(BaseModel):
    """Pojedynczy temat edukacyjny z sekcjami, podsumowaniem i quizem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    sections: tuple[EducationSection, ...]
    key_points: tuple[str, ...]
    when_to_seek_help: str
    quiz: tuple[QuizQuestion, ...]

    @model_validator(mode="after")
    def _waliduj(self) -> EducationTopic:
        if not self.sections:
            raise ValueError(f"Temat {self.id}: brak sekcji.")
        if not self.key_points:
            raise ValueError(f"Temat {self.id}: brak sekcji wazne_w_skrocie.")
        if not self.when_to_seek_help.strip():
            raise ValueError(f"Temat {self.id}: brak sekcji kiedy_szukac_pomocy.")
        if len(self.quiz) != QUIZ_PYTANIA_NA_TEMAT:
            raise ValueError(
                f"Temat {self.id}: quiz musi mieć {QUIZ_PYTANIA_NA_TEMAT} pytań."
            )
        return self


class EducationContent(BaseModel):
    """Komplet treści edukacyjnych + stałe zastrzeżenie."""

    model_config = ConfigDict(frozen=True)

    version: str
    disclaimer: str
    topics: tuple[EducationTopic, ...]

    @model_validator(mode="after")
    def _waliduj(self) -> EducationContent:
        if not self.topics:
            raise ValueError("Brak tematów edukacyjnych.")
        if not self.disclaimer.strip():
            raise ValueError("Brak zastrzeżenia o tym, że to nie diagnoza.")
        ids = [t.id for t in self.topics]
        if len(ids) != len(set(ids)):
            raise ValueError("Identyfikatory tematów nie są unikalne.")
        return self

    @classmethod
    def from_dict(cls, raw: dict) -> EducationContent:
        if not isinstance(raw, dict) or not isinstance(raw.get("tematy"), list):
            raise ValueError("Definicja treści wymaga listy 'tematy'.")
        try:
            topics = tuple(cls._temat_from_dict(t) for t in raw["tematy"])
            return cls(
                version=raw["wersja"],
                disclaimer=raw["zastrzezenie"],
                topics=topics,
            )
        except KeyError as exc:
            raise ValueError(f"Treść edukacyjna pozbawiona pola: {exc}.") from exc

    @staticmethod
    def _temat_from_dict(t: dict) -> EducationTopic:
        return EducationTopic(
            id=t["id"],
            title=t["tytul"],
            sections=tuple(
                EducationSection(heading=s["naglowek"], body=s["tresc"])
                for s in t["sekcje"]
            ),
            key_points=tuple(t["wazne_w_skrocie"]),
            when_to_seek_help=t["kiedy_szukac_pomocy"],
            quiz=tuple(
                QuizQuestion(
                    question=q["pytanie"],
                    options=tuple(q["odpowiedzi"]),
                    correct_index=q["poprawna"],
                )
                for q in t["quiz"]
            ),
        )

    def topic_by_id(self, topic_id: str) -> EducationTopic:
        for t in self.topics:
            if t.id == topic_id:
                return t
        raise KeyError(topic_id)
