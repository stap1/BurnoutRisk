"""Testy rekodowania ScoringEngine (Prompt 1.2, spec §3.2 krok 1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.survey import ScoringEngine, SurveyDefinition, recode_raw_answer

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


# --- recode_raw_answer: pojedyncza odpowiedź ---


@pytest.mark.parametrize(
    ("raw", "oczekiwany"),
    [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)],
)
def test_odwracane_to_4_minus_raw(raw: int, oczekiwany: int) -> None:
    assert recode_raw_answer(raw, is_reversed=True) == oczekiwany


@pytest.mark.parametrize("raw", [0, 1, 2, 3, 4])
def test_nieodwracane_to_raw_bez_zmian(raw: int) -> None:
    assert recode_raw_answer(raw, is_reversed=False) == raw


def test_pominiete_daje_none_a_nie_zero() -> None:
    assert recode_raw_answer(None, is_reversed=False) is None
    assert recode_raw_answer(None, is_reversed=True) is None


@pytest.mark.parametrize("zly", [-1, 5, 100])
def test_raw_poza_zakresem_to_blad(zly: int) -> None:
    with pytest.raises(ValueError):
        recode_raw_answer(zly, is_reversed=False)


def test_bool_nie_jest_poprawnym_raw() -> None:
    # True == 1, ale to prawie zawsze pomyłka - odrzucamy jawnie.
    with pytest.raises(ValueError):
        recode_raw_answer(True, is_reversed=False)


# --- ScoringEngine.recode: komplet odpowiedzi ---


def test_recode_calej_ankiety(definicja: SurveyDefinition) -> None:
    engine = ScoringEngine(definicja)
    raw = {
        "A1": 0,  # nieodwracane -> 0
        "A4": 1,  # odwracane    -> 3
        "B3": 4,  # odwracane    -> 0
        "C2": 3,  # nieodwracane -> 3
        "F1": 0,  # odwracane    -> 4
    }
    wynik = engine.recode(raw)
    assert wynik["A1"] == 0
    assert wynik["A4"] == 3
    assert wynik["B3"] == 0
    assert wynik["C2"] == 3
    assert wynik["F1"] == 4


def test_recode_obejmuje_wszystkie_pytania_brakujace_jako_none(
    definicja: SurveyDefinition,
) -> None:
    engine = ScoringEngine(definicja)
    wynik = engine.recode({"A1": 2})
    # Wpis dla każdego pytania definicji; niepodane -> None (pominięte).
    assert set(wynik) == {q.id for q in definicja.questions}
    assert wynik["A1"] == 2
    assert wynik["A3"] is None


def test_recode_skipped_jako_none(definicja: SurveyDefinition) -> None:
    engine = ScoringEngine(definicja)
    # A1 jest pomijalne; "wolę nie odpowiadać" = None (nie zero).
    wynik = engine.recode({"A1": None})
    assert wynik["A1"] is None


def test_recode_jest_deterministyczne(definicja: SurveyDefinition) -> None:
    engine = ScoringEngine(definicja)
    raw = {"A1": 1, "A4": 2, "C1": 4, "F3": 0}
    assert engine.recode(raw) == engine.recode(raw)


def test_recode_odrzuca_nieznane_id(definicja: SurveyDefinition) -> None:
    engine = ScoringEngine(definicja)
    with pytest.raises(ValueError):
        engine.recode({"X9": 1})
