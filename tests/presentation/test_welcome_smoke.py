"""Smoke testy ekranu powitalnego + zgody (Prompt 7.2)."""

from __future__ import annotations


def test_ekran_startowy_to_welcome(app) -> None:  # noqa: ANN001
    from presentation.views.welcome import WelcomeView

    assert isinstance(app._views["start"], WelcomeView)


def test_dalej_zablokowane_bez_zgody(app) -> None:  # noqa: ANN001
    welcome = app._views["start"]
    assert str(welcome.dalej_btn["state"]) == "disabled"


def test_zgoda_odblokowuje_dalej(app) -> None:  # noqa: ANN001
    welcome = app._views["start"]
    welcome.zgoda_var.set(True)
    welcome._aktualizuj_przycisk()
    assert str(welcome.dalej_btn["state"]) == "normal"


def test_dalej_przechodzi_do_ankiety(app) -> None:  # noqa: ANN001
    welcome = app._views["start"]
    welcome.zgoda_var.set(True)
    welcome._dalej()
    app.update_idletasks()
    # Brak wyjątku = nawigacja zadziałała; ekran "ankieta" istnieje.
    assert "ankieta" in app._views
