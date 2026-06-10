"""SecurityService - włączanie/wyłączanie PIN i odblokowanie (Prompt 7.7).

Spina envelope encryption (Argon2id + AES-GCM) z magazynem klucza i flagą
`pin_enabled` w `app_meta`. Włączenie PIN nie zmienia samego klucza bazy - tylko
sposób jego przechowywania (jawny klucz znika, zostaje koperta). Dzięki temu dane
zaszyfrowane wcześniej pozostają odczytywalne po podaniu PIN.

Błędny PIN → WrongPinError; brak/uszkodzona koperta → KeyRecoveryNeeded
(ścieżka recovery, nigdy cichy crash).
"""

from __future__ import annotations

import sqlite3

from infrastructure.crypto.key_store import KeyringKeyStore
from infrastructure.crypto.pin import (
    Envelope,
    KeyRecoveryNeeded,
    unwrap_db_key,
    wrap_db_key,
)

KLUCZ_PIN_ENABLED = "pin_enabled"


class SecurityService:
    def __init__(self, connection: sqlite3.Connection, key_store: KeyringKeyStore) -> None:
        self._conn = connection
        self._key_store = key_store

    def is_pin_enabled(self) -> bool:
        row = self._conn.execute(
            "SELECT value FROM app_meta WHERE key = ?", (KLUCZ_PIN_ENABLED,)
        ).fetchone()
        return bool(row) and row[0] == "1"

    def enable_pin(self, pin: str) -> None:
        if self.is_pin_enabled():
            raise ValueError("PIN jest już włączony.")
        key = self._key_store.get_or_create_key()
        env = wrap_db_key(pin, key)
        self._key_store.store_envelope(env.salt, env.wrapped)
        self._key_store.delete_plain_key()
        self._set_flag(True)

    def disable_pin(self, pin: str) -> None:
        if not self.is_pin_enabled():
            raise ValueError("PIN nie jest włączony.")
        key = self.unlock(pin)
        self._key_store.store_key(key)
        self._key_store.clear_envelope()
        self._set_flag(False)

    def unlock(self, pin: str) -> bytes:
        """Odzyskuje klucz bazy z koperty; błędny PIN → WrongPinError."""
        koperta = self._key_store.load_envelope()
        if koperta is None:
            raise KeyRecoveryNeeded("Brak koperty klucza - wymagane recovery.")
        salt, wrapped = koperta
        return unwrap_db_key(pin, Envelope(salt=salt, wrapped=wrapped))

    def _set_flag(self, enabled: bool) -> None:
        self._conn.execute("BEGIN")
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO app_meta(key, value) VALUES(?, ?)",
                (KLUCZ_PIN_ENABLED, "1" if enabled else "0"),
            )
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise
