"""Wspólne fixture'y dla smoke-testów UI (Faza 7).

Buduje fasadę na bazie tymczasowej i z atrapą keyring, tworzy okno aplikacji w
trybie ukrytym (bez mainloop). Gdy środowisko nie ma displaya - test jest
pomijany (skip), nie failuje.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from pathlib import Path

import pytest

from app_facade import AppFacade
from composition_root import build_app_facade

STALY_CZAS = datetime(2026, 6, 10, 12, 0, 0)


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


@pytest.fixture
def facade(tmp_path: Path) -> AppFacade:
    return build_app_facade(
        db_path=tmp_path / "baza.db",
        keyring_backend=FakeKeyring(),
        clock=lambda: STALY_CZAS,
    )


@pytest.fixture
def app(facade: AppFacade):
    from presentation.app import BurnoutApp

    try:
        instancja = BurnoutApp(facade)
    except tk.TclError:
        pytest.skip("Brak środowiska graficznego dla tkinter")
    instancja.withdraw()
    instancja.update_idletasks()
    yield instancja
    instancja.destroy()
