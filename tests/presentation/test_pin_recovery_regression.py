"""Regresja #3: _wylacz obsługuje KeyRecoveryNeeded (nie wybija obsługi zdarzenia)."""

from __future__ import annotations

import presentation.views.pin as pinmod
from infrastructure.crypto import KeyRecoveryNeeded


def test_wylacz_lapie_key_recovery_needed(app, monkeypatch) -> None:  # noqa: ANN001
    monkeypatch.setattr(pinmod.messagebox, "showinfo", lambda *a, **k: None)

    view = app._views["pin"]
    view.on_show()

    def boom(pin):  # noqa: ANN001
        raise KeyRecoveryNeeded("uszkodzona koperta")

    monkeypatch.setattr(app.facade, "disable_pin", boom)
    view._pin_var.set("1234")

    # Nie powinno rzucić - błąd ma być złapany i pokazany jako komunikat.
    view._wylacz()
