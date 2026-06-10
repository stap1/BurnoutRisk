"""Testy wyniku całkowitego z renormalizacją wag (Prompt 1.4, spec §3.2 krok 4).

To najłatwiejszy do popsucia fragment scoringu - stąd dedykowane, jawne testy
(spec §9). Kluczowa własność: obszar nieoceniony NIE zaniża wyniku.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.survey import ScoringEngine, SurveyDefinition

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


@pytest.fixture(scope="module")
def engine(definicja: SurveyDefinition) -> ScoringEngine:
    return ScoringEngine(definicja)


def test_wszystkie_obszary_maks_daje_100(
    engine: ScoringEngine, definicja: SurveyDefinition
) -> None:
    # Każde nieodwracane = 4, każde odwracane raw=0 -> risk 4. Wszystkie S=100.
    raw = {q.id: (0 if q.is_reversed else 4) for q in definicja.questions}
    assert engine.total_score(raw) == 100.0


def test_wszystkie_obszary_min_daje_0(
    engine: ScoringEngine, definicja: SurveyDefinition
) -> None:
    raw = {q.id: (4 if q.is_reversed else 0) for q in definicja.questions}
    assert engine.total_score(raw) == 0.0


def test_nieoceniony_obszar_nie_zaniza_wyniku(engine: ScoringEngine) -> None:
    # Tylko obszar A oceniony i maksymalny (S=100); reszta = brak danych.
    # Bez renormalizacji wynik bylby zanizony (~26); z renormalizacja = 100.
    raw = {"A1": 4, "A2": 4, "A3": 4, "A4": 0}
    assert engine.total_score(raw) == 100.0


def test_renormalizacja_dwa_obszary(engine: ScoringEngine) -> None:
    # A (waga 26) S=100, C (waga 20) S=0, reszta nieoceniona.
    # total = (26*100 + 20*0) / (26+20) = 2600/46.
    raw = {
        "A1": 4, "A2": 4, "A3": 4, "A4": 0,   # A -> 100
        "C1": 0, "C2": 0, "C3": 0, "C4": 0,   # C -> 0
    }
    assert engine.total_score(raw) == pytest.approx(2600 / 46)


def test_jeden_oceniony_obszar_to_jego_wynik(engine: ScoringEngine) -> None:
    # Tylko D oceniony, S = 50 -> total = 50 (mianownik = sama waga D).
    raw = {"D1": 2, "D2": 2}
    assert engine.total_score(raw) == 50.0


def test_wszystko_pominiete_daje_none(engine: ScoringEngine) -> None:
    assert engine.total_score({}) is None


def test_ponizej_progu_wszedzie_daje_none(engine: ScoringEngine) -> None:
    # Po jednej odpowiedzi w kilku obszarach - zaden nie przekracza progu.
    assert engine.total_score({"A1": 4, "C1": 4, "D1": 4}) is None


def test_total_deterministyczny(engine: ScoringEngine) -> None:
    raw = {"A1": 1, "A2": 3, "B1": 2, "B2": 4, "C1": 0, "C2": 2}
    assert engine.total_score(raw) == engine.total_score(raw)
