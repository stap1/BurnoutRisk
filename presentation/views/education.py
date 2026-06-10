"""Moduł edukacyjny - kafelki, temat, mini-quiz (Prompt 7.6, spec §9.4).

Home: kafelki tematów. Temat: treść + „ważne w skrócie" + „kiedy warto poszukać
pomocy" + stałe zastrzeżenie „to nie diagnoza". Mini-quiz sprawdza zrozumienie
(nie samoocenę stanu), wynik zapisywany w postępie.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from presentation import palette
from presentation.views.base import BaseView


class EducationView(BaseView):
    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)

    def on_show(self) -> None:
        self._show_home()

    def _wyczysc(self) -> ttk.Frame:
        for w in self.winfo_children():
            w.destroy()
        ramka = ttk.Frame(self)
        ramka.pack(fill="both", expand=True)
        return ramka

    # --- home (kafelki) ---

    def _show_home(self) -> None:
        r = self._wyczysc()
        ttk.Label(r, text="Materiały edukacyjne", font=("", 18, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            r, text=self.app.facade.get_education_disclaimer(),
            wraplength=720, justify="left", foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(4, 14))

        for temat in self.app.facade.get_education_topics():
            ttk.Button(
                r, text=temat.title, width=50,
                command=lambda t=temat.id: self._show_topic(t),
            ).pack(anchor="w", pady=3)

    # --- temat ---

    def _show_topic(self, topic_id: str) -> None:
        self.app.facade.record_topic_view(topic_id)
        temat = self.app.facade.get_education_topic(topic_id)
        if temat is None:
            self._show_home()
            return

        r = self._wyczysc()
        ttk.Label(r, text=temat.title, font=("", 18, "bold")).pack(anchor="w")

        for sekcja in temat.sections:
            ttk.Label(r, text=sekcja.heading, font=("", 12, "bold")).pack(
                anchor="w", pady=(10, 2)
            )
            ttk.Label(r, text=sekcja.body, wraplength=720, justify="left").pack(
                anchor="w"
            )

        ttk.Label(r, text="Ważne w skrócie", font=("", 12, "bold")).pack(
            anchor="w", pady=(12, 2)
        )
        for p in temat.key_points:
            ttk.Label(r, text=f"• {p}", wraplength=700, justify="left").pack(anchor="w")

        ttk.Label(r, text="Kiedy warto poszukać pomocy", font=("", 12, "bold")).pack(
            anchor="w", pady=(12, 2)
        )
        ttk.Label(
            r, text=temat.when_to_seek_help, wraplength=720, justify="left"
        ).pack(anchor="w")

        ttk.Label(
            r, text=self.app.facade.get_education_disclaimer(),
            wraplength=720, justify="left", foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(12, 0))

        przyciski = ttk.Frame(r)
        przyciski.pack(anchor="w", pady=(14, 0))
        ttk.Button(
            przyciski, text="Rozwiąż mini-quiz",
            command=lambda: self._show_quiz(topic_id),
        ).pack(side="left", padx=(0, 8))
        ttk.Button(przyciski, text="Wróć", command=self._show_home).pack(side="left")

    # --- quiz ---

    def _show_quiz(self, topic_id: str) -> None:
        temat = self.app.facade.get_education_topic(topic_id)
        r = self._wyczysc()
        ttk.Label(r, text=f"Mini-quiz: {temat.title}", font=("", 16, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            r, text="Sprawdzenie zrozumienia treści (nie ocena Twojego stanu).",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(2, 12))

        self._quiz_vars: list[tk.IntVar] = []
        for i, q in enumerate(temat.quiz):
            blok = ttk.Frame(r)
            blok.pack(fill="x", anchor="w", pady=6)
            ttk.Label(blok, text=f"{i + 1}. {q.question}", wraplength=700,
                      justify="left").pack(anchor="w")
            var = tk.IntVar(value=-1)
            self._quiz_vars.append(var)
            for j, opcja in enumerate(q.options):
                ttk.Radiobutton(
                    blok, text=opcja, value=j, variable=var
                ).pack(anchor="w")

        self._wynik_lbl = ttk.Label(r, text="", font=("", 12, "bold"))
        self._wynik_lbl.pack(anchor="w", pady=(10, 0))

        ttk.Button(
            r, text="Sprawdź", command=lambda: self._sprawdz_quiz(topic_id)
        ).pack(anchor="w", pady=(8, 0))
        ttk.Button(r, text="Wróć", command=lambda: self._show_topic(topic_id)).pack(
            anchor="w", pady=(6, 0)
        )

    def _sprawdz_quiz(self, topic_id: str) -> None:
        odpowiedzi = [v.get() for v in self._quiz_vars]
        progress = self.app.facade.submit_quiz(topic_id, odpowiedzi)
        self._wynik_lbl.config(
            text=f"Twój wynik: {progress.quiz_score}/{len(self._quiz_vars)}"
        )
