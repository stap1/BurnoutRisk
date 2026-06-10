"""Encje definicji ankiety (Prompt 1.1).

Czyste obiekty domenowe - ZERO I/O (zgodnie z twardą regułą warstwowania).
Wczytanie pliku `questions.json` to zadanie warstwy infrastruktury; tutaj żyje
tylko struktura danych i jej walidacja (`SurveyDefinition.from_dict`).

Model danych wg spec §3.1 i §3.3:
- `Question` (id, category, text, is_reversed, is_skippable, display_order)
- `Category` (id, name, weight, question_ids)
- `SurveyDefinition` (lista Question + Category)

Kluczowe rozróżnienie (spec §4.2): identyfikatory pytań (A1..F3) i przypisanie
do kategorii są STAŁE i niezależne od `display_order`. Kolejność wyświetlania to
osobna warstwa - scoring nigdy od niej nie zależy.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator


class Question(BaseModel):
    """Pojedyncze pytanie ankiety.

    `is_reversed` - pytanie odwracane (wysoki surowy wynik = niskie ryzyko,
    rekodowane w ScoringEngine). `is_skippable` - można świadomie pominąć
    ("wolę nie odpowiadać") na najcięższych pozycjach (spec §4.2).
    `display_order` - pozycja w kolejności wyświetlania, NIEZALEŻna od `id`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    category: str
    text: str
    is_reversed: bool = False
    is_skippable: bool = False
    display_order: int


class Category(BaseModel):
    """Obszar ankiety (A-F) z wagą i listą przypisanych pytań."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    name: str
    weight: int
    question_ids: tuple[str, ...]


class SurveyDefinition(BaseModel):
    """Kompletna definicja ankiety: kategorie + pytania.

    Walidacja spójności (suma wag = 100, unikalne id, każde pytanie w istniejącej
    kategorii, `display_order` jako permutacja 1..N) jest twardym warunkiem - błąd
    danych musi ujawnić się przy starcie, nie w trakcie scoringu.
    """

    model_config = ConfigDict(frozen=True)

    categories: tuple[Category, ...]
    questions: tuple[Question, ...]

    @model_validator(mode="after")
    def _waliduj_spojnosc(self) -> SurveyDefinition:
        if not self.questions:
            raise ValueError("Definicja ankiety nie zawiera żadnych pytań.")
        if not self.categories:
            raise ValueError("Definicja ankiety nie zawiera żadnych kategorii.")

        # Unikalne identyfikatory pytań.
        ids = [q.id for q in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Identyfikatory pytań nie są unikalne.")

        # Unikalne identyfikatory kategorii.
        cat_ids = [c.id for c in self.categories]
        if len(cat_ids) != len(set(cat_ids)):
            raise ValueError("Identyfikatory kategorii nie są unikalne.")
        cat_id_set = set(cat_ids)

        # Każde pytanie należy do istniejącej kategorii.
        for q in self.questions:
            if q.category not in cat_id_set:
                raise ValueError(
                    f"Pytanie {q.id} wskazuje na nieistniejącą kategorię {q.category!r}."
                )

        # Każda kategoria ma co najmniej jedno pytanie, a jej question_ids
        # zgadzają się z faktycznym przypisaniem pytań.
        for c in self.categories:
            faktyczne = tuple(q.id for q in self.questions if q.category == c.id)
            if not faktyczne:
                raise ValueError(f"Kategoria {c.id!r} nie ma przypisanych pytań.")
            if set(c.question_ids) != set(faktyczne):
                raise ValueError(
                    f"Lista question_ids kategorii {c.id!r} jest niespójna z pytaniami."
                )

        # Suma wag kategorii = 100 (spec §3.1).
        suma_wag = sum(c.weight for c in self.categories)
        if suma_wag != 100:
            raise ValueError(f"Suma wag kategorii wynosi {suma_wag}, oczekiwano 100.")

        # display_order to permutacja 1..N (unikalne, ciągłe, bez luk).
        kolejnosci = sorted(q.display_order for q in self.questions)
        if kolejnosci != list(range(1, len(self.questions) + 1)):
            raise ValueError(
                "Pola display_order muszą tworzyć ciągłą permutację 1..N bez powtórzeń."
            )

        return self

    @classmethod
    def from_dict(cls, raw: dict) -> SurveyDefinition:
        """Buduje definicję ze słownika (np. z wczytanego JSON-a). Bez I/O.

        Klucze w danych są w języku projektu (polski); mapujemy je tu na pola encji
        (angielskie wg spec §3.3). question_ids kategorii są wyprowadzane z pytań.
        """
        if not isinstance(raw, dict):
            raise ValueError("Definicja ankiety musi być obiektem (JSON object).")

        raw_kategorie = raw.get("kategorie")
        raw_pytania = raw.get("pytania")
        if not isinstance(raw_kategorie, list) or not isinstance(raw_pytania, list):
            raise ValueError(
                "Definicja ankiety wymaga list 'kategorie' oraz 'pytania'."
            )

        try:
            questions = tuple(
                Question(
                    id=p["id"],
                    category=p["kategoria"],
                    text=p["tresc"],
                    is_reversed=bool(p.get("odwracane", False)),
                    is_skippable=bool(p.get("pomijalne", False)),
                    display_order=p["kolejnosc"],
                )
                for p in raw_pytania
            )
        except KeyError as exc:
            raise ValueError(f"Pytanie pozbawione wymaganego pola: {exc}.") from exc

        # question_ids kategorii wyprowadzone z pytań (w kolejności wyświetlania).
        przypisane: dict[str, list[str]] = {}
        for q in sorted(questions, key=lambda q: q.display_order):
            przypisane.setdefault(q.category, []).append(q.id)

        try:
            categories = tuple(
                Category(
                    id=k["id"],
                    name=k["nazwa"],
                    weight=k["waga"],
                    question_ids=tuple(przypisane.get(k["id"], ())),
                )
                for k in raw_kategorie
            )
        except KeyError as exc:
            raise ValueError(f"Kategoria pozbawiona wymaganego pola: {exc}.") from exc

        return cls(categories=categories, questions=questions)

    def question_by_id(self, question_id: str) -> Question:
        for q in self.questions:
            if q.id == question_id:
                return q
        raise KeyError(question_id)

    def category_by_id(self, category_id: str) -> Category:
        for c in self.categories:
            if c.id == category_id:
                return c
        raise KeyError(category_id)

    @property
    def questions_in_display_order(self) -> tuple[Question, ...]:
        """Pytania posortowane wg `display_order` - na potrzeby prezentacji."""
        return tuple(sorted(self.questions, key=lambda q: q.display_order))
