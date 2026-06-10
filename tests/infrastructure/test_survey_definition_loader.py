"""Testy loadera definicji ankiety (Prompt 1.1, warstwa infrastruktury)."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.survey import SurveyDefinition
from infrastructure.persistence.survey_definition_loader import (
    load_survey_definition,
)


def test_laduje_domyslny_plik_questions_json() -> None:
    definicja = load_survey_definition()
    assert isinstance(definicja, SurveyDefinition)
    assert len(definicja.questions) == 21


def test_brak_pliku_to_czytelny_blad(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_survey_definition(tmp_path / "nie_istnieje.json")


def test_niepoprawny_json_to_czytelny_blad(tmp_path: Path) -> None:
    zly = tmp_path / "zly.json"
    zly.write_text("{ to nie jest json ", encoding="utf-8")
    with pytest.raises(ValueError):
        load_survey_definition(zly)
