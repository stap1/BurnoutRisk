"""ReportService - agregacja danych do raportu/postępu (Prompt 8.1).

Buduje trendy (sesje + check-iny) oraz warstwę sprawczości (ukończone działania,
liczba check-inów, obszary poprawione/pogorszone). Cała prezentacja trendu
podlega zabezpieczeniom §6.3.1 - tu dostarczamy też dane sprawczości, by krzywej
nigdy nie pokazywać „nago".
"""

from __future__ import annotations

from application.dto.report import (
    AgencySummaryDTO,
    ProgressReportDTO,
    TrendPointDTO,
)
from application.ports.repositories import ICoachRepository, ISurveyRepository
from domain.coaching import CheckinPoint, TrendDetector


class ReportService:
    def __init__(
        self,
        survey_repository: ISurveyRepository,
        coach_repository: ICoachRepository,
        *,
        trend_detector: TrendDetector | None = None,
    ) -> None:
        self._survey_repo = survey_repository
        self._coach_repo = coach_repository
        self._trend = trend_detector or TrendDetector()

    def get_progress_report(self) -> ProgressReportDTO:
        return ProgressReportDTO(
            session_trend=self._session_trend(),
            checkin_trend=self._checkin_trend(),
            agency=self._agency(),
        )

    def _session_trend(self) -> list[TrendPointDTO]:
        # Historia jest od najnowszej - odwracamy na oś czasu rosnącą.
        sesje = list(reversed(self._survey_repo.get_history()))
        return [
            TrendPointDTO(label=s.created_at.date().isoformat(), value=s.total_score)
            for s in sesje
            if s.total_score is not None
        ]

    def _checkin_trend(self) -> list[TrendPointDTO]:
        checkiny = self._coach_repo.get_checkins(None)
        punkty = []
        for c in checkiny:
            wsk = self._trend.wellbeing_index(
                CheckinPoint(stress=c.stress, sleep=c.sleep, energy=c.energy)
            )
            punkty.append(TrendPointDTO(label=c.date, value=wsk))
        return punkty

    def _agency(self) -> AgencySummaryDTO:
        plan = self._coach_repo.get_latest_plan()
        total = len(plan.actions) if plan else 0
        completed = (
            sum(1 for a in plan.actions if a.completed_date is not None) if plan else 0
        )
        checkin_count = len(self._coach_repo.get_checkins(None))
        improved, worsened = self._porownaj_ostatnie_sesje()
        return AgencySummaryDTO(
            completed_actions=completed,
            total_actions=total,
            checkin_count=checkin_count,
            improved_areas=improved,
            worsened_areas=worsened,
        )

    def _porownaj_ostatnie_sesje(self) -> tuple[list[str], list[str]]:
        historia = self._survey_repo.get_history()  # najnowsza pierwsza
        if len(historia) < 2:
            return [], []
        nowsza = self._survey_repo.get_session(historia[0].session_id)
        starsza = self._survey_repo.get_session(historia[1].session_id)
        if nowsza is None or starsza is None:
            return [], []

        stare = {a.category_id: a for a in starsza.area_scores}
        improved: list[str] = []
        worsened: list[str] = []
        for a in nowsza.area_scores:
            s = stare.get(a.category_id)
            if s is None or a.score is None or s.score is None:
                continue
            # Niższy wynik = lepiej (mniejsze ryzyko).
            if a.score < s.score:
                improved.append(a.name)
            elif a.score > s.score:
                worsened.append(a.name)
        return improved, worsened
