"""Regresja #6: get_history ma deterministyczną kolejność (tie-breaker po id)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import AnswerDTO, SurveyAnswersDTO
from application.services import SurveyService
from domain.survey import SurveyDefinition
from infrastructure.persistence.database import init_database
from infrastructure.persistence.survey_repository import SqliteSurveyRepository

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"
TEN_SAM_CZAS = datetime(2026, 6, 5, 12, 0, 0)


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    return SurveyDefinition.from_dict(
        json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    )


def test_kolejnosc_stabilna_przy_rownym_started_at(tmp_path: Path, definicja: SurveyDefinition) -> None:
    conn = init_database(tmp_path / "b.db")
    try:
        repo = SqliteSurveyRepository(conn, definicja)
        svc = SurveyService(definicja, repo, lambda: TEN_SAM_CZAS)
        for _ in range(3):
            svc.submit_survey(
                SurveyAnswersDTO(
                    answers=[AnswerDTO(question_id=q.id, raw_answer=2) for q in definicja.questions]
                )
            )
        # Trzy sesje z IDENTYCZNYM started_at - kolejność musi być deterministyczna
        # (powtarzalna), dzięki wtórnemu sortowaniu po id.
        h1 = [s.session_id for s in repo.get_history()]
        h2 = [s.session_id for s in repo.get_history()]
        assert h1 == h2
        assert h1 == sorted(h1, reverse=True)  # id DESC
    finally:
        conn.close()
