"""Porty repozytoriów (abstrakcyjne interfejsy) - warstwa aplikacji.

Application definiuje porty i zależy WYŁĄCZNIE od domeny; nie wie nic o SQLite.
Konkretne implementacje (Faza 3+) żyją w infrastrukturze i są wiązane w
composition root. Porty rosną wraz z kolejnymi fazami - to świadoma decyzja, nie
zmiana istniejącego kontraktu bez powodu (spec §1.2.1).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime

from application.dto.survey import (
    SessionSummaryDTO,
    SurveyAnswersDTO,
    SurveyResultDTO,
)
from domain.survey import ScoringResult


class ISurveyRepository(ABC):
    """Trwałość sesji ankiety (sesja + odpowiedzi + wyniki obszarów)."""

    @abstractmethod
    def save_survey(
        self,
        *,
        answers: SurveyAnswersDTO,
        risk_scores: Mapping[str, int | None],
        result: ScoringResult,
        created_at: datetime,
    ) -> str:
        """Zapisuje sesję atomowo (Faza 3.3) i zwraca jej identyfikator.

        Sesja + wszystkie odpowiedzi (z `risk_score` po rekodowaniu) + wyniki
        obszarów w JEDNEJ transakcji; błąd → ROLLBACK (brak zapisu częściowego).
        """

    @abstractmethod
    def get_history(self) -> list[SessionSummaryDTO]:
        """Lista skrótów sesji (od najnowszej)."""

    @abstractmethod
    def get_session(self, session_id: str) -> SurveyResultDTO | None:
        """Pełny wynik sesji lub None, gdy nie istnieje."""


class ICoachRepository(ABC):
    """Trwałość planów coachingowych, działań, check-inów i outcome'ów (Faza 4)."""

    @abstractmethod
    def save_plan(self, plan: object) -> str:
        """Zapisuje plan i zwraca jego identyfikator. Typ planu doprecyzuje Faza 4."""

    @abstractmethod
    def get_latest_plan(self) -> object | None:
        """Najnowszy plan lub None."""

    @abstractmethod
    def save_checkin(self, checkin: object) -> str:
        """Zapisuje dzienny check-in (notatka szyfrowana w infrastrukturze)."""

    @abstractmethod
    def save_outcome(self, outcome: object) -> str:
        """Zapisuje okresową ocenę efektu (komentarz szyfrowany)."""


class IEducationRepository(ABC):
    """Trwałość postępu w module edukacyjnym (Faza 5)."""

    @abstractmethod
    def get_progress(self, topic_id: str) -> object | None:
        """Postęp dla tematu lub None."""

    @abstractmethod
    def upsert_progress(self, progress: object) -> None:
        """Zapisuje/aktualizuje postęp (first/last viewed, quiz_score)."""
