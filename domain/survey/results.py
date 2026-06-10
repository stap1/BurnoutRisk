"""Obiekty wynikowe scoringu (domena, czyste value objects).

`AreaScore` - wynik pojedynczego obszaru A-F (spec §3.3). `ScoringResult`
(pełny wynik) dojdzie w Prompcie 1.5.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.common import AreaStatus


class AreaScore(BaseModel):
    """Wynik obszaru w jednej sesji.

    `score` to liczba 0-100 dla obszaru ocenionego (`status = RATED`), albo `None`
    gdy obszar nie przekroczył progu minimalnej liczby odpowiedzi
    (`status = INSUFFICIENT_DATA`). `answered`/`question_count` niosą kontekst
    braków (przydatne dla neutralnej prezentacji "za mało danych").
    """

    model_config = ConfigDict(frozen=True)

    category_id: str
    score: float | None
    status: AreaStatus
    answered: int
    question_count: int
