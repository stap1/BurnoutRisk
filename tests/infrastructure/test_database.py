"""Testy integracyjne bazy: schemat, wersjonowanie, idempotentność (Prompt 3.1)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from infrastructure.persistence.database import (
    EXPECTED_SCHEMA_VERSION,
    apply_migrations,
    connect,
    get_schema_version,
    init_database,
)

OCZEKIWANE_TABELE = {
    "app_meta",
    "survey_session",
    "survey_answer",
    "category_score",
    "coach_plan",
    "coach_action",
    "coach_checkin",
    "coach_outcome",
    "education_progress",
}


def _tabele(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def test_init_tworzy_wszystkie_tabele(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    assert OCZEKIWANE_TABELE <= _tabele(conn)
    conn.close()


def test_init_ustawia_wersje_schematu(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    assert get_schema_version(conn) == EXPECTED_SCHEMA_VERSION
    assert EXPECTED_SCHEMA_VERSION >= 1
    conn.close()


def test_swieza_baza_ma_wersje_0(tmp_path: Path) -> None:
    conn = connect(tmp_path / "baza.db")
    assert get_schema_version(conn) == 0
    conn.close()


def test_migracje_sa_idempotentne(tmp_path: Path) -> None:
    sciezka = tmp_path / "baza.db"
    conn = init_database(sciezka)
    tabele_pierwsze = _tabele(conn)

    # Ponowne uruchomienie nie zmienia wersji ani schematu i nie rzuca.
    wersja = apply_migrations(conn)
    apply_migrations(conn)
    assert wersja == EXPECTED_SCHEMA_VERSION
    assert get_schema_version(conn) == EXPECTED_SCHEMA_VERSION
    assert _tabele(conn) == tabele_pierwsze
    conn.close()


def test_wal_jest_aktywny(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    tryb = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert tryb.lower() == "wal"
    conn.close()


def test_foreign_keys_wlaczone(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.close()


def test_busy_timeout_ustawiony(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    assert conn.execute("PRAGMA busy_timeout").fetchone()[0] > 0
    conn.close()


def test_fk_cascade_usuwa_odpowiedzi(tmp_path: Path) -> None:
    # Kontrola, ze klucze obce dzialaja: usuniecie sesji kasuje jej odpowiedzi.
    conn = init_database(tmp_path / "baza.db")
    conn.execute("BEGIN")
    conn.execute(
        "INSERT INTO survey_session(id, started_at) VALUES('s1', '2026-06-10')"
    )
    conn.execute(
        "INSERT INTO survey_answer(id, session_id, question_id, raw_answer, skipped)"
        " VALUES('a1', 's1', 'C1', 2, 0)"
    )
    conn.execute("COMMIT")

    conn.execute("DELETE FROM survey_session WHERE id='s1'")
    pozostale = conn.execute("SELECT COUNT(*) FROM survey_answer").fetchone()[0]
    assert pozostale == 0
    conn.close()


def test_wersja_w_app_meta_jako_tekst(tmp_path: Path) -> None:
    conn = init_database(tmp_path / "baza.db")
    row = conn.execute(
        "SELECT value FROM app_meta WHERE key='schema_version'"
    ).fetchone()
    assert row[0] == str(EXPECTED_SCHEMA_VERSION)
    conn.close()
