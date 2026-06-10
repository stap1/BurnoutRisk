"""Tymczasowy ekran startowy (Prompt 7.1).

Zostanie zastąpiony ekranem powitalnym + zgodą w Prompcie 7.2. Istnieje, by okno
miało co pokazać i by nawigacja oraz safety-net były testowalne od początku.
"""

from __future__ import annotations

from tkinter import ttk

from presentation.views.base import BaseView


class PlaceholderView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)
        ttk.Label(
            self,
            text="Burnout Risk Monitor",
            font=("", 18, "bold"),
        ).pack(anchor="w", pady=(0, 8))
        ttk.Label(
            self,
            text="Lokalne, edukacyjne narzędzie do refleksji nad ryzykiem wypalenia.",
            wraplength=700,
        ).pack(anchor="w")
