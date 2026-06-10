"""Ekran coachingu: wizard, plan, check-in (Prompt 7.5, spec §6.4).

Wizard (cel + budżet) → plan 14-dniowy (oznaczanie ukończone + rating 0-5) →
dzienny check-in (3 suwaki 0-10 + notatka szyfrowana). Wejście check-inu inicjuje
sprawdzenie trendu; przy utrzymującym się pogorszeniu pokazujemy miękką, NIE-
diagnostyczną sugestię z łagodnym odesłaniem do specjalisty.
"""

from __future__ import annotations

import datetime as _dt
import tkinter as tk
from tkinter import messagebox, ttk

from application.dto import CheckInDTO, CoachConfigDTO
from domain.common import Goal
from presentation import palette
from presentation.views.base import BaseView

CELE = [
    (Goal.ENERGIA, "Energia i regeneracja"),
    (Goal.STRES, "Mniej stresu"),
    (Goal.GRANICE, "Granice i czas"),
    (Goal.RELACJE, "Relacje i uznanie"),
]
BUDZETY = [5, 10, 15]


class CoachView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)
        self._plan = None

    def on_show(self) -> None:
        istniejacy = self.app.facade.get_latest_plan()
        if istniejacy is not None:
            self._plan = istniejacy
            self._show_plan()
        else:
            self._show_wizard()

    def _wyczysc(self) -> ttk.Frame:
        for w in self.winfo_children():
            w.destroy()
        ramka = ttk.Frame(self)
        ramka.pack(fill="both", expand=True)
        return ramka

    # --- wizard ---

    def _show_wizard(self) -> None:
        r = self._wyczysc()
        ttk.Label(r, text="Zaplanuj małe kroki", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(
            r, text="Wybierz, na czym chcesz się skupić i ile czasu dziennie możesz dać.",
            foreground=palette.TEKST_PRZYGASZONY, wraplength=700,
        ).pack(anchor="w", pady=(4, 14))

        self._cel_var = tk.StringVar(value=Goal.STRES.value)
        ttk.Label(r, text="Cel:").pack(anchor="w")
        for goal, etykieta in CELE:
            ttk.Radiobutton(
                r, text=etykieta, value=goal.value, variable=self._cel_var
            ).pack(anchor="w")

        self._budzet_var = tk.IntVar(value=10)
        ttk.Label(r, text="Budżet czasu dziennie:").pack(anchor="w", pady=(10, 0))
        wiersz = ttk.Frame(r)
        wiersz.pack(anchor="w")
        for b in BUDZETY:
            ttk.Radiobutton(
                wiersz, text=f"{b} min", value=b, variable=self._budzet_var
            ).pack(side="left", padx=(0, 10))

        ttk.Button(r, text="Utwórz plan", command=self._utworz_plan).pack(
            anchor="w", pady=(16, 0)
        )

    def _utworz_plan(self) -> None:
        wynik = getattr(self.app, "last_result", None)
        if wynik is None or wynik.session_id is None:
            messagebox.showinfo(
                "Najpierw ankieta",
                "Aby ułożyć plan, wypełnij najpierw krótką ankietę.",
                parent=self,
            )
            return
        config = CoachConfigDTO(
            based_on_session_id=wynik.session_id,
            goal=Goal(self._cel_var.get()),
            daily_time_budget=self._budzet_var.get(),
        )
        self._plan = self.app.facade.create_coach_plan(config)
        self._show_plan()

    # --- plan ---

    def _show_plan(self) -> None:
        r = self._wyczysc()
        ttk.Label(r, text="Twój plan na 14 dni", font=("", 18, "bold")).pack(anchor="w")

        if self._plan.escalation_flag:
            ttk.Label(
                r,
                text=(
                    "Część odpowiedzi dotyczy bezpieczeństwa w pracy - obok planu "
                    "warto sięgnąć po realne wsparcie."
                ),
                wraplength=700, foreground=palette.TEKST_PRZYGASZONY,
            ).pack(anchor="w", pady=(4, 8))

        if not self._plan.actions:
            ttk.Label(
                r, text="Na teraz nie ma potrzeby planu - to dobra wiadomość.",
                wraplength=700,
            ).pack(anchor="w", pady=(8, 0))
        else:
            kanwa = ttk.Frame(r)
            kanwa.pack(fill="both", expand=True, pady=(8, 0))
            for akcja in self._plan.actions:
                self._wiersz_akcji(kanwa, akcja)

        ttk.Button(
            r, text="Dzienny check-in", command=self._show_checkin
        ).pack(anchor="w", pady=(14, 0))

    def _wiersz_akcji(self, parent: ttk.Widget, akcja) -> None:  # noqa: ANN001
        wiersz = ttk.Frame(parent)
        wiersz.pack(fill="x", pady=2, anchor="w")

        done_var = tk.BooleanVar(value=akcja.completed_date is not None)
        # Combobox tworzymy najpierw, by checkbox mógł czytać jego BIEŻĄCĄ wartość
        # (inaczej oznaczenie ukończenia nadpisywałoby ocenę nieaktualnym DTO).
        ocena = ttk.Combobox(
            wiersz, width=4, state="readonly",
            values=["", "0", "1", "2", "3", "4", "5"],
        )
        ocena.set("" if akcja.rating is None else str(akcja.rating))

        ttk.Checkbutton(
            wiersz, variable=done_var,
            command=lambda a=akcja, c=ocena, v=done_var: self._zapisz_akcje(a, c, v),
        ).pack(side="left")
        ttk.Label(
            wiersz, text=f"Dz. {akcja.scheduled_day}: {akcja.description}",
            wraplength=560, justify="left",
        ).pack(side="left", padx=(4, 8))

        ocena.pack(side="right")
        ocena.bind(
            "<<ComboboxSelected>>",
            lambda e, a=akcja, c=ocena, v=done_var: self._zapisz_akcje(a, c, v),
        )

    def _zapisz_akcje(self, akcja, combo, done_var) -> None:  # noqa: ANN001
        """Zapisuje stan działania: ukończenie + ocena ZAWSZE z bieżącego combobox."""
        wartosc = combo.get()
        rating = int(wartosc) if wartosc else None
        self.app.facade.update_coach_action(
            akcja.id, completed=done_var.get(), rating=rating
        )

    # --- check-in ---

    def _show_checkin(self) -> None:
        r = self._wyczysc()
        ttk.Label(r, text="Dzienny check-in", font=("", 18, "bold")).pack(anchor="w")
        ttk.Label(
            r, text="Jak dziś jest? Przesuń suwaki (0-10).",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(4, 12))

        self._suwaki: dict[str, tk.IntVar] = {}
        for klucz, etykieta in [
            ("stress", "Stres"), ("sleep", "Sen"), ("energy", "Energia")
        ]:
            var = tk.IntVar(value=5)
            self._suwaki[klucz] = var
            blok = ttk.Frame(r)
            blok.pack(fill="x", pady=4, anchor="w")
            ttk.Label(blok, text=etykieta, width=10).pack(side="left")
            ttk.Scale(blok, from_=0, to=10, variable=var, length=300).pack(side="left")

        ttk.Label(r, text="Notatka (opcjonalna, szyfrowana):").pack(
            anchor="w", pady=(10, 2)
        )
        self._notatka = tk.Text(r, height=3, width=60)
        self._notatka.pack(anchor="w")

        self._sugestia_lbl = ttk.Label(r, text="", wraplength=700, justify="left")
        self._sugestia_lbl.pack(anchor="w", pady=(10, 0))

        ttk.Button(r, text="Zapisz check-in", command=self._zapisz_checkin).pack(
            anchor="w", pady=(12, 0)
        )
        ttk.Button(r, text="Wróć do planu", command=self._show_plan).pack(
            anchor="w", pady=(6, 0)
        )

    def _zapisz_checkin(self) -> None:
        notatka = self._notatka.get("1.0", "end").strip() or None
        checkin = CheckInDTO(
            plan_id=self._plan.id if self._plan else None,
            date=_dt.date.today().isoformat(),
            stress=int(self._suwaki["stress"].get()),
            sleep=int(self._suwaki["sleep"].get()),
            energy=int(self._suwaki["energy"].get()),
            note=notatka,
        )
        wynik = self.app.facade.submit_checkin(checkin)
        if wynik.trend_worsening and wynik.trend_suggestion:
            self._sugestia_lbl.config(text=wynik.trend_suggestion)
        else:
            self._sugestia_lbl.config(text="Zapisano. Dzięki, że dbasz o siebie.")
