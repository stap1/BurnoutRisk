"""ScoringEngine - rdzeń obliczeń ankiety (domena, ZERO I/O).

Algorytm jest czystą, deterministyczną funkcją: te same wejścia → ten sam wynik
(spec §3.2). Tutaj realizujemy **Krok 1 - rekodowanie odpowiedzi na risk_score**;
kolejne kroki (wynik obszaru, wynik całkowity, pasma) dochodzą w Promptach 1.3-1.5.

Rekodowanie (spec §3.2 krok 1):
- pytanie odwracane:      risk_score = 4 - raw_answer
- pytanie nieodwracane:   risk_score = raw_answer
- pytanie pominięte:      risk_score = None  (brak danych, NIE zero)

Wynik obszaru (spec §3.2 krok 2-3):
- S_obszar = (avg(risk_score udzielonych) / 4) * 100
- obszar oceniany, gdy udzielono >= ceil(liczba_pytań / 2) odpowiedzi
  (A/B/C: min 2 z 4; D/E/F: min 2 z 3); poniżej -> INSUFFICIENT_DATA, score=None.
"""

from __future__ import annotations

from collections.abc import Mapping
from math import ceil

from domain.common import AreaStatus
from domain.survey.entities import SurveyDefinition
from domain.survey.results import AreaScore

RAW_MIN = 0
RAW_MAX = 4


def min_required_answers(question_count: int) -> int:
    """Próg minimalnej liczby odpowiedzi: co najmniej połowa, zaokrąglona w górę."""
    return ceil(question_count / 2)


def recode_raw_answer(raw_answer: int | None, *, is_reversed: bool) -> int | None:
    """Rekoduje pojedynczą surową odpowiedź na risk_score (0-4) lub None.

    `raw_answer is None` oznacza brak odpowiedzi (świadome pominięcie lub jej brak)
    i daje `None` - NIGDY zero, bo zero to realna, najniższa wartość ryzyka.
    """
    if raw_answer is None:
        return None
    # bool jest podtypem int - odrzucamy, by uniknąć cichych pomyłek (True == 1).
    if isinstance(raw_answer, bool) or not isinstance(raw_answer, int):
        raise ValueError(f"raw_answer musi być int 0-4 lub None, otrzymano {raw_answer!r}.")
    if not RAW_MIN <= raw_answer <= RAW_MAX:
        raise ValueError(f"raw_answer poza zakresem {RAW_MIN}-{RAW_MAX}: {raw_answer}.")
    return RAW_MAX - raw_answer if is_reversed else raw_answer


class ScoringEngine:
    """Silnik scoringu związany z konkretną definicją ankiety.

    Bezstanowy względem danych użytkownika - przechowuje tylko definicję (pytania,
    flagi odwracania). Wszystkie metody są czyste i deterministyczne.
    """

    def __init__(self, definition: SurveyDefinition) -> None:
        self._definition = definition

    def recode(self, raw_answers: Mapping[str, int | None]) -> dict[str, int | None]:
        """Rekoduje komplet odpowiedzi na risk_score per pytanie.

        Wynik zawiera wpis dla KAŻDEGO pytania definicji; brakujące w wejściu
        pytanie traktujemy jak pominięte (None). Nieznany identyfikator pytania
        w wejściu to błąd (ochrona przed literówką/desynchronizacją danych).
        """
        znane = {q.id for q in self._definition.questions}
        nieznane = set(raw_answers) - znane
        if nieznane:
            raise ValueError(f"Nieznane identyfikatory pytań: {sorted(nieznane)}.")

        return {
            q.id: recode_raw_answer(raw_answers.get(q.id), is_reversed=q.is_reversed)
            for q in self._definition.questions
        }

    def area_scores(
        self, raw_answers: Mapping[str, int | None]
    ) -> dict[str, AreaScore]:
        """Liczy wynik każdego obszaru A-F z progiem minimalnej liczby odpowiedzi.

        Zwraca wpis dla każdej kategorii definicji. Obszar poniżej progu dostaje
        `status = INSUFFICIENT_DATA` i `score = None` (nie wchodzi do wyniku
        całkowitego - patrz Prompt 1.4). Średnia liczona wyłącznie z udzielonych
        odpowiedzi (pominięte/None są ignorowane, nie liczą się jako zero).
        """
        recoded = self.recode(raw_answers)

        wyniki: dict[str, AreaScore] = {}
        for c in self._definition.categories:
            udzielone = [
                recoded[qid] for qid in c.question_ids if recoded[qid] is not None
            ]
            liczba_pytan = len(c.question_ids)

            if len(udzielone) >= min_required_answers(liczba_pytan):
                srednia = sum(udzielone) / len(udzielone)
                score = (srednia / RAW_MAX) * 100
                status = AreaStatus.RATED
            else:
                score = None
                status = AreaStatus.INSUFFICIENT_DATA

            wyniki[c.id] = AreaScore(
                category_id=c.id,
                score=score,
                status=status,
                answered=len(udzielone),
                question_count=liczba_pytan,
            )
        return wyniki

    def total_score(
        self, raw_answers: Mapping[str, int | None]
    ) -> float | None:
        """Wynik całkowity 0-100 z renormalizacją wag (spec §3.2 krok 4).

        Średnia ważona wyłącznie obszarów ocenionych (`RATED`), z mianownikiem =
        suma wag obszarów ocenionych. Renormalizacja sprawia, że obszar pominięty
        (INSUFFICIENT_DATA) NIE zaniża wyniku - nie wchodzi ani do licznika, ani
        do mianownika. Gdy żaden obszar nie jest oceniony -> None ("za mało danych").
        """
        obszary = self.area_scores(raw_answers)
        wagi = {c.id: c.weight for c in self._definition.categories}

        licznik = 0.0
        mianownik = 0
        for area in obszary.values():
            if area.status is AreaStatus.RATED and area.score is not None:
                licznik += wagi[area.category_id] * area.score
                mianownik += wagi[area.category_id]

        if mianownik == 0:
            return None
        return licznik / mianownik
