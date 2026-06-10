"""Ekran PIN + recovery (Prompt 7.7, spec §2.2.2).

PIN jest opcjonalny (domyślnie wyłączony) i dokłada ochronę zaszyfrowanych pól.
Włączając PIN, użytkownik widzi wyraźne ostrzeżenie: utrata PIN = utrata
zaszyfrowanych pól. Zawsze dostępna jest wyraźna opcja „nie pamiętam PIN-u →
zresetuj" (kontrolowany wipe do czystego, używalnego stanu).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from infrastructure.crypto import WrongPinError
from presentation import palette
from presentation.views.base import BaseView

OSTRZEZENIE = (
    "Uwaga: PIN dokłada ochronę notatek i komentarzy. Jeśli zapomnisz PIN, "
    "nie odzyskasz zaszyfrowanych pól - jedynym wyjściem będzie reset danych."
)


class PinView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)

    def on_show(self) -> None:
        for w in self.winfo_children():
            w.destroy()

        wlaczony = self.app.facade.is_pin_enabled()
        ttk.Label(self, text="PIN i prywatność", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(
            self,
            text=f"Status: PIN {'włączony' if wlaczony else 'wyłączony'}.",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(4, 12))

        self._pin_var = tk.StringVar()
        ttk.Label(self, text="PIN:").pack(anchor="w")
        ttk.Entry(self, textvariable=self._pin_var, show="•", width=20).pack(anchor="w")

        if not wlaczony:
            ttk.Label(
                self, text=OSTRZEZENIE, wraplength=700, justify="left",
                foreground=palette.TEKST_PRZYGASZONY,
            ).pack(anchor="w", pady=(8, 8))
            ttk.Button(self, text="Włącz PIN", command=self._wlacz).pack(anchor="w")
        else:
            ttk.Button(self, text="Wyłącz PIN", command=self._wylacz).pack(
                anchor="w", pady=(8, 0)
            )

        ttk.Separator(self).pack(fill="x", pady=16)
        ttk.Label(
            self, text="Nie pamiętasz PIN-u?", font=("", 12, "bold")
        ).pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Możesz zresetować aplikację do czystego stanu. To nieodwracalnie "
                "usunie dotychczasowe dane, ale przywróci pełną używalność."
            ),
            wraplength=700, justify="left",
        ).pack(anchor="w", pady=(2, 6))
        ttk.Button(
            self, text="Nie pamiętam PIN-u → zresetuj", command=self._reset
        ).pack(anchor="w")

    def _wlacz(self) -> None:
        pin = self._pin_var.get().strip()
        if not pin:
            messagebox.showinfo("PIN", "Podaj PIN.", parent=self)
            return
        self.app.facade.enable_pin(pin)
        messagebox.showinfo("PIN", "PIN włączony.", parent=self)
        self.on_show()

    def _wylacz(self) -> None:
        try:
            self.app.facade.disable_pin(self._pin_var.get().strip())
        except WrongPinError:
            messagebox.showinfo("PIN", "Nieprawidłowy PIN.", parent=self)
            return
        messagebox.showinfo("PIN", "PIN wyłączony.", parent=self)
        self.on_show()

    def _reset(self) -> None:
        if messagebox.askyesno(
            "Reset",
            "Na pewno zresetować? To nieodwracalnie usunie wszystkie dane.",
            parent=self,
        ):
            self.app.facade.wipe_all_data()
            messagebox.showinfo("Reset", "Dane wyczyszczone.", parent=self)
            self.on_show()
