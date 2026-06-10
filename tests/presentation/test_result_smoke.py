"""Smoke testy profilowego ekranu wyniku (Prompt 7.4)."""

from __future__ import annotations

from application.dto import AnswerDTO, SurveyAnswersDTO


def _wykonaj_ankiete(app, raw_per_question) -> None:  # noqa: ANN001
    form = app.facade.get_survey_form()
    answers = [
        AnswerDTO(question_id=q.id, raw_answer=raw_per_question(q))
        for q in form.questions
    ]
    app.last_result = app.facade.submit_survey(SurveyAnswersDTO(answers=answers))


def _is_reversed(q) -> bool:  # noqa: ANN001
    return q.id in {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}


def test_wynik_renderuje_profil(app) -> None:  # noqa: ANN001
    _wykonaj_ankiete(app, lambda q: 2)
    app.show_view("wynik")
    app.update_idletasks()
    # Brak wyjatku = profil sie wyrenderowal; wynik ma 6 obszarow.
    assert len(app.last_result.area_scores) == 6


def test_obszar_a_wysoki_pokazuje_eskalacje(app) -> None:  # noqa: ANN001
    # Wysokie A (nekanie/agresja), reszta niska -> sciezka specjalna.
    def raw(q):
        if q.category == "A":
            return 0 if _is_reversed(q) else 4
        return 4 if _is_reversed(q) else 0

    _wykonaj_ankiete(app, raw)
    view = app._views["wynik"]
    app.show_view("wynik")
    app.update_idletasks()
    # Obszar A powinien byc w pasmie uwagi.
    a = next(x for x in app.last_result.area_scores if x.category_id == "A")
    assert a.band is not None
    # Render nie rzuca; eskalacja obecna gdy A w pasmie HIGH/VERY_HIGH.
    from domain.common import RiskBand
    assert a.band in {RiskBand.HIGH, RiskBand.VERY_HIGH}


def test_wynik_bez_danych_nie_rzuca(app) -> None:  # noqa: ANN001
    app.last_result = None
    app.show_view("wynik")
    app.update_idletasks()  # graceful komunikat, brak wyjatku


def test_band_wyliczany_per_obszar(app) -> None:  # noqa: ANN001
    _wykonaj_ankiete(app, lambda q: 2)  # wszystkie risk=2 -> S=50 -> HIGH
    from domain.common import RiskBand

    for a in app.last_result.area_scores:
        assert a.band == RiskBand.HIGH
