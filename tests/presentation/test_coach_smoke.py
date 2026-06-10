"""Smoke testy ekranu coachingu (Prompt 7.5)."""

from __future__ import annotations

from application.dto import AnswerDTO, SurveyAnswersDTO
from domain.common import Goal


def _is_reversed(q) -> bool:  # noqa: ANN001
    return q.id in {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}


def _ankieta_wysokie_C(app) -> None:  # noqa: ANN001
    form = app.facade.get_survey_form()
    answers = []
    for q in form.questions:
        if q.category == "C":
            answers.append(AnswerDTO(question_id=q.id, raw_answer=4))
        else:
            answers.append(
                AnswerDTO(question_id=q.id, raw_answer=4 if _is_reversed(q) else 0)
            )
    app.last_result = app.facade.submit_survey(SurveyAnswersDTO(answers=answers))


def test_wizard_pokazuje_sie_bez_planu(app) -> None:  # noqa: ANN001
    app.show_view("coaching")
    app.update_idletasks()
    view = app._views["coaching"]
    assert hasattr(view, "_cel_var")  # wizard zbudowany


def test_utworzenie_planu(app) -> None:  # noqa: ANN001
    _ankieta_wysokie_C(app)
    view = app._views["coaching"]
    app.show_view("coaching")
    view._cel_var.set(Goal.STRES.value)
    view._budzet_var.set(10)
    view._utworz_plan()
    app.update_idletasks()
    assert view._plan is not None
    assert len(view._plan.actions) == 14


def test_oznaczenie_dzialania_persystuje(app) -> None:  # noqa: ANN001
    _ankieta_wysokie_C(app)
    view = app._views["coaching"]
    app.show_view("coaching")
    view._cel_var.set(Goal.STRES.value)
    view._budzet_var.set(10)
    view._utworz_plan()
    akcja = view._plan.actions[0]
    app.facade.update_coach_action(akcja.id, completed=True, rating=4)
    # Odczyt potwierdza trwalosc.
    plan = app.facade.get_latest_plan()
    zaktualizowana = next(a for a in plan.actions if a.id == akcja.id)
    assert zaktualizowana.completed_date is not None
    assert zaktualizowana.rating == 4


def test_checkin_zapisuje_i_pokazuje_komunikat(app) -> None:  # noqa: ANN001
    _ankieta_wysokie_C(app)
    view = app._views["coaching"]
    app.show_view("coaching")
    view._cel_var.set(Goal.STRES.value)
    view._budzet_var.set(10)
    view._utworz_plan()
    view._show_checkin()
    view._suwaki["stress"].set(7)
    view._suwaki["sleep"].set(4)
    view._suwaki["energy"].set(4)
    view._notatka.insert("1.0", "trudny dzień")
    view._zapisz_checkin()
    app.update_idletasks()
    # Jeden check-in: za malo danych na trend -> komunikat potwierdzajacy (nie sugestia).
    assert view._sugestia_lbl["text"]
