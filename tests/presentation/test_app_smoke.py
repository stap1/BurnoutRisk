"""Smoke testy szkieletu UI (Prompt 7.1)."""

from __future__ import annotations


def test_okno_startuje(app) -> None:  # noqa: ANN001
    assert app.title().startswith("Burnout Risk Monitor")


def test_ekran_startowy_widoczny(app) -> None:  # noqa: ANN001
    # Po starcie pokazany jest ekran powitalny.
    assert "start" in app._views


def test_safety_net_osiagalny(app) -> None:  # noqa: ANN001
    # Safety-net musi dać się otworzyć (z każdego ekranu).
    dialog = app.open_safety_net()
    app.update_idletasks()
    assert dialog.winfo_exists()
    dialog.destroy()


def test_motyw_nie_blokuje_startu(app) -> None:  # noqa: ANN001
    # theme_applied to bool (True = sv_ttk, False = fallback) - oba dozwolone.
    assert isinstance(app.theme_applied, bool)
