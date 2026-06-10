"""Bazowy widok - wspólny kontrakt ekranów (Faza 7).

Każdy ekran to ramka `ttk.Frame` z dostępem do aplikacji (nawigacja + fasada).
Metoda `on_show` pozwala odświeżyć dane przy każdym wejściu na ekran.
"""

from __future__ import annotations

import tkinter.ttk as ttk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from presentation.app import BurnoutApp


class BaseView(ttk.Frame):
    def __init__(self, parent: ttk.Widget, app: BurnoutApp) -> None:
        super().__init__(parent, padding=24)
        self.app = app

    def on_show(self) -> None:
        """Wywoływane przy każdym pokazaniu ekranu (domyślnie nic)."""
