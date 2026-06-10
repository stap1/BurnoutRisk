"""Magazyn klucza szyfrującego oparty o systemowy keyring (Prompt 3.2).

Implementuje port `IKeyStore`. Przy 1. uruchomieniu generuje losowy klucz bazy
(AES-256) i zapisuje w keyring; kolejne uruchomienia go odczytują. Klucz trzymany
jest w postaci base64 (keyring przechowuje napisy).

Fail-fast (spec §12.6): `is_backend_safe()` wykrywa niebezpieczny backend
(null/fail/plaintext), by aplikacja mogła uczciwie ostrzec, że szyfrowanie może
nie być skuteczne - bez udawania ochrony, której nie ma.

Backend keyring jest wstrzykiwany (domyślnie aktywny systemowy), co pozwala
testować logikę bez dotykania prawdziwego magazynu poświadczeń.
"""

from __future__ import annotations

import base64
import binascii
import os
from typing import Protocol

import keyring

from application.ports.security import IKeyStore
from infrastructure.crypto.aes_gcm import KEY_BYTES
from infrastructure.crypto.pin import KeyRecoveryNeeded

SERVICE_NAME = "BurnoutRiskMonitor"
DEFAULT_USERNAME = "db_key"

# Fragmenty nazw modułu/klasy backendu uznawane za niebezpieczne.
NIEBEZPIECZNE_BACKENDY = ("fail", "null", "plaintext")


class _KeyringBackend(Protocol):
    def get_password(self, service: str, username: str) -> str | None: ...
    def set_password(self, service: str, username: str, password: str) -> None: ...
    def delete_password(self, service: str, username: str) -> None: ...


class KeyringKeyStore(IKeyStore):
    def __init__(
        self,
        *,
        backend: _KeyringBackend | None = None,
        service_name: str = SERVICE_NAME,
        username: str = DEFAULT_USERNAME,
    ) -> None:
        self._backend: _KeyringBackend = backend or keyring.get_keyring()
        self._service = service_name
        self._username = username

    def get_or_create_key(self) -> bytes:
        zapisany = self._backend.get_password(self._service, self._username)
        if zapisany:
            try:
                klucz = base64.b64decode(zapisany, validate=True)
            except (binascii.Error, ValueError) as exc:
                # Uszkodzony wpis (np. zmiana hasła OS, przeniesienie maszyny) -
                # nie crashujemy, sygnalizujemy potrzebę recovery (spec §2.2.2).
                raise KeyRecoveryNeeded("Klucz w keyring jest uszkodzony.") from exc
            if len(klucz) != KEY_BYTES:
                raise KeyRecoveryNeeded("Klucz w keyring ma nieprawidłową długość.")
            return klucz

        klucz = os.urandom(KEY_BYTES)
        self._backend.set_password(
            self._service, self._username, base64.b64encode(klucz).decode("ascii")
        )
        return klucz

    def store_key(self, key: bytes) -> None:
        """Zapisuje jawny klucz bazy (używane przy wyłączaniu PIN)."""
        self._backend.set_password(
            self._service, self._username, base64.b64encode(key).decode("ascii")
        )

    def has_plain_key(self) -> bool:
        return bool(self._backend.get_password(self._service, self._username))

    def delete_plain_key(self) -> None:
        """Usuwa tylko jawny klucz (przy włączaniu PIN koperta zostaje)."""
        try:
            self._backend.delete_password(self._service, self._username)
        except keyring.errors.PasswordDeleteError:
            pass

    def delete_key(self) -> None:
        try:
            self._backend.delete_password(self._service, self._username)
            self._backend.delete_password(self._service, self._envelope_user())
        except keyring.errors.PasswordDeleteError:
            # Brak wpisu do usunięcia traktujemy jak stan docelowy (idempotencja wipe).
            pass

    # --- koperta (tryb PIN) ---

    def _envelope_user(self) -> str:
        return f"{self._username}_envelope"

    def store_envelope(self, salt: bytes, wrapped: bytes) -> None:
        wartosc = (
            base64.b64encode(salt).decode("ascii")
            + ":"
            + base64.b64encode(wrapped).decode("ascii")
        )
        self._backend.set_password(self._service, self._envelope_user(), wartosc)

    def load_envelope(self) -> tuple[bytes, bytes] | None:
        wartosc = self._backend.get_password(self._service, self._envelope_user())
        if not wartosc or ":" not in wartosc:
            return None
        s, w = wartosc.split(":", 1)
        try:
            return base64.b64decode(s, validate=True), base64.b64decode(w, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise KeyRecoveryNeeded("Koperta klucza w keyring jest uszkodzona.") from exc

    def clear_envelope(self) -> None:
        try:
            self._backend.delete_password(self._service, self._envelope_user())
        except keyring.errors.PasswordDeleteError:
            pass

    def is_backend_safe(self) -> bool:
        cls = type(self._backend)
        nazwa = f"{cls.__module__}.{cls.__name__}".lower()
        return not any(frag in nazwa for frag in NIEBEZPIECZNE_BACKENDY)
