"""Smoke testy ekranu ankiety (Prompt 7.3)."""

from __future__ import annotations

from presentation.views.survey import POMINIETA, SurveyView


def _ankieta(app) -> SurveyView:  # noqa: ANN001
    app.show_view("ankieta")
    app.update_idletasks()
    return app._views["ankieta"]


def test_ankieta_paginuje(app) -> None:  # noqa: ANN001
    v = _ankieta(app)
    assert len(v._strony) >= 1
    # 21 pytań po 3 na stronę = 7 stron.
    assert sum(len(s) for s in v._strony) == 21


def test_walidacja_blokuje_bez_odpowiedzi(app) -> None:  # noqa: ANN001
    v = _ankieta(app)
    assert v._waliduj_strone() is False


def test_odpowiedz_przechodzi_walidacje(app) -> None:  # noqa: ANN001
    v = _ankieta(app)
    for q in v._strony[0]:
        v._vars[q.id].set(2)
    assert v._waliduj_strone() is True


def test_pelne_wypelnienie_i_submit(app) -> None:  # noqa: ANN001
    v = _ankieta(app)
    for q in v._form.questions:
        v._vars[q.id].set(2)
    v._submit()
    app.update_idletasks()
    assert app.last_result is not None
    assert app.last_result.total_score is not None


def test_pominiecie_pomijalnego_dziala(app) -> None:  # noqa: ANN001
    v = _ankieta(app)
    for q in v._form.questions:
        if q.is_skippable:
            v._vars[q.id].set(POMINIETA)
        else:
            v._vars[q.id].set(2)
    v._submit()
    app.update_idletasks()
    assert app.last_result is not None
