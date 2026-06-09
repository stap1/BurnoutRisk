"""Trywialny smoke test Fazy 0 - potwierdza, że pytest działa i szkielet się importuje."""

from __future__ import annotations


def test_smoke_import_szkielet() -> None:
    """Composition root buduje fasadę bez wyjątku."""
    from composition_root import build_app_facade
    from app_facade import AppFacade

    facade = build_app_facade()
    assert isinstance(facade, AppFacade)
