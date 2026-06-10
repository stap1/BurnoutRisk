"""ScoringEngine - rdzeń obliczeń ankiety (domena, ZERO I/O).

Algorytm jest czystą, deterministyczną funkcją: te same wejścia → ten sam wynik
(spec §3.2). Tutaj realizujemy **Krok 1 - rekodowanie odpowiedzi na risk_score**;
kolejne kroki (wynik obszaru, wynik całkowity, pasma) dochodzą w Promptach 1.3-1.5.

Rekodowanie (spec §3.2 krok 1):
- pytanie odwracane:      risk_score = 4 - raw_answer
- pytanie nieodwracane:   risk_score = raw_answer
- pytanie pominięte:      risk_score = None  (brak danych, NIE zero)
"""

from __future__ import annotations

from collections.abc import Mapping

from domain.survey.entities import SurveyDefinition

RAW_MIN = 0
RAW_MAX = 4


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
