"""Ekran eksportu danych (Prompt 8.2, spec §10.1).

Eksport ostatniej sesji (+ plan) do CSV. PRZED zapisem - wyraźne ostrzeżenie o
niezaszyfrowanym pliku z danymi o zdrowiu, które trzeba potwierdzić. Plik trafia
wyłącznie lokalnie (wybór ścieżki przez użytkownika).
"""

from __future__ import annotations

from tkinter import filedialog, messagebox, ttk

from presentation import palette
from presentation.views.base import BaseView


class ExportView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)

    def on_show(self) -> None:
        for w in self.winfo_children():
            w.destroy()

        ttk.Label(self, text="Eksport danych", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(
            self,
            text="Możesz zapisać ostatnią sesję (i plan) do pliku CSV na swoim dysku.",
            wraplength=720, justify="left",
        ).pack(anchor="w", pady=(6, 8))

        ttk.Label(
            self, text=self.app.facade.get_export_warning(),
            wraplength=720, justify="left", background=palette.NEUTRALNY, padding=8,
        ).pack(anchor="w", pady=(0, 12))

        if not self.app.facade.has_session_to_export():
            ttk.Label(
                self, text="Najpierw wypełnij ankietę - nie ma jeszcze czego eksportować.",
                foreground=palette.TEKST_PRZYGASZONY,
            ).pack(anchor="w")
            return

        ttk.Button(self, text="Eksportuj do CSV", command=self._eksportuj).pack(
            anchor="w"
        )

    def _eksportuj(self) -> None:
        if not messagebox.askyesno(
            "Potwierdź eksport",
            self.app.facade.get_export_warning() + "\n\nKontynuować?",
            parent=self,
        ):
            return
        sciezka = filedialog.asksaveasfilename(
            parent=self, defaultextension=".csv",
            filetypes=[("Plik CSV", "*.csv")],
            title="Zapisz eksport jako",
        )
        if not sciezka:
            return
        self._eksportuj_do(sciezka)
        messagebox.showinfo("Eksport", "Zapisano plik.", parent=self)

    def _eksportuj_do(self, sciezka: str) -> None:
        """Sam zapis (wydzielony, by był testowalny bez okien dialogowych)."""
        self.app.facade.export_last_session(sciezka)
