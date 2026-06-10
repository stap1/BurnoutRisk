"""Profilowy ekran wyniku (Prompt 7.4, spec §5).

Bohaterem jest profil obszarów A-F (nie liczba). Liczba 0-100 dyskretna, z
kontekstem normalizującym. Obszary „za mało danych" neutralnie (wyszarzone).
Paleta stonowana; etykiety informujące, nie alarmujące. Połączenie z następnymi
krokami (edukacja/coaching); obszar A wysoki → ścieżka specjalna (eskalacja +
safety-net), bez mikro-coachingu.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from domain.common import RiskBand
from presentation import palette
from presentation.views.base import BaseView

KONTEKST = (
    "To migawka z dziś - nie diagnoza i nie stała cecha. Wynik może się zmieniać."
)
OBSZAR_ESKALACJI = "A"
PASMA_UWAGI = {RiskBand.HIGH, RiskBand.VERY_HIGH}


class ResultView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)
        self._body = ttk.Frame(self)
        self._body.pack(fill="both", expand=True)

    def on_show(self) -> None:
        for w in self._body.winfo_children():
            w.destroy()

        wynik = getattr(self.app, "last_result", None)
        if wynik is None:
            ttk.Label(self._body, text="Brak wyniku do pokazania.").pack(anchor="w")
            return

        ttk.Label(self._body, text="Twój profil obszarów", font=("", 18, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            self._body, text=KONTEKST, wraplength=720, justify="left",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(4, 16))

        # Profil obszarów - BOHATER ekranu.
        for area in wynik.area_scores:
            self._wiersz_obszaru(area)

        # Liczba ogólna - dyskretnie, mniejsza, z kontekstem.
        ogolny = (
            f"Wynik ogólny: {round(wynik.total_score)}/100"
            if wynik.total_score is not None
            else "Za mało danych, by przedstawić ogólny obraz."
        )
        ttk.Label(
            self._body, text=ogolny, foreground=palette.TEKST_PRZYGASZONY
        ).pack(anchor="w", pady=(16, 0))

        self._nastepne_kroki(wynik)

    def _wiersz_obszaru(self, area) -> None:  # noqa: ANN001
        wiersz = ttk.Frame(self._body)
        wiersz.pack(fill="x", pady=4, anchor="w")

        ttk.Label(wiersz, text=area.name, width=34, anchor="w").pack(side="left")

        # Pasek koloru pasma (tk.Frame, bo potrzebny background).
        szerokosc = int((area.score or 0) / 100 * 220)
        pasek = tk.Frame(wiersz, height=16, width=max(szerokosc, 2),
                         background=palette.kolor_pasma(area.band))
        pasek.pack(side="left", padx=(0, 10))
        pasek.pack_propagate(False)

        ttk.Label(
            wiersz, text=palette.etykieta_pasma(area.band),
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(side="left")

    def _nastepne_kroki(self, wynik) -> None:  # noqa: ANN001
        ttk.Separator(self._body).pack(fill="x", pady=14)
        ttk.Label(self._body, text="Następne kroki", font=("", 13, "bold")).pack(
            anchor="w"
        )

        # Ścieżka specjalna obszaru A (spec §7) - poważnie, ale bez alarmu.
        obszar_a = next(
            (a for a in wynik.area_scores if a.category_id == OBSZAR_ESKALACJI), None
        )
        if obszar_a is not None and obszar_a.band in PASMA_UWAGI:
            self._blok_eskalacji()
            return

        przyciski = ttk.Frame(self._body)
        przyciski.pack(anchor="w", pady=(8, 0))
        ttk.Button(
            przyciski, text="Materiały edukacyjne",
            command=lambda: self.app.show_view("edukacja"),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(
            przyciski, text="Zaplanuj małe kroki (coaching)",
            command=lambda: self.app.show_view("coaching"),
        ).pack(side="left")

    def _blok_eskalacji(self) -> None:
        ttk.Label(
            self._body,
            text=(
                "Część Twoich odpowiedzi dotyczy relacji i bezpieczeństwa w pracy. "
                "To sytuacja, która wykracza poza to, w czym aplikacja może pomóc - i "
                "nie rozwiążą jej krótkie ćwiczenia. Warto poszukać realnego wsparcia: "
                "zaufanej osoby, działu HR lub przełożonego wyższego szczebla, a w "
                "razie potrzeby wsparcia zewnętrznego."
            ),
            wraplength=720, justify="left",
        ).pack(anchor="w", pady=(8, 8))
        ttk.Button(
            self._body, text="Pokaż wsparcie", command=self.app.open_safety_net
        ).pack(anchor="w")
