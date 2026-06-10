"""Safety-net jako okno dialogowe - dostępne z KAŻDEGO ekranu (spec §8.1).

Pokazuje komunikat ramowy i zweryfikowane zasoby wsparcia. Ton spokojny, bez
alarmu. Numery i linki pochodzą z `crisis_resources.json` (przez fasadę).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from application.dto import SafetyNetDTO
from presentation import palette


class SafetyNetDialog(tk.Toplevel):
    def __init__(self, parent: tk.Misc, data: SafetyNetDTO) -> None:
        super().__init__(parent)
        self.title("Wsparcie")
        self.configure(padx=20, pady=20)
        self.resizable(False, False)

        ttk.Label(
            self,
            text=data.framing_message,
            wraplength=460,
            justify="left",
        ).pack(anchor="w", pady=(0, 12))

        for r in data.resources:
            ramka = ttk.Frame(self)
            ramka.pack(fill="x", pady=6)
            ttk.Label(
                ramka, text=f"{r.number}  -  {r.name}", font=("", 11, "bold")
            ).pack(anchor="w")
            ttk.Label(ramka, text=r.description, wraplength=460, justify="left").pack(
                anchor="w"
            )
            ttk.Label(
                ramka, text=r.link, foreground=palette.AKCENT
            ).pack(anchor="w")

        ttk.Button(self, text="Zamknij", command=self.destroy).pack(
            anchor="e", pady=(14, 0)
        )

        self.transient(parent)
