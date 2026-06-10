"""Ekran powitalny + zgoda + prywatność (Prompt 7.2, spec §4.1, §2.1, §2.4).

Zgoda jest wymagana, by przejść dalej. Komunikat jest uczciwy: narzędzie
edukacyjne (nie diagnoza), wszystko lokalnie (zero sieci/telemetrii), realny
poziom ochrony (szyfrowane tylko notatki/komentarze; PIN opcjonalny) oraz
transparentna retencja (dane zostają, dopóki ich nie usuniesz).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from presentation import palette
from presentation.views.base import BaseView

DISCLAIMER = (
    "To narzędzie edukacyjne, które pomaga zatrzymać się i spojrzeć na swoje "
    "samopoczucie w pracy. Nie stawia diagnozy i nie zastępuje kontaktu ze "
    "specjalistą."
)

PRYWATNOSC = (
    "Twoja prywatność:\n"
    "• Wszystko działa lokalnie na tym komputerze - bez internetu, bez telemetrii.\n"
    "• Tryb anonimowy: nie prosimy o imię ani dane identyfikujące.\n"
    "• Notatki i komentarze są szyfrowane; pozostałe dane przechowywane lokalnie.\n"
    "• PIN jest opcjonalny (domyślnie wyłączony) i dokłada ochronę notatek.\n"
    "• Dane zostają u Ciebie, dopóki sam ich nie usuniesz (możesz wyczyścić wszystko)."
)


class WelcomeView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)

        ttk.Label(self, text="Witaj", font=("", 20, "bold")).pack(
            anchor="w", pady=(0, 10)
        )
        ttk.Label(self, text=DISCLAIMER, wraplength=720, justify="left").pack(
            anchor="w", pady=(0, 16)
        )
        ttk.Label(
            self,
            text=PRYWATNOSC,
            wraplength=720,
            justify="left",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(0, 20))

        self.zgoda_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self,
            text="Rozumiem i chcę kontynuować.",
            variable=self.zgoda_var,
            command=self._aktualizuj_przycisk,
        ).pack(anchor="w", pady=(0, 12))

        self.dalej_btn = ttk.Button(
            self, text="Dalej", command=self._dalej, state="disabled"
        )
        self.dalej_btn.pack(anchor="w")

    def _aktualizuj_przycisk(self) -> None:
        self.dalej_btn.config(state="normal" if self.zgoda_var.get() else "disabled")

    def _dalej(self) -> None:
        if self.zgoda_var.get():
            self.app.show_view("ankieta")
