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
import os
from typing import Protocol

import keyring

from application.ports.security import IKeyStore
from infrastructure.crypto.aes_gcm import KEY_BYTES

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
            return base64.b64decode(zapisany)

        klucz = os.urandom(KEY_BYTES)
        self._backend.set_password(
            self._service, self._username, base64.b64encode(klucz).decode("ascii")
        )
        return klucz

    def delete_key(self) -> None:
        try:
            self._backend.delete_password(self._service, self._username)
        except keyring.errors.PasswordDeleteError:
            # Brak klucza do usunięcia traktujemy jak stan docelowy (idempotencja wipe).
            pass

    def is_backend_safe(self) -> bool:
        cls = type(self._backend)
        nazwa = f"{cls.__module__}.{cls.__name__}".lower()
        return not any(frag in nazwa for frag in NIEBEZPIECZNE_BACKENDY)
