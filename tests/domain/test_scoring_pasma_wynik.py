"""Testy pasm ryzyka, top obszarów i pełnego ScoringResult (Prompt 1.5, §3.2/§5.5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.common import AreaStatus, RiskBand
from domain.survey import (
    ScoringEngine,
    ScoringResult,
    SurveyDefinition,
    risk_band,
)

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


@pytest.fixture(scope="module")
def engine(definicja: SurveyDefinition) -> ScoringEngine:
    return ScoringEngine(definicja)


# --- granice pasm ryzyka (24/25, 49/50, 69/70) ---


@pytest.mark.parametrize(
    ("score", "pasmo"),
    [
        (0, RiskBand.LOW),
        (24, RiskBand.LOW),
        (24.99, RiskBand.LOW),
        (25, RiskBand.MODERATE),
        (49, RiskBand.MODERATE),
        (49.99, RiskBand.MODERATE),
        (50, RiskBand.HIGH),
        (69, RiskBand.HIGH),
        (69.99, RiskBand.HIGH),
        (70, RiskBand.VERY_HIGH),
        (100, RiskBand.VERY_HIGH),
    ],
)
def test_granice_pasm(score: float, pasmo: RiskBand) -> None:
    assert risk_band(score) == pasmo


# --- top obszary (z pominięciem INSUFFICIENT_DATA) ---


def test_top_obszary_sortowane_malejaco(engine: ScoringEngine) -> None:
    # A: S=100, C: S=50, D: S=0. Oczekiwana kolejnosc: A, C, D.
    raw = {
        "A1": 4, "A2": 4, "A3": 4, "A4": 0,   # A -> 100
        "C1": 2, "C2": 2, "C3": 2, "C4": 2,   # C -> 50
        "D1": 0, "D2": 0, "D3": 0,            # D -> 0
    }
    wynik = engine.score(raw)
    assert wynik.top_areas == ("A", "C", "D")


def test_top_obszary_pomijaja_brak_danych(engine: ScoringEngine) -> None:
    # Oceniony tylko A; reszta ponizej progu -> tylko A w top.
    raw = {"A1": 4, "A2": 4, "A3": 4, "A4": 0}
    wynik = engine.score(raw)
    assert wynik.top_areas == ("A",)


def test_top_n_ogranicza_liczbe(engine: ScoringEngine) -> None:
    raw = {
        "A1": 4, "A2": 4,        # A oceniony
        "B1": 4, "B2": 4,        # B oceniony
        "C1": 4, "C2": 4,        # C oceniony
        "D1": 4, "D2": 4,        # D oceniony
    }
    wynik = engine.score(raw, top_n=2)
    assert len(wynik.top_areas) == 2


# --- pełny ScoringResult ---


def test_score_zwraca_pelny_wynik(engine: ScoringEngine) -> None:
    raw = {"A1": 4, "A2": 4, "A3": 4, "A4": 0}
    wynik = engine.score(raw)
    assert isinstance(wynik, ScoringResult)
    assert wynik.total_score == 100.0
    assert wynik.risk_band == RiskBand.VERY_HIGH
    # area_scores zawiera wszystkie 6 obszarow w kolejnosci A..F.
    assert tuple(a.category_id for a in wynik.area_scores) == ("A", "B", "C", "D", "E", "F")
    assert "A" not in wynik.unrated_areas
    assert set(wynik.unrated_areas) == {"B", "C", "D", "E", "F"}


def test_score_wszystko_pominiete_to_none(engine: ScoringEngine) -> None:
    wynik = engine.score({})
    assert wynik.total_score is None
    assert wynik.risk_band is None
    assert wynik.top_areas == ()
    assert set(wynik.unrated_areas) == {"A", "B", "C", "D", "E", "F"}


def test_score_pasmo_zgodne_z_total(
    engine: ScoringEngine, definicja: SurveyDefinition
) -> None:
    # Wszystkie odpowiedzi raw=2 -> risk 2 (odwracane i nie) -> kazdy S=50 -> total=50 -> HIGH.
    raw = {q.id: 2 for q in definicja.questions}
    wynik = engine.score(raw)
    assert wynik.total_score == 50.0
    assert wynik.risk_band == RiskBand.HIGH


def test_score_deterministyczny(engine: ScoringEngine) -> None:
    raw = {"A1": 1, "A2": 3, "B1": 2, "B2": 4, "C1": 0, "C2": 2, "D1": 1, "D2": 4}
    assert engine.score(raw) == engine.score(raw)


def test_unrated_obszary_maja_status_insufficient(engine: ScoringEngine) -> None:
    wynik = engine.score({"A1": 4, "A2": 4})
    for a in wynik.area_scores:
        if a.category_id in wynik.unrated_areas:
            assert a.status == AreaStatus.INSUFFICIENT_DATA
            assert a.score is None
