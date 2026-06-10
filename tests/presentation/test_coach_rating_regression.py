"""Regresja #2: oznaczenie ukończenia NIE kasuje wcześniej ustawionej oceny."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from application.dto import AnswerDTO, SurveyAnswersDTO
from domain.common import Goal


def _is_reversed(q) -> bool:  # noqa: ANN001
    return q.id in {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}


def _utworz_plan(app):  # noqa: ANN001
    form = app.facade.get_survey_form()
    answers = [
        AnswerDTO(question_id=q.id, raw_answer=4 if q.category == "C" else (4 if _is_reversed(q) else 0))
        for q in form.questions
    ]
    app.last_result = app.facade.submit_survey(SurveyAnswersDTO(answers=answers))
    view = app._views["coaching"]
    app.show_view("coaching")
    view._cel_var.set(Goal.STRES.value)
    view._budzet_var.set(10)
    view._utworz_plan()
    return view


def test_ocena_zachowana_po_oznaczeniu_ukonczenia(app) -> None:  # noqa: ANN001
    view = _utworz_plan(app)
    akcja = view._plan.actions[0]

    combo = ttk.Combobox(app, values=["", "0", "1", "2", "3", "4", "5"])
    combo.set("3")
    done = tk.BooleanVar(value=False)

    # 1) Najpierw ocena (combobox), bez ukończenia.
    view._zapisz_akcje(akcja, combo, done)
    plan = app.facade.get_latest_plan()
    a = next(x for x in plan.actions if x.id == akcja.id)
    assert a.rating == 3
    assert a.completed_date is None

    # 2) Potem oznaczenie ukończenia - ocena MUSI zostać zachowana.
    done.set(True)
    view._zapisz_akcje(akcja, combo, done)
    plan = app.facade.get_latest_plan()
    a = next(x for x in plan.actions if x.id == akcja.id)
    assert a.rating == 3            # nie skasowana do None
    assert a.completed_date is not None
