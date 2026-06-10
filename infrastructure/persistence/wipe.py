"""Operacje kasowania danych: selektywne i pełny wipe (Prompt 3.5, spec §2.4).

- Kasowanie selektywne: pojedyncza sesja ankiety lub pojedynczy plan coachingu
  (kaskada FK usuwa rekordy zależne).
- Pełny wipe: czyści wszystkie dane i USUWA klucz z keyring, pozostawiając czysty,
  używalny stan (schemat zostaje, by aplikacja działała dalej). To także cel
  ścieżki recovery "nie pamiętam PIN-u → reset" (spec §2.2.2).

Wszystkie operacje są transakcyjne (błąd → ROLLBACK).
"""

from __future__ import annotations

import sqlite3

from application.ports.security import IKeyStore
from infrastructure.persistence.database import KLUCZ_WERSJI

# Tabele danych użytkownika w kolejności child → parent (kaskada i tak zadziała,
# ale jawna kolejność jest odporna na wyłączone FK).
_TABELE_DANYCH = (
    "survey_answer",
    "category_score",
    "coach_action",
    "coach_checkin",
    "coach_outcome",
    "coach_plan",
    "survey_session",
    "education_progress",
)


class WipeService:
    def __init__(self, connection: sqlite3.Connection, key_store: IKeyStore) -> None:
        self._conn = connection
        self._key_store = key_store

    def delete_session(self, session_id: str) -> bool:
        """Usuwa sesję ankiety (kaskada: odpowiedzi + wyniki obszarów)."""
        return self._delete_one("survey_session", session_id)

    def delete_plan(self, plan_id: str) -> bool:
        """Usuwa plan coachingu (kaskada: działania, check-iny, outcome)."""
        return self._delete_one("coach_plan", plan_id)

    def full_wipe(self) -> None:
        """Czyści wszystkie dane i usuwa klucz z keyring (stan początkowy).

        Zachowuje `schema_version` w `app_meta`, by nie wymuszać ponownych migracji
        - baza pozostaje od razu używalna.
        """
        try:
            self._conn.execute("BEGIN")
            for tabela in _TABELE_DANYCH:
                self._conn.execute(f"DELETE FROM {tabela}")
            self._conn.execute(
                "DELETE FROM app_meta WHERE key != ?", (KLUCZ_WERSJI,)
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

        # Klucz kasujemy po udanym wyczyszczeniu danych.
        self._key_store.delete_key()

    def _delete_one(self, tabela: str, row_id: str) -> bool:
        try:
            self._conn.execute("BEGIN")
            cur = self._conn.execute(
                f"DELETE FROM {tabela} WHERE id = ?", (row_id,)
            )
            usuniete = cur.rowcount
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
        return usuniete > 0
