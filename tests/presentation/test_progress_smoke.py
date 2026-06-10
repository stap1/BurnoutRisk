"""Smoke testy ProgressPage z wykresami (Prompt 8.1)."""

from __future__ import annotations

from application.dto import AnswerDTO, SurveyAnswersDTO


def test_postep_renderuje_sie_pusty(app) -> None:  # noqa: ANN001
    # Bez danych: wykres pokazuje "za malo danych", brak wyjatku.
    app.show_view("postep")
    app.update_idletasks()
    assert app._views["postep"]._canvas is not None


def test_postep_z_danymi(app) -> None:  # noqa: ANN001
    form = app.facade.get_survey_form()
    app.facade.submit_survey(
        SurveyAnswersDTO(
            answers=[AnswerDTO(question_id=q.id, raw_answer=2) for q in form.questions]
        )
    )
    app.show_view("postep")
    app.update_idletasks()
    report = app.facade.get_progress_report()
    assert len(report.session_trend) == 1
