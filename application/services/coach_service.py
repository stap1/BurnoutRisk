"""CoachService - orkiestracja coachingu (Prompt 6.1).

Spina generator planu, repozytorium coachingu, repozytorium ankiety (profil bazowy)
i detektor trendu. Czas wstrzykiwany. Zwraca DTO.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from application.dto.coach import (
    CheckInDTO,
    CheckInResultDTO,
    CoachConfigDTO,
    CoachPlanDTO,
)
from application.ports.repositories import ICoachRepository, ISurveyRepository
from domain.coaching import (
    CheckinPoint,
    CoachActionLibrary,
    CoachPlanGenerator,
    TrendDetector,
)
from domain.common import AreaStatus
from domain.survey import AreaScore, ScoringResult
from application.dto.survey import SurveyResultDTO


class CoachService:
    def __init__(
        self,
        survey_repository: ISurveyRepository,
        coach_repository: ICoachRepository,
        library: CoachActionLibrary,
        clock: Callable[[], datetime],
        *,
        trend_detector: TrendDetector | None = None,
    ) -> None:
        self._survey_repo = survey_repository
        self._coach_repo = coach_repository
        self._generator = CoachPlanGenerator(library)
        self._trend = trend_detector or TrendDetector()
        self._clock = clock

    def create_plan(self, config: CoachConfigDTO) -> CoachPlanDTO:
        sesja = self._survey_repo.get_session(config.based_on_session_id)
        if sesja is None:
            raise ValueError(f"Nie znaleziono sesji: {config.based_on_session_id}")

        result = self._adapt_result(sesja)
        plan = self._generator.generate(
            result,
            goal=config.goal,
            daily_time_budget=config.daily_time_budget,
            based_on_session_id=config.based_on_session_id,
        )
        plan_id = self._coach_repo.save_plan(plan, created_at=self._clock())
        zapisany = self._coach_repo.get_plan(plan_id)
        assert zapisany is not None  # właśnie zapisany
        return zapisany

    def get_latest_plan(self) -> CoachPlanDTO | None:
        return self._coach_repo.get_latest_plan()

    def submit_checkin(self, checkin: CheckInDTO) -> CheckInResultDTO:
        checkin_id = self._coach_repo.save_checkin(checkin)
        # Sprawdzenie trendu inicjowane wejściem użytkownika (nigdy w tle).
        seria = self._coach_repo.get_checkins(checkin.plan_id)
        punkty = [
            CheckinPoint(stress=c.stress, sleep=c.sleep, energy=c.energy)
            for c in seria
        ]
        trend = self._trend.detect(punkty)
        return CheckInResultDTO(
            checkin_id=checkin_id,
            trend_enough_data=trend.enough_data,
            trend_worsening=trend.worsening,
            trend_suggestion=trend.suggestion,
        )

    @staticmethod
    def _adapt_result(sesja: SurveyResultDTO) -> ScoringResult:
        """Buduje domenowy ScoringResult z zapisanego wyniku sesji (DTO).

        Generator korzysta z `category_id`, `status` i `score` obszarów - pozostałe
        pola (answered/question_count) nie wpływają na plan, więc są neutralne.
        """
        area_scores = tuple(
            AreaScore(
                category_id=a.category_id,
                score=a.score,
                status=a.status,
                answered=0,
                question_count=0,
            )
            for a in sesja.area_scores
        )
        return ScoringResult(
            total_score=sesja.total_score,
            risk_band=sesja.risk_band,
            area_scores=area_scores,
            top_areas=tuple(sesja.top_areas),
            unrated_areas=tuple(sesja.unrated_areas),
        )
