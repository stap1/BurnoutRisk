"""Test gatingu startu przy włączonym PIN (Prompt 7.7)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from composition_root import PinRequiredError, build_app_facade
from infrastructure.crypto import WrongPinError

CZAS = datetime(2026, 6, 10, 12, 0, 0)


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service, username):  # noqa: ANN001
        return self._store.get((service, username))

    def set_password(self, service, username, password):  # noqa: ANN001
        self._store[(service, username)] = password

    def delete_password(self, service, username):  # noqa: ANN001
        self._store.pop((service, username), None)


def test_po_wlaczeniu_pin_start_wymaga_pinu(tmp_path: Path) -> None:
    kr = FakeKeyring()
    db = tmp_path / "b.db"

    facade = build_app_facade(db_path=db, keyring_backend=kr, clock=lambda: CZAS)
    facade.enable_pin("1234")

    # Kolejne uruchomienie bez PIN-u -> PinRequiredError (nie crash).
    with pytest.raises(PinRequiredError):
        build_app_facade(db_path=db, keyring_backend=kr, clock=lambda: CZAS)

    # Zły PIN -> WrongPinError (kontrolowany).
    with pytest.raises(WrongPinError):
        build_app_facade(db_path=db, keyring_backend=kr, clock=lambda: CZAS, pin="0000")

    # Poprawny PIN -> aplikacja startuje.
    odblokowana = build_app_facade(
        db_path=db, keyring_backend=kr, clock=lambda: CZAS, pin="1234"
    )
    assert odblokowana.is_pin_enabled() is True
