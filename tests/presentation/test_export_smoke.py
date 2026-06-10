"""Smoke testy ekranu eksportu + ostrzeżenia (Prompt 8.2)."""

from __future__ import annotations

from pathlib import Path

from application.dto import AnswerDTO, SurveyAnswersDTO


def test_ostrzezenie_o_niezaszyfrowanym_pliku(app) -> None:  # noqa: ANN001
    ostrz = app.facade.get_export_warning()
    assert "niezaszyfrowany" in ostrz.lower()


def test_export_view_renderuje(app) -> None:  # noqa: ANN001
    app.show_view("eksport")
    app.update_idletasks()
    assert "eksport" in app._views


def test_eksport_zapisuje_plik(app, tmp_path: Path) -> None:  # noqa: ANN001
    form = app.facade.get_survey_form()
    app.facade.submit_survey(
        SurveyAnswersDTO(
            answers=[AnswerDTO(question_id=q.id, raw_answer=2) for q in form.questions]
        )
    )
    view = app._views["eksport"]
    plik = tmp_path / "out.csv"
    view._eksportuj_do(str(plik))
    assert plik.exists()
    assert "Wynik (0-100)" in plik.read_text(encoding="utf-8-sig")


def test_brak_sesji_brak_eksportu(app) -> None:  # noqa: ANN001
    assert app.facade.has_session_to_export() is False
