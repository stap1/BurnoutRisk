"""Smoke testy modułu edukacyjnego (Prompt 7.6)."""

from __future__ import annotations


def test_home_pokazuje_tematy(app) -> None:  # noqa: ANN001
    app.show_view("edukacja")
    app.update_idletasks()
    # Brak wyjatku; sa tematy do pokazania.
    assert len(app.facade.get_education_topics()) >= 5


def test_otwarcie_tematu_zapisuje_view(app) -> None:  # noqa: ANN001
    view = app._views["edukacja"]
    app.show_view("edukacja")
    tid = app.facade.get_education_topics()[0].id
    view._show_topic(tid)
    app.update_idletasks()
    # record_topic_view zapisal postep.
    assert app.facade.get_education_progress(tid) is not None


def test_quiz_poprawny_daje_pelny_wynik(app) -> None:  # noqa: ANN001
    view = app._views["edukacja"]
    app.show_view("edukacja")
    temat = app.facade.get_education_topics()[0]
    view._show_quiz(temat.id)
    for var, q in zip(view._quiz_vars, temat.quiz):
        var.set(q.correct_index)
    view._sprawdz_quiz(temat.id)
    app.update_idletasks()
    assert f"{len(temat.quiz)}/{len(temat.quiz)}" in view._wynik_lbl["text"]
    # Wynik zapisany w postepie.
    assert app.facade.get_education_progress(temat.id).quiz_score == len(temat.quiz)
