"""ProgressPage - trendy + warstwa sprawczości (Prompt 8.1, spec §6.3.1, §10).

Wykres trendu NIGDY nie jest pokazywany „nago": zawsze towarzyszy mu konstruktywny
kontekst, warstwa sprawczości (co się udało) i konkretny następny krok. Paleta
stonowana; domyślnie patrzymy na dłuższy obraz, nie dzień-do-dnia.
"""

from __future__ import annotations

from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from presentation import palette
from presentation.charts.trend_chart import build_progress_figure
from presentation.views.base import BaseView

KONTEKST = (
    "Spadki bywają naturalną częścią procesu - to nie wyrok. Obok wykresu masz to, "
    "co już udało Ci się zrobić, oraz konkretny następny krok."
)


class ProgressView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)
        self._canvas = None

    def on_show(self) -> None:
        for w in self.winfo_children():
            w.destroy()
        self._canvas = None

        report = self.app.facade.get_progress_report()

        ttk.Label(self, text="Twój postęp", font=("", 18, "bold")).pack(anchor="w")

        # Warstwa sprawczości - spokojny, prawdziwy ton.
        ag = report.agency
        sprawczosc = (
            f"Ukończone działania: {ag.completed_actions}/{ag.total_actions}   •   "
            f"Check-iny: {ag.checkin_count}"
        )
        ttk.Label(self, text=sprawczosc).pack(anchor="w", pady=(6, 2))
        if ag.improved_areas:
            ttk.Label(
                self, text="Poprawiło się: " + ", ".join(ag.improved_areas),
                foreground=palette.TEKST_PRZYGASZONY, wraplength=720, justify="left",
            ).pack(anchor="w")

        # Konstruktywne obramowanie - krzywa nigdy „nago".
        ttk.Label(
            self, text=KONTEKST, wraplength=720, justify="left",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(6, 8))

        figura = build_progress_figure(report)
        self._canvas = FigureCanvasTkAgg(figura, master=self)
        self._canvas.draw()
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # Następny krok - spadek zawsze prowadzi gdzieś dalej.
        kroki = ttk.Frame(self)
        kroki.pack(anchor="w", pady=(10, 0))
        ttk.Button(
            kroki, text="Materiały edukacyjne",
            command=lambda: self.app.show_view("edukacja"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            kroki, text="Plan i check-in",
            command=lambda: self.app.show_view("coaching"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(kroki, text="Potrzebuję wsparcia", command=self.app.open_safety_net).pack(
            side="left"
        )
