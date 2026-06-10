"""Testy envelope encryption (tryb PIN) i recovery (Prompt 3.4)."""

from __future__ import annotations

import os

import pytest

from infrastructure.crypto import (
    KEY_BYTES,
    Envelope,
    KeyRecoveryNeeded,
    KeyringKeyStore,
    WrongPinError,
    unwrap_db_key,
    wrap_db_key,
)
from infrastructure.crypto.pin import SALT_BYTES


def _db_key() -> bytes:
    return os.urandom(KEY_BYTES)


# --- envelope encryption ---


def test_wrap_unwrap_round_trip() -> None:
    db_key = _db_key()
    env = wrap_db_key("moj-pin-1234", db_key)
    assert unwrap_db_key("moj-pin-1234", env) == db_key


def test_zly_pin_to_wrong_pin_error() -> None:
    env = wrap_db_key("poprawny", _db_key())
    with pytest.raises(WrongPinError):
        unwrap_db_key("bledny", env)


def test_koperta_nie_zawiera_jawnego_klucza() -> None:
    db_key = _db_key()
    env = wrap_db_key("pin", db_key)
    # Klucz bazy NIGDY nie leży jawnie w kopercie.
    assert db_key not in env.wrapped
    assert len(env.salt) == SALT_BYTES


def test_kazda_koperta_ma_inna_sol() -> None:
    db_key = _db_key()
    e1 = wrap_db_key("pin", db_key)
    e2 = wrap_db_key("pin", db_key)
    assert e1.salt != e2.salt
    assert e1.wrapped != e2.wrapped


def test_uszkodzona_koperta_to_recovery() -> None:
    env = Envelope(salt=b"za-krotka", wrapped=b"x")
    with pytest.raises(KeyRecoveryNeeded):
        unwrap_db_key("pin", env)


def test_pusty_pin_odrzucony() -> None:
    with pytest.raises(ValueError):
        wrap_db_key("", _db_key())


# --- recovery: uszkodzony klucz w keyring -> propozycja recovery, nie crash ---


class FakeKeyring:
    def __init__(self, initial: dict | None = None) -> None:
        self._store = dict(initial or {})

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


def test_uszkodzony_klucz_w_keyring_to_recovery() -> None:
    backend = FakeKeyring(
        {("BurnoutRiskMonitor", "db_key"): "!!! to nie jest base64 !!!"}
    )
    ks = KeyringKeyStore(backend=backend)
    with pytest.raises(KeyRecoveryNeeded):
        ks.get_or_create_key()


def test_klucz_zlej_dlugosci_to_recovery() -> None:
    import base64

    backend = FakeKeyring(
        {("BurnoutRiskMonitor", "db_key"): base64.b64encode(b"za krotki").decode()}
    )
    ks = KeyringKeyStore(backend=backend)
    with pytest.raises(KeyRecoveryNeeded):
        ks.get_or_create_key()
