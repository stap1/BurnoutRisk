"""Ekran ankiety z miękkim lądowaniem (Prompt 7.3, spec §4.2-4.3).

Miękkie wprowadzenie, paginacja wg display_order, pasek postępu, walidacja
(nie można dalej bez odpowiedzi; „wolę nie odpowiadać" jest poprawnym wyborem na
pytaniach pomijalnych). Po zakończeniu woła submit_survey i przechodzi do wyniku.
"""

from __future__ import annotations

from tkinter import messagebox, ttk

from application.dto import AnswerDTO, SurveyAnswersDTO
from presentation import palette
from presentation.views.base import BaseView

NIEUDZIELONA = -1
POMINIETA = 99  # wartość wewnętrzna „wolę nie odpowiadać"

WPROWADZENIE = (
    "Część pytań dotyczy trudnych sytuacji w pracy. Odpowiadaj tak, jak czujesz - "
    "nie ma złych odpowiedzi. Jeśli któreś pytanie jest zbyt trudne, możesz je pominąć."
)


class SurveyView(BaseView):
    PYTANIA_NA_STRONE = 3

    def __init__(self, parent: ttk.Widget, app) -> None:  # noqa: ANN001
        super().__init__(parent, app)
        import tkinter as tk

        self._tk = tk

        ttk.Label(self, text="Krótka ankieta", font=("", 18, "bold")).pack(
            anchor="w"
        )
        ttk.Label(
            self, text=WPROWADZENIE, wraplength=720, justify="left",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(anchor="w", pady=(6, 12))

        self._progress = ttk.Progressbar(self, maximum=1, length=720)
        self._progress.pack(fill="x", pady=(0, 12))

        self._body = ttk.Frame(self)
        self._body.pack(fill="both", expand=True)

        nav = ttk.Frame(self)
        nav.pack(fill="x", pady=(12, 0))
        self._wstecz_btn = ttk.Button(nav, text="Wstecz", command=self._wstecz)
        self._wstecz_btn.pack(side="left")
        self._dalej_btn = ttk.Button(nav, text="Dalej", command=self._dalej)
        self._dalej_btn.pack(side="right")

        self._form = None
        self._vars: dict[str, object] = {}
        self._strony: list[list] = []
        self._strona = 0

    def on_show(self) -> None:
        self._form = self.app.facade.get_survey_form()
        self._skala = list(self._form.answer_scale)
        self._vars = {q.id: self._tk.IntVar(value=NIEUDZIELONA) for q in self._form.questions}
        pyt = self._form.questions
        self._strony = [
            pyt[i : i + self.PYTANIA_NA_STRONE]
            for i in range(0, len(pyt), self.PYTANIA_NA_STRONE)
        ]
        self._progress.config(maximum=len(self._strony))
        self._strona = 0
        self._render()

    # --- render strony ---

    def _render(self) -> None:
        for w in self._body.winfo_children():
            w.destroy()

        for q in self._strony[self._strona]:
            blok = ttk.Frame(self._body)
            blok.pack(fill="x", pady=10, anchor="w")
            ttk.Label(blok, text=q.text, wraplength=700, justify="left",
                      font=("", 11)).pack(anchor="w")
            opcje = ttk.Frame(blok)
            opcje.pack(anchor="w", pady=(4, 0))
            for wartosc, etykieta in self._skala:
                ttk.Radiobutton(
                    opcje, text=etykieta, value=wartosc, variable=self._vars[q.id]
                ).pack(side="left", padx=(0, 10))
            if q.is_skippable:
                ttk.Radiobutton(
                    blok, text="Wolę nie odpowiadać", value=POMINIETA,
                    variable=self._vars[q.id],
                ).pack(anchor="w", pady=(4, 0))

        self._progress.config(value=self._strona + 1)
        self._wstecz_btn.config(
            state="normal" if self._strona > 0 else "disabled"
        )
        ostatnia = self._strona == len(self._strony) - 1
        self._dalej_btn.config(text="Zakończ" if ostatnia else "Dalej")

    # --- walidacja i nawigacja ---

    def _waliduj_strone(self) -> bool:
        return all(
            self._vars[q.id].get() != NIEUDZIELONA
            for q in self._strony[self._strona]
        )

    def _wstecz(self) -> None:
        if self._strona > 0:
            self._strona -= 1
            self._render()

    def _dalej(self) -> None:
        if not self._waliduj_strone():
            messagebox.showinfo(
                "Brak odpowiedzi",
                "Zaznacz odpowiedź na każde pytanie na tej stronie "
                "(na trudnych pytaniach możesz wybrać opcję pominięcia).",
                parent=self,
            )
            return
        if self._strona < len(self._strony) - 1:
            self._strona += 1
            self._render()
        else:
            self._submit()

    def _submit(self) -> None:
        answers = []
        for q in self._form.questions:
            wartosc = self._vars[q.id].get()
            if wartosc == POMINIETA:
                answers.append(AnswerDTO(question_id=q.id, raw_answer=None, skipped=True))
            else:
                answers.append(AnswerDTO(question_id=q.id, raw_answer=wartosc))
        wynik = self.app.facade.submit_survey(SurveyAnswersDTO(answers=answers))
        self.app.last_result = wynik
        self.app.show_view("wynik")
