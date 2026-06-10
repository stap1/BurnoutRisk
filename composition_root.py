"""Composition root - jedyne miejsce wiązania konkretnych implementacji.

Ręczna iniekcja zależności (bez frameworka DI): otwiera bazę, ładuje dane
statyczne, tworzy crypto/keyring i repozytoria z infrastruktury, składa serwisy
aplikacji i wstrzykuje wszystko do AppFacade.

Parametry (`db_path`, `keyring_backend`, `clock`) pozwalają testom budować fasadę
na bazie tymczasowej i z atrapą keyring, bez dotykania środowiska systemowego.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app_facade import AppFacade
from application.services import CoachService, EducationService, SurveyService
from infrastructure.crypto import AesGcmCryptoService, KeyringKeyStore
from infrastructure.persistence.coach_actions_loader import load_coach_actions
from infrastructure.persistence.coach_repository import SqliteCoachRepository
from infrastructure.persistence.crisis_resources_loader import load_crisis_resources
from infrastructure.persistence.database import init_database
from infrastructure.persistence.education_content_loader import load_education_content
from infrastructure.persistence.education_repository import SqliteEducationRepository
from infrastructure.persistence.survey_definition_loader import load_survey_definition
from infrastructure.persistence.survey_repository import SqliteSurveyRepository
from infrastructure.persistence.wipe import WipeService

DEFAULT_DB_PATH = Path.home() / ".burnout_risk_monitor" / "burnout.db"
KLUCZ_CRISIS_VERIFIED = "crisis_resources_verified_at"


def _set_app_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("BEGIN")
    try:
        conn.execute(
            "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)", (key, value)
        )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise


def build_app_facade(
    *,
    db_path: Path | str | None = None,
    keyring_backend: object | None = None,
    clock: Callable[[], datetime] | None = None,
) -> AppFacade:
    """Buduje gotową do użycia fasadę z wszystkimi zależnościami."""
    sciezka = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    conn = init_database(sciezka)

    zegar = clock or datetime.now

    # Dane statyczne (walidowane; brak safety-netu = błąd blokujący).
    definition = load_survey_definition()
    library = load_coach_actions()
    crisis = load_crisis_resources()
    education_content = load_education_content()

    # Klucz i szyfrowanie pól wrażliwych.
    key_store = KeyringKeyStore(backend=keyring_backend)  # type: ignore[arg-type]
    keyring_safe = key_store.is_backend_safe()
    crypto = AesGcmCryptoService(key_store.get_or_create_key())

    # Repozytoria (infrastruktura).
    survey_repo = SqliteSurveyRepository(conn, definition)
    coach_repo = SqliteCoachRepository(conn, crypto)
    education_repo = SqliteEducationRepository(conn)
    wipe_service = WipeService(conn, key_store)

    # Serwisy aplikacji.
    survey_service = SurveyService(definition, survey_repo, zegar)
    coach_service = CoachService(survey_repo, coach_repo, library, zegar)
    education_service = EducationService(education_content, education_repo, zegar)

    # Data weryfikacji zasobów kryzysowych do app_meta (reguła re-weryfikacji §8.2).
    _set_app_meta(conn, KLUCZ_CRISIS_VERIFIED, crisis.verified_at)

    return AppFacade(
        survey_definition=definition,
        survey_service=survey_service,
        coach_service=coach_service,
        education_service=education_service,
        crisis_resources=crisis,
        wipe_service=wipe_service,
        keyring_safe=keyring_safe,
    )
