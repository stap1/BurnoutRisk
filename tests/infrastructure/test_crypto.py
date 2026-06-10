"""Testy AES-GCM CryptoService i KeyStore (Prompt 3.2)."""

from __future__ import annotations

import os

import pytest

from infrastructure.crypto import (
    KEY_BYTES,
    AesGcmCryptoService,
    DecryptionError,
    KeyringKeyStore,
)


# --- AES-GCM CryptoService ---


def _klucz() -> bytes:
    return os.urandom(KEY_BYTES)


def test_round_trip_szyfrowania() -> None:
    svc = AesGcmCryptoService(_klucz())
    tekst = "Notatka z check-inu: dziś lepiej. ąęó"
    blob = svc.encrypt(tekst)
    assert svc.decrypt(blob) == tekst


def test_szyfrogram_jest_nieczytelny() -> None:
    svc = AesGcmCryptoService(_klucz())
    tekst = "tajne dane o zdrowiu"
    blob = svc.encrypt(tekst)
    assert isinstance(blob, bytes)
    assert tekst.encode("utf-8") not in blob


def test_kazde_szyfrowanie_ma_inny_nonce() -> None:
    svc = AesGcmCryptoService(_klucz())
    assert svc.encrypt("to samo") != svc.encrypt("to samo")


def test_zly_klucz_nie_odszyfruje() -> None:
    blob = AesGcmCryptoService(_klucz()).encrypt("x")
    inny = AesGcmCryptoService(_klucz())
    with pytest.raises(DecryptionError):
        inny.decrypt(blob)


def test_naruszony_szyfrogram_to_blad() -> None:
    svc = AesGcmCryptoService(_klucz())
    blob = bytearray(svc.encrypt("dane"))
    blob[-1] ^= 0x01  # zmiana jednego bitu taga
    with pytest.raises(DecryptionError):
        svc.decrypt(bytes(blob))


def test_za_krotki_blob_to_blad() -> None:
    svc = AesGcmCryptoService(_klucz())
    with pytest.raises(DecryptionError):
        svc.decrypt(b"krotkie")


@pytest.mark.parametrize("zly", [b"", b"za krotki", os.urandom(16), os.urandom(64)])
def test_zla_dlugosc_klucza_to_blad(zly: bytes) -> None:
    with pytest.raises(ValueError):
        AesGcmCryptoService(zly)


# --- KeyStore (z atrapą backendu keyring) ---


class FakeKeyring:
    """In-memory backend keyring do testów (duck-typed)."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


class FakeFailKeyring(FakeKeyring):
    """Atrapa udająca niebezpieczny backend (po nazwie klasy)."""


def test_get_or_create_generuje_klucz() -> None:
    ks = KeyringKeyStore(backend=FakeKeyring())
    klucz = ks.get_or_create_key()
    assert isinstance(klucz, bytes)
    assert len(klucz) == KEY_BYTES


def test_get_or_create_jest_stabilny() -> None:
    ks = KeyringKeyStore(backend=FakeKeyring())
    assert ks.get_or_create_key() == ks.get_or_create_key()


def test_jawny_klucz_bazy_nie_jest_zapisany_w_postaci_surowej() -> None:
    backend = FakeKeyring()
    ks = KeyringKeyStore(backend=backend)
    klucz = ks.get_or_create_key()
    zapisane = backend.get_password("BurnoutRiskMonitor", "db_key")
    assert zapisane is not None
    # W keyring jest base64, nie surowe bajty klucza.
    assert zapisane != klucz.decode("latin-1")


def test_delete_key_usuwa() -> None:
    backend = FakeKeyring()
    ks = KeyringKeyStore(backend=backend)
    ks.get_or_create_key()
    ks.delete_key()
    assert backend.get_password("BurnoutRiskMonitor", "db_key") is None
    # Po usunieciu kolejne get_or_create generuje nowy.
    nowy = ks.get_or_create_key()
    assert len(nowy) == KEY_BYTES


def test_delete_key_jest_idempotentny() -> None:
    ks = KeyringKeyStore(backend=FakeKeyring())
    ks.delete_key()  # bez wczesniejszego zapisu - nie rzuca


def test_backend_bezpieczny() -> None:
    assert KeyringKeyStore(backend=FakeKeyring()).is_backend_safe() is True


def test_backend_niebezpieczny_po_nazwie() -> None:
    assert KeyringKeyStore(backend=FakeFailKeyring()).is_backend_safe() is False
