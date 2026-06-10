"""Testy kasowania selektywnego i pełnego wipe (Prompt 3.5)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import AnswerDTO, SurveyAnswersDTO
from domain.survey import ScoringEngine, SurveyDefinition
from infrastructure.persistence.database import init_database
from infrastructure.persistence.survey_repository import SqliteSurveyRepository
from infrastructure.persistence.wipe import WipeService

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"
STALY_CZAS = datetime(2026, 6, 10, 9, 30, 0)


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


@pytest.fixture
def conn(tmp_path: Path):
    c = init_database(tmp_path / "baza.db")
    yield c
    c.close()


class FakeKeyStore:
    def __init__(self) -> None:
        self.deleted = False

    def get_or_create_key(self) -> bytes:
        return b"0" * 32

    def delete_key(self) -> None:
        self.deleted = True

    def is_backend_safe(self) -> bool:
        return True


def _zapisz_sesje(conn, definicja: SurveyDefinition) -> str:
    engine = ScoringEngine(definicja)
    answers = SurveyAnswersDTO(
        answers=[AnswerDTO(question_id=q.id, raw_answer=2) for q in definicja.questions]
    )
    mapping = answers.to_raw_mapping()
    repo = SqliteSurveyRepository(conn, definicja)
    return repo.save_survey(
        answers=answers,
        risk_scores=engine.recode(mapping),
        result=engine.score(mapping),
        created_at=STALY_CZAS,
    )


def _wstaw_plan(conn, plan_id: str = "plan-1") -> None:
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO coach_plan(id, created_at, escalation_flag) VALUES(?, ?, 0)",
        (plan_id, "2026-06-10"),
    )
    conn.execute(
        "INSERT INTO coach_action(id, plan_id, description) VALUES('akcja-1', ?, 'x')",
        (plan_id,),
    )
    conn.execute("COMMIT")


# --- kasowanie selektywne ---


def test_delete_session_usuwa_sesje_i_zalezne(conn, definicja: SurveyDefinition) -> None:
    sid = _zapisz_sesje(conn, definicja)
    wipe = WipeService(conn, FakeKeyStore())

    assert wipe.delete_session(sid) is True
    assert conn.execute("SELECT COUNT(*) FROM survey_session").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM survey_answer").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM category_score").fetchone()[0] == 0


def test_delete_session_nieistniejaca_zwraca_false(conn, definicja: SurveyDefinition) -> None:
    wipe = WipeService(conn, FakeKeyStore())
    assert wipe.delete_session("nie-ma") is False


def test_delete_session_nie_rusza_innych(conn, definicja: SurveyDefinition) -> None:
    sid1 = _zapisz_sesje(conn, definicja)
    sid2 = _zapisz_sesje(conn, definicja)
    wipe = WipeService(conn, FakeKeyStore())
    wipe.delete_session(sid1)
    assert conn.execute(
        "SELECT COUNT(*) FROM survey_session WHERE id=?", (sid2,)
    ).fetchone()[0] == 1


def test_delete_plan_usuwa_plan_i_dzialania(conn) -> None:
    _wstaw_plan(conn)
    wipe = WipeService(conn, FakeKeyStore())
    assert wipe.delete_plan("plan-1") is True
    assert conn.execute("SELECT COUNT(*) FROM coach_plan").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM coach_action").fetchone()[0] == 0


# --- pełny wipe ---


def test_full_wipe_czysci_dane_i_usuwa_klucz(conn, definicja: SurveyDefinition) -> None:
    _zapisz_sesje(conn, definicja)
    _wstaw_plan(conn)
    ks = FakeKeyStore()
    wipe = WipeService(conn, ks)

    wipe.full_wipe()

    for tabela in (
        "survey_session", "survey_answer", "category_score",
        "coach_plan", "coach_action",
    ):
        assert conn.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0] == 0
    assert ks.deleted is True


def test_full_wipe_zachowuje_schema_version(conn, definicja: SurveyDefinition) -> None:
    _zapisz_sesje(conn, definicja)
    WipeService(conn, FakeKeyStore()).full_wipe()
    wersja = conn.execute(
        "SELECT value FROM app_meta WHERE key='schema_version'"
    ).fetchone()
    assert wersja is not None


def test_po_wipe_baza_jest_uzywalna(conn, definicja: SurveyDefinition) -> None:
    _zapisz_sesje(conn, definicja)
    WipeService(conn, FakeKeyStore()).full_wipe()
    # Czysty, uzywalny stan - mozna zapisac nowa sesje.
    sid = _zapisz_sesje(conn, definicja)
    assert conn.execute(
        "SELECT COUNT(*) FROM survey_session WHERE id=?", (sid,)
    ).fetchone()[0] == 1
