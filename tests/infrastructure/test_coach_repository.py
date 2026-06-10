"""Testy integracyjne SqliteCoachRepository (Prompt 4.4)."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import CheckInDTO, OutcomeDTO
from domain.coaching import CoachPlanGenerator
from domain.common import AreaStatus, Goal, RiskBand
from domain.survey import AreaScore, ScoringResult
from infrastructure.crypto import KEY_BYTES, AesGcmCryptoService
from infrastructure.persistence.coach_actions_loader import load_coach_actions
from infrastructure.persistence.coach_repository import SqliteCoachRepository
from infrastructure.persistence.database import init_database

STALY_CZAS = datetime(2026, 6, 10, 8, 0, 0)


@pytest.fixture
def conn(tmp_path: Path):
    c = init_database(tmp_path / "baza.db")
    yield c
    c.close()


@pytest.fixture
def repo(conn) -> SqliteCoachRepository:
    return SqliteCoachRepository(conn, AesGcmCryptoService(os.urandom(KEY_BYTES)))


def _plan(based_on_session_id: str | None = None):
    wynik = ScoringResult(
        total_score=80.0,
        risk_band=RiskBand.VERY_HIGH,
        area_scores=(
            AreaScore(category_id="C", score=80.0, status=AreaStatus.RATED, answered=4, question_count=4),
        ),
        top_areas=("C",),
        unrated_areas=(),
    )
    gen = CoachPlanGenerator(load_coach_actions())
    return gen.generate(
        wynik, goal=Goal.STRES, daily_time_budget=10,
        based_on_session_id=based_on_session_id,
    )


def _wstaw_sesje(conn, sid: str = "sesja-1") -> str:
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO survey_session(id, started_at) VALUES(?, ?)", (sid, "2026-06-10")
    )
    conn.execute("COMMIT")
    return sid


def test_round_trip_planu_i_dzialan(repo: SqliteCoachRepository) -> None:
    plan = _plan()
    pid = repo.save_plan(plan, created_at=STALY_CZAS)

    odczyt = repo.get_plan(pid)
    assert odczyt is not None
    assert odczyt.goal == Goal.STRES
    assert odczyt.daily_time_budget == 10
    assert odczyt.based_on_session_id is None
    assert odczyt.escalation_flag is False
    assert odczyt.focus_areas == ["C"]
    assert len(odczyt.actions) == len(plan.actions)
    # Działania uporządkowane po dniu.
    assert [a.scheduled_day for a in odczyt.actions] == list(range(1, len(plan.actions) + 1))


def test_get_latest_plan(repo: SqliteCoachRepository) -> None:
    repo.save_plan(_plan(), created_at=datetime(2026, 6, 1, 8, 0))
    pid2 = repo.save_plan(_plan(), created_at=datetime(2026, 6, 9, 8, 0))
    najnowszy = repo.get_latest_plan()
    assert najnowszy is not None
    assert najnowszy.id == pid2


def test_get_plan_nieistniejacy_to_none(repo: SqliteCoachRepository) -> None:
    assert repo.get_plan("nie-ma") is None


def test_plan_linkuje_realna_sesje(repo: SqliteCoachRepository, conn) -> None:
    sid = _wstaw_sesje(conn)
    pid = repo.save_plan(_plan(based_on_session_id=sid), created_at=STALY_CZAS)
    odczyt = repo.get_plan(pid)
    assert odczyt is not None
    assert odczyt.based_on_session_id == sid


# --- check-iny z szyfrowaną notatką ---


def test_checkin_notatka_szyfrowana_round_trip(repo: SqliteCoachRepository, conn) -> None:
    pid = repo.save_plan(_plan(), created_at=STALY_CZAS)
    notatka = "Dziś było ciężko, ale zrobiłem przerwę. ąęó"
    cid = repo.save_checkin(
        CheckInDTO(plan_id=pid, date="2026-06-10", stress=7, sleep=4, energy=4, note=notatka)
    )

    odczyt = repo.get_checkins(pid)
    assert len(odczyt) == 1
    assert odczyt[0].id == cid
    assert odczyt[0].note == notatka  # odszyfrowane

    # W bazie notatka jest nieczytelnym BLOB-em (nie zawiera jawnego tekstu).
    raw = conn.execute("SELECT notes FROM coach_checkin WHERE id=?", (cid,)).fetchone()[0]
    assert isinstance(raw, bytes)
    assert notatka.encode("utf-8") not in raw


def test_checkin_bez_notatki(repo: SqliteCoachRepository) -> None:
    pid = repo.save_plan(_plan(), created_at=STALY_CZAS)
    repo.save_checkin(
        CheckInDTO(plan_id=pid, date="2026-06-10", stress=5, sleep=5, energy=5, note=None)
    )
    odczyt = repo.get_checkins(pid)
    assert odczyt[0].note is None


def test_checkin_bez_planu(repo: SqliteCoachRepository) -> None:
    # plan_id moze byc None (check-in niezwiazany z planem).
    repo.save_checkin(
        CheckInDTO(plan_id=None, date="2026-06-10", stress=5, sleep=5, energy=5)
    )
    wszystkie = repo.get_checkins()
    assert len(wszystkie) == 1
    assert wszystkie[0].plan_id is None


# --- outcome z szyfrowanym komentarzem ---


def test_outcome_komentarz_szyfrowany(repo: SqliteCoachRepository, conn) -> None:
    pid = repo.save_plan(_plan(), created_at=STALY_CZAS)
    komentarz = "Po dwóch tygodniach trochę lepiej."
    oid = repo.save_outcome(
        OutcomeDTO(plan_id=pid, date="2026-06-24", perceived_burnout=6, comments=komentarz)
    )

    odczyt = repo.get_outcomes(pid)
    assert len(odczyt) == 1
    assert odczyt[0].comments == komentarz
    raw = conn.execute("SELECT comments FROM coach_outcome WHERE id=?", (oid,)).fetchone()[0]
    assert komentarz.encode("utf-8") not in raw
