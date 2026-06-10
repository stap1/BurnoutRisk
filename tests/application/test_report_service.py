"""Testy ReportService - agregacja trendów i warstwy sprawczości (Prompt 8.1)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import AnswerDTO, CheckInDTO, CoachConfigDTO, SurveyAnswersDTO
from application.services import CoachService, ReportService, SurveyService
from domain.common import Goal
from domain.survey import SurveyDefinition
from infrastructure.crypto import KEY_BYTES, AesGcmCryptoService
from infrastructure.persistence.coach_actions_loader import load_coach_actions
from infrastructure.persistence.coach_repository import SqliteCoachRepository
from infrastructure.persistence.database import init_database
from infrastructure.persistence.survey_repository import SqliteSurveyRepository

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    return SurveyDefinition.from_dict(
        json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    )


@pytest.fixture
def srodowisko(tmp_path: Path, definicja: SurveyDefinition):
    import os

    conn = init_database(tmp_path / "b.db")
    survey_repo = SqliteSurveyRepository(conn, definicja)
    coach_repo = SqliteCoachRepository(conn, AesGcmCryptoService(os.urandom(KEY_BYTES)))
    yield conn, survey_repo, coach_repo
    conn.close()


def _zegar(dni: list[int]):
    it = iter(dni)

    def teraz() -> datetime:
        return datetime(2026, 6, next(it), 12, 0, 0)

    return teraz


def test_session_trend_rosnaco_w_czasie(srodowisko, definicja) -> None:  # noqa: ANN001
    conn, survey_repo, coach_repo = srodowisko
    svc = SurveyService(definicja, survey_repo, _zegar([1, 5, 9]))
    for raw in (1, 2, 3):
        svc.submit_survey(
            SurveyAnswersDTO(
                answers=[AnswerDTO(question_id=q.id, raw_answer=raw) for q in definicja.questions]
            )
        )
    report = ReportService(survey_repo, coach_repo).get_progress_report()
    # 3 sesje, od najstarszej; wynik rosnie (raw 1->2->3).
    assert len(report.session_trend) == 3
    wartosci = [p.value for p in report.session_trend]
    assert wartosci == sorted(wartosci)


def test_agency_liczy_dzialania_i_checkiny(srodowisko, definicja) -> None:  # noqa: ANN001
    conn, survey_repo, coach_repo = srodowisko
    survey = SurveyService(definicja, survey_repo, _zegar([1]))
    wynik = survey.submit_survey(
        SurveyAnswersDTO(
            answers=[
                AnswerDTO(question_id=q.id, raw_answer=4 if q.category == "C" else 0)
                for q in definicja.questions
            ]
        )
    )
    coach = CoachService(survey_repo, coach_repo, load_coach_actions(), _zegar([2, 3, 4]))
    plan = coach.create_plan(
        CoachConfigDTO(based_on_session_id=wynik.session_id, goal=Goal.STRES, daily_time_budget=10)
    )
    coach.update_action(plan.actions[0].id, completed=True, rating=5)
    coach.submit_checkin(
        CheckInDTO(plan_id=plan.id, date="2026-06-03", stress=6, sleep=5, energy=5)
    )

    report = ReportService(survey_repo, coach_repo).get_progress_report()
    assert report.agency.total_actions == 14
    assert report.agency.completed_actions == 1
    assert report.agency.checkin_count == 1
    assert len(report.checkin_trend) == 1


def test_porownanie_sesji_wskazuje_poprawe(srodowisko, definicja) -> None:  # noqa: ANN001
    conn, survey_repo, coach_repo = srodowisko
    svc = SurveyService(definicja, survey_repo, _zegar([1, 9]))
    # Sesja 1: wysokie ryzyko (raw 4 nieodwracane), sesja 2: niższe (raw 1).
    svc.submit_survey(
        SurveyAnswersDTO(
            answers=[AnswerDTO(question_id=q.id, raw_answer=4 if not _rev(q) else 0)
                     for q in definicja.questions]
        )
    )
    svc.submit_survey(
        SurveyAnswersDTO(
            answers=[AnswerDTO(question_id=q.id, raw_answer=1 if not _rev(q) else 3)
                     for q in definicja.questions]
        )
    )
    report = ReportService(survey_repo, coach_repo).get_progress_report()
    # Nowsza sesja ma nizsze wyniki -> obszary "poprawione".
    assert report.agency.improved_areas
    assert not report.agency.worsened_areas


def test_pusty_raport_nie_rzuca(srodowisko, definicja) -> None:  # noqa: ANN001
    conn, survey_repo, coach_repo = srodowisko
    report = ReportService(survey_repo, coach_repo).get_progress_report()
    assert report.session_trend == []
    assert report.checkin_trend == []
    assert report.agency.total_actions == 0


def _rev(q) -> bool:  # noqa: ANN001
    return q.id in {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}
