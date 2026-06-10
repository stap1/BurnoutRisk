"""Testy biblioteki mikro-działań (Prompt 4.1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.coaching import (
    DOZWOLONE_BUDZETY,
    OBSZARY_DZIALAN,
    CoachActionLibrary,
)
from infrastructure.persistence.coach_actions_loader import load_coach_actions

ACTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "coach_actions.json"


@pytest.fixture(scope="module")
def biblioteka() -> CoachActionLibrary:
    return load_coach_actions()


def test_laduje_sie(biblioteka: CoachActionLibrary) -> None:
    assert isinstance(biblioteka, CoachActionLibrary)
    assert len(biblioteka.actions) >= 15


def test_pokrywa_obszary_b_do_f(biblioteka: CoachActionLibrary) -> None:
    obszary = {a.area for a in biblioteka.actions}
    assert obszary == set(OBSZARY_DZIALAN)


def test_brak_obszaru_a(biblioteka: CoachActionLibrary) -> None:
    # Obszar A NIE ma mikro-działań (ścieżka specjalna, §7).
    assert all(a.area != "A" for a in biblioteka.actions)


def test_kazdy_obszar_ma_kazdy_budzet(biblioteka: CoachActionLibrary) -> None:
    for obszar in OBSZARY_DZIALAN:
        czasy = {a.minutes for a in biblioteka.actions if a.area == obszar}
        assert set(DOZWOLONE_BUDZETY) <= czasy


def test_for_area_and_budget_respektuje_budzet(biblioteka: CoachActionLibrary) -> None:
    pasujace = biblioteka.for_area_and_budget("C", 10)
    assert pasujace  # cos jest
    assert all(a.minutes <= 10 for a in pasujace)
    # Posortowane malejaco po czasie.
    assert [a.minutes for a in pasujace] == sorted(
        (a.minutes for a in pasujace), reverse=True
    )


def test_for_area_and_budget_jest_deterministyczne(biblioteka: CoachActionLibrary) -> None:
    assert biblioteka.for_area_and_budget("F", 15) == biblioteka.for_area_and_budget("F", 15)


# --- walidacja błędnych danych ---


def test_odrzuca_obszar_a() -> None:
    raw = {
        "dzialania": [
            {"id": "A5", "obszar": "A", "typ": "x", "czas": 5, "cel": None, "tresc": "t"},
        ]
    }
    with pytest.raises(ValidationError):
        CoachActionLibrary.from_dict(raw)


def test_odrzuca_zly_budzet() -> None:
    raw = {
        "dzialania": [
            {"id": "C7", "obszar": "C", "typ": "x", "czas": 7, "cel": None, "tresc": "t"},
        ]
    }
    with pytest.raises(ValidationError):
        CoachActionLibrary.from_dict(raw)


def test_odrzuca_niepelne_pokrycie_budzetow() -> None:
    # Obszar C tylko z budżetem 5 - brak 10 i 15.
    raw = {
        "dzialania": [
            {"id": "C5", "obszar": "C", "typ": "x", "czas": 5, "cel": None, "tresc": "t"},
        ]
    }
    with pytest.raises(ValidationError):
        CoachActionLibrary.from_dict(raw)
