"""Testy SqliteSurveyRepository: round-trip i atomowość zapisu (Prompt 3.3)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import AnswerDTO, SurveyAnswersDTO
from domain.common import RiskBand
from domain.survey import ScoringEngine, SurveyDefinition
from infrastructure.persistence.database import init_database
from infrastructure.persistence.survey_repository import SqliteSurveyRepository

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


def _odpowiedzi(definicja: SurveyDefinition, raw: int = 2) -> SurveyAnswersDTO:
    return SurveyAnswersDTO(
        answers=[AnswerDTO(question_id=q.id, raw_answer=raw) for q in definicja.questions]
    )


def _zapisz(conn, definicja, answers, **kw):
    engine = ScoringEngine(definicja)
    mapping = answers.to_raw_mapping()
    repo = SqliteSurveyRepository(conn, definicja, **kw)
    return repo, repo.save_survey(
        answers=answers,
        risk_scores=engine.recode(mapping),
        result=engine.score(mapping),
        created_at=STALY_CZAS,
    )


def test_round_trip_zapis_odczyt(conn, definicja: SurveyDefinition) -> None:
    answers = _odpowiedzi(definicja, raw=2)  # wszystkie S=50 -> total=50 -> HIGH
    repo, sid = _zapisz(conn, definicja, answers)

    wynik = repo.get_session(sid)
    assert wynik is not None
    assert wynik.session_id == sid
    assert wynik.created_at == STALY_CZAS
    assert wynik.total_score == 50.0
    assert wynik.risk_band == RiskBand.HIGH
    assert {a.category_id for a in wynik.area_scores} == {"A", "B", "C", "D", "E", "F"}
    assert all(a.name for a in wynik.area_scores)


def test_zapisuje_wszystkie_odpowiedzi_z_risk_score(
    conn, definicja: SurveyDefinition
) -> None:
    answers = _odpowiedzi(definicja, raw=2)
    _zapisz(conn, definicja, answers)
    liczba = conn.execute("SELECT COUNT(*) FROM survey_answer").fetchone()[0]
    assert liczba == len(definicja.questions)
    # A4 jest odwracane: raw=2 -> risk_score = 4-2 = 2; A1 nieodwracane raw=2 -> 2.
    a4 = conn.execute(
        "SELECT risk_score FROM survey_answer WHERE question_id='A4'"
    ).fetchone()[0]
    assert a4 == 2


def test_zapisuje_wyniki_obszarow(conn, definicja: SurveyDefinition) -> None:
    _zapisz(conn, definicja, _odpowiedzi(definicja))
    liczba = conn.execute("SELECT COUNT(*) FROM category_score").fetchone()[0]
    assert liczba == 6


def test_skipped_zapisany_jako_null_i_flaga(conn, definicja: SurveyDefinition) -> None:
    answers = SurveyAnswersDTO(
        answers=[
            AnswerDTO(question_id="A1", raw_answer=None, skipped=True)
            if q.id == "A1"
            else AnswerDTO(question_id=q.id, raw_answer=2)
            for q in definicja.questions
        ]
    )
    _zapisz(conn, definicja, answers)
    row = conn.execute(
        "SELECT raw_answer, risk_score, skipped FROM survey_answer WHERE question_id='A1'"
    ).fetchone()
    assert row["raw_answer"] is None
    assert row["risk_score"] is None
    assert row["skipped"] == 1


def test_get_history_zwraca_skroty(conn, definicja: SurveyDefinition) -> None:
    repo, sid = _zapisz(conn, definicja, _odpowiedzi(definicja))
    historia = repo.get_history()
    assert len(historia) == 1
    assert historia[0].session_id == sid
    assert historia[0].total_score == 50.0


def test_get_session_nieistniejaca_to_none(conn, definicja: SurveyDefinition) -> None:
    repo = SqliteSurveyRepository(conn, definicja)
    assert repo.get_session("nie-ma") is None


def test_top_areas_round_trip(conn, definicja: SurveyDefinition) -> None:
    # A maksymalne, reszta nizej -> A w top_areas.
    answers = SurveyAnswersDTO(
        answers=[
            AnswerDTO(question_id=q.id, raw_answer=(0 if q.is_reversed else 4))
            if q.category == "A"
            else AnswerDTO(question_id=q.id, raw_answer=(4 if q.is_reversed else 0))
            for q in definicja.questions
        ]
    )
    repo, sid = _zapisz(conn, definicja, answers)
    wynik = repo.get_session(sid)
    assert wynik is not None
    assert wynik.top_areas[0] == "A"


# --- ATOMOWOŚĆ: błąd w trakcie -> ROLLBACK, brak zapisu częściowego ---


def test_blad_w_trakcie_zapisu_robi_rollback(conn, definicja: SurveyDefinition) -> None:
    # id_factory zwraca stały identyfikator -> druga odpowiedz narusza PRIMARY KEY
    # tabeli survey_answer w trakcie transakcji. Cala sesja musi sie wycofac.
    answers = _odpowiedzi(definicja, raw=2)
    with pytest.raises(Exception):
        _zapisz(conn, definicja, answers, id_factory=lambda: "staly-id")

    assert conn.execute("SELECT COUNT(*) FROM survey_session").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM survey_answer").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM category_score").fetchone()[0] == 0


def test_po_rollback_mozna_zapisac_ponownie(conn, definicja: SurveyDefinition) -> None:
    answers = _odpowiedzi(definicja, raw=2)
    with pytest.raises(Exception):
        _zapisz(conn, definicja, answers, id_factory=lambda: "staly-id")
    # Po nieudanym zapisie baza jest w czystym, uzywalnym stanie.
    repo, sid = _zapisz(conn, definicja, answers)
    assert repo.get_session(sid) is not None
