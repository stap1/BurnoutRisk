"""Połączenie z bazą SQLite, schemat i ręczne wersjonowanie (Prompt 3.1).

Czysty `sqlite3` (bez ORM). Schemat wg spec §2.5; wersjonowanie wg §2.5.1:
`schema_version` w `app_meta`, migracje jako uporządkowana lista funkcji,
wykonywane w JEDNEJ transakcji i idempotentne (gate po numerze wersji).

Tryb WAL, `foreign_keys=ON` oraz `busy_timeout` ustawiane przy każdym połączeniu.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

# Domyślny czas oczekiwania na zwolnienie blokady (ms) - chroni zapis ankiety
# przed natychmiastowym "database is locked" (spec §4.4).
DEFAULT_BUSY_TIMEOUT_MS = 5000

KLUCZ_WERSJI = "schema_version"


def connect(path: Path | str) -> sqlite3.Connection:
    """Otwiera połączenie z ustawionymi pragmami.

    `isolation_level=None` (autocommit) - transakcjami sterujemy jawnie
    (BEGIN/COMMIT/ROLLBACK), co jest potrzebne dla atomowych migracji i zapisu.
    """
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute(f"PRAGMA busy_timeout={DEFAULT_BUSY_TIMEOUT_MS}")
    return conn


# Instrukcje DDL schematu początkowego (spec §2.5). Wykonywane pojedynczo, by nie
# zrywać ręcznej transakcji - `executescript` robiłby niejawny COMMIT.
_DDL_001: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS app_meta (
        key   TEXT PRIMARY KEY,
        value TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS survey_session (
        id                 TEXT PRIMARY KEY,
        started_at         TEXT,
        completed_at       TEXT,
        total_score        REAL,
        risk_band          TEXT,
        top_areas_json     TEXT,
        unrated_areas_json TEXT,
        app_version        TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS survey_answer (
        id          TEXT PRIMARY KEY,
        session_id  TEXT NOT NULL REFERENCES survey_session(id) ON DELETE CASCADE,
        question_id TEXT NOT NULL,
        raw_answer  INTEGER,
        risk_score  INTEGER,
        skipped     INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS category_score (
        id          TEXT PRIMARY KEY,
        session_id  TEXT NOT NULL REFERENCES survey_session(id) ON DELETE CASCADE,
        category_id TEXT NOT NULL,
        score       REAL,
        status      TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coach_plan (
        id                  TEXT PRIMARY KEY,
        created_at          TEXT,
        based_on_session_id TEXT REFERENCES survey_session(id) ON DELETE SET NULL,
        focus_areas_json    TEXT,
        goal                TEXT,
        daily_time_budget   INTEGER,
        escalation_flag     INTEGER NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coach_action (
        id             TEXT PRIMARY KEY,
        plan_id        TEXT NOT NULL REFERENCES coach_plan(id) ON DELETE CASCADE,
        action_type    TEXT,
        description    TEXT,
        scheduled_date TEXT,
        completed_date TEXT,
        rating         INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coach_checkin (
        id      TEXT PRIMARY KEY,
        plan_id TEXT REFERENCES coach_plan(id) ON DELETE CASCADE,
        date    TEXT,
        stress  INTEGER,
        sleep   INTEGER,
        energy  INTEGER,
        notes   BLOB
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS coach_outcome (
        id                TEXT PRIMARY KEY,
        plan_id           TEXT NOT NULL REFERENCES coach_plan(id) ON DELETE CASCADE,
        date              TEXT,
        perceived_burnout INTEGER,
        comments          BLOB
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS education_progress (
        topic_id        TEXT PRIMARY KEY,
        first_viewed_at TEXT,
        last_viewed_at  TEXT,
        quiz_score      INTEGER
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_answer_session ON survey_answer(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_catscore_session ON category_score(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_action_plan ON coach_action(plan_id)",
    "CREATE INDEX IF NOT EXISTS idx_checkin_plan ON coach_checkin(plan_id)",
    "CREATE INDEX IF NOT EXISTS idx_outcome_plan ON coach_outcome(plan_id)",
)


def _migracja_001_schemat_poczatkowy(conn: sqlite3.Connection) -> None:
    """Tworzy komplet tabel wg spec §2.5."""
    for ddl in _DDL_001:
        conn.execute(ddl)


# Uporządkowana lista migracji. Numer wersji = indeks + 1.
MIGRATIONS: list[Callable[[sqlite3.Connection], None]] = [
    _migracja_001_schemat_poczatkowy,
]

EXPECTED_SCHEMA_VERSION = len(MIGRATIONS)


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Zwraca aktualną wersję schematu (0, gdy baza niemigrowana)."""
    try:
        row = conn.execute(
            "SELECT value FROM app_meta WHERE key = ?", (KLUCZ_WERSJI,)
        ).fetchone()
    except sqlite3.OperationalError:
        return 0  # brak tabeli app_meta - baza świeża
    return int(row[0]) if row and row[0] is not None else 0


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
        (KLUCZ_WERSJI, str(version)),
    )


def apply_migrations(conn: sqlite3.Connection) -> int:
    """Uruchamia brakujące migracje w jednej transakcji. Idempotentne.

    Zwraca wersję schematu po migracji. Ponowne wywołanie na aktualnej bazie nie
    robi nic (gate po numerze wersji). Błąd w trakcie → ROLLBACK (brak stanu
    pośredniego).
    """
    current = get_schema_version(conn)
    target = EXPECTED_SCHEMA_VERSION
    if current >= target:
        return current

    try:
        conn.execute("BEGIN")
        for i in range(current, target):
            MIGRATIONS[i](conn)
            _set_schema_version(conn, i + 1)
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    return target


def init_database(path: Path | str) -> sqlite3.Connection:
    """Otwiera połączenie i doprowadza schemat do oczekiwanej wersji."""
    conn = connect(path)
    apply_migrations(conn)
    return conn
