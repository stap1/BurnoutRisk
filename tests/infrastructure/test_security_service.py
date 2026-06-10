"""Testy SecurityService - envelope encryption trybu PIN (Prompt 7.7)."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.crypto import KeyringKeyStore, SecurityService, WrongPinError
from infrastructure.persistence.database import init_database


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):  # noqa: ANN001
        return self._store.get((service, username))

    def set_password(self, service, username, password):  # noqa: ANN001
        self._store[(service, username)] = password

    def delete_password(self, service, username):  # noqa: ANN001
        self._store.pop((service, username), None)


@pytest.fixture
def setup(tmp_path: Path):
    conn = init_database(tmp_path / "b.db")
    ks = KeyringKeyStore(backend=FakeKeyring())
    sec = SecurityService(conn, ks)
    yield conn, ks, sec
    conn.close()


def test_domyslnie_pin_wylaczony(setup) -> None:  # noqa: ANN001
    _, _, sec = setup
    assert sec.is_pin_enabled() is False


def test_enable_pin_chowa_jawny_klucz_zostawia_koperte(setup) -> None:  # noqa: ANN001
    _, ks, sec = setup
    klucz = ks.get_or_create_key()
    sec.enable_pin("1234")
    assert sec.is_pin_enabled() is True
    assert ks.has_plain_key() is False  # jawny klucz zniknął
    # Poprawny PIN odzyskuje DOKŁADNIE ten sam klucz (dane pozostają odczytywalne).
    assert sec.unlock("1234") == klucz


def test_zly_pin_to_wrong_pin_error(setup) -> None:  # noqa: ANN001
    _, _, sec = setup
    sec.enable_pin("1234")
    with pytest.raises(WrongPinError):
        sec.unlock("0000")


def test_disable_pin_przywraca_jawny_klucz(setup) -> None:  # noqa: ANN001
    _, ks, sec = setup
    klucz = ks.get_or_create_key()
    sec.enable_pin("1234")
    sec.disable_pin("1234")
    assert sec.is_pin_enabled() is False
    assert ks.has_plain_key() is True
    assert ks.get_or_create_key() == klucz


def test_enable_gdy_juz_wlaczony_to_blad(setup) -> None:  # noqa: ANN001
    _, _, sec = setup
    sec.enable_pin("1234")
    with pytest.raises(ValueError):
        sec.enable_pin("5678")
