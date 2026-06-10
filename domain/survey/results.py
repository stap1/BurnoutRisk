"""Obiekty wynikowe scoringu (domena, czyste value objects).

`AreaScore` - wynik pojedynczego obszaru A-F. `ScoringResult` - pełny wynik
ankiety (spec §3.3).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from domain.common import AreaStatus, RiskBand


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


class ScoringResult(BaseModel):
    """Pełny wynik scoringu jednej sesji (spec §3.3).

    `total_score`/`risk_band` to `None`, gdy żaden obszar nie został oceniony.
    `area_scores` zawiera wpis dla każdego obszaru (A-F) w stałej kolejności.
    `top_areas` - obszary o najwyższym ryzyku (tylko RATED), napędzają profilowy
    ekran wyniku i generator planu. `unrated_areas` - obszary bez wystarczających
    danych (prezentowane neutralnie).
    """

    model_config = ConfigDict(frozen=True)

    total_score: float | None
    risk_band: RiskBand | None
    area_scores: tuple[AreaScore, ...]
    top_areas: tuple[str, ...]
    unrated_areas: tuple[str, ...]
