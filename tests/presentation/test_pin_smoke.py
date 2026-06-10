"""Smoke testy ekranu PIN + recovery (Prompt 7.7)."""

from __future__ import annotations


def test_pin_view_renderuje_stan_wylaczony(app) -> None:  # noqa: ANN001
    app.show_view("pin")
    app.update_idletasks()
    assert app.facade.is_pin_enabled() is False


def test_pin_view_renderuje_stan_wlaczony(app) -> None:  # noqa: ANN001
    app.facade.enable_pin("1234")
    view = app._views["pin"]
    view.on_show()  # render w stanie włączonym - bez wyjątku
    app.update_idletasks()
    assert app.facade.is_pin_enabled() is True


def test_recovery_reset_czysci_dane(app) -> None:  # noqa: ANN001
    from application.dto import AnswerDTO, SurveyAnswersDTO

    form = app.facade.get_survey_form()
    app.facade.submit_survey(
        SurveyAnswersDTO(
            answers=[AnswerDTO(question_id=q.id, raw_answer=2) for q in form.questions]
        )
    )
    assert app.facade.get_history()
    # Recovery = pełny wipe (czysty, używalny stan).
    app.facade.wipe_all_data()
    assert app.facade.get_history() == []
