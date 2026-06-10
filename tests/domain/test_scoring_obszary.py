"""Testy wyniku obszaru i progu min. liczby odpowiedzi (Prompt 1.3, spec §3.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.common import AreaStatus
from domain.survey import ScoringEngine, SurveyDefinition, min_required_answers

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


@pytest.fixture(scope="module")
def engine(definicja: SurveyDefinition) -> ScoringEngine:
    return ScoringEngine(definicja)


# --- próg minimalnej liczby odpowiedzi ---


@pytest.mark.parametrize(("n", "prog"), [(4, 2), (3, 2)])
def test_prog_to_polowa_w_gore(n: int, prog: int) -> None:
    assert min_required_answers(n) == prog


# --- wzór S_obszar = (avg(udzielone)/4)*100 ---


def test_obszar_same_maksima_daje_100(engine: ScoringEngine) -> None:
    # A: A1,A2,A3 nieodwracane = 4; A4 odwracane raw=0 -> risk 4. avg=4 -> 100.
    wynik = engine.area_scores({"A1": 4, "A2": 4, "A3": 4, "A4": 0})
    a = wynik["A"]
    assert a.status == AreaStatus.RATED
    assert a.score == 100.0
    assert a.answered == 4


def test_obszar_same_minima_daje_0(engine: ScoringEngine) -> None:
    # C: wszystkie nieodwracane, raw=0 -> risk 0. avg=0 -> 0.
    wynik = engine.area_scores({"C1": 0, "C2": 0, "C3": 0, "C4": 0})
    assert wynik["C"].status == AreaStatus.RATED
    assert wynik["C"].score == 0.0


def test_obszar_srednia_z_dwojki(engine: ScoringEngine) -> None:
    # C1=2, C2=2 (oba udzielone), reszta C pominieta. avg=2 -> (2/4)*100 = 50.
    wynik = engine.area_scores({"C1": 2, "C2": 2})
    assert wynik["C"].status == AreaStatus.RATED
    assert wynik["C"].score == 50.0
    assert wynik["C"].answered == 2


def test_srednia_tylko_z_udzielonych_pomija_none(engine: ScoringEngine) -> None:
    # C1=4, C2=0, C3 i C4 pominiete. avg(4,0)=2 -> 50 (None NIE liczy sie jak 0).
    wynik = engine.area_scores({"C1": 4, "C2": 0, "C3": None, "C4": None})
    assert wynik["C"].score == 50.0
    assert wynik["C"].answered == 2


# --- próg: poniżej -> INSUFFICIENT_DATA, score=None ---


def test_kategoria_4pyt_ponizej_progu_to_brak_danych(engine: ScoringEngine) -> None:
    # tylko 1 odpowiedz w A (prog = 2).
    wynik = engine.area_scores({"A1": 3})
    assert wynik["A"].status == AreaStatus.INSUFFICIENT_DATA
    assert wynik["A"].score is None
    assert wynik["A"].answered == 1


def test_kategoria_4pyt_na_progu_jest_oceniana(engine: ScoringEngine) -> None:
    wynik = engine.area_scores({"A1": 4, "A3": 4})
    assert wynik["A"].status == AreaStatus.RATED
    assert wynik["A"].score == 100.0


def test_kategoria_3pyt_ponizej_progu(engine: ScoringEngine) -> None:
    # D ma 3 pytania, prog = 2; jedna odpowiedz -> brak danych.
    wynik = engine.area_scores({"D1": 2})
    assert wynik["D"].status == AreaStatus.INSUFFICIENT_DATA
    assert wynik["D"].score is None


def test_kategoria_3pyt_na_progu_jest_oceniana(engine: ScoringEngine) -> None:
    wynik = engine.area_scores({"D1": 2, "D2": 2})
    assert wynik["D"].status == AreaStatus.RATED
    assert wynik["D"].score == 50.0


def test_area_scores_zawiera_wszystkie_obszary(engine: ScoringEngine) -> None:
    wynik = engine.area_scores({"A1": 1, "A2": 1})
    assert set(wynik) == {"A", "B", "C", "D", "E", "F"}
    # obszary bez odpowiedzi -> brak danych
    assert wynik["F"].status == AreaStatus.INSUFFICIENT_DATA


def test_pusty_zestaw_wszystkie_obszary_bez_danych(engine: ScoringEngine) -> None:
    wynik = engine.area_scores({})
    assert all(a.status == AreaStatus.INSUFFICIENT_DATA for a in wynik.values())
    assert all(a.score is None for a in wynik.values())


def test_area_scores_deterministyczne(engine: ScoringEngine) -> None:
    raw = {"A1": 1, "A2": 3, "A4": 2, "C1": 4, "C2": 0}
    assert engine.area_scores(raw) == engine.area_scores(raw)
