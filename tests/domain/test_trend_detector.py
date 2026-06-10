"""Testy TrendDetector: wskaźnik złożony, minimum danych, utrzymujący się trend."""

from __future__ import annotations

import pytest

from domain.coaching import (
    SOFT_SUGGESTION,
    CheckinPoint,
    TrendConfig,
    TrendDetector,
)


@pytest.fixture
def detektor() -> TrendDetector:
    return TrendDetector()


def _ci(stress: int, sleep: int, energy: int) -> CheckinPoint:
    return CheckinPoint(stress=stress, sleep=sleep, energy=energy)


# --- wskaźnik złożony i kierunek (stres odwrócony) ---


def test_wskaznik_kierunek(detektor: TrendDetector) -> None:
    # Najgorzej: max stres, zero snu/energii -> 0. Najlepiej -> 10.
    assert detektor.wellbeing_index(_ci(10, 0, 0)) == 0
    assert detektor.wellbeing_index(_ci(0, 10, 10)) == 10


def test_stres_obniza_wskaznik(detektor: TrendDetector) -> None:
    lepszy = detektor.wellbeing_index(_ci(2, 5, 5))
    gorszy = detektor.wellbeing_index(_ci(8, 5, 5))
    assert gorszy < lepszy


# --- minimum danych: cicho ---


def test_ponizej_minimum_brak_sugestii(detektor: TrendDetector) -> None:
    wynik = detektor.detect([_ci(5, 5, 5), _ci(6, 5, 5)])
    assert wynik.enough_data is False
    assert wynik.worsening is False
    assert wynik.suggestion is None


# --- utrzymujący się trend spadkowy wyzwala sugestię ---


def test_utrzymujacy_sie_spadek_wyzwala() -> None:
    det = TrendDetector()
    # stres rosnie o 2 na krok -> wellbeing spada o ~0.667 na krok (>0.5 progu).
    checkins = [_ci(s, 5, 5) for s in (0, 2, 4, 6, 8, 10)]
    wynik = det.detect(checkins)
    assert wynik.enough_data is True
    assert wynik.worsening is True
    assert wynik.suggestion == SOFT_SUGGESTION


def test_pojedynczy_spadek_nie_wyzwala(detektor: TrendDetector) -> None:
    # Stabilnie, z jednym gorszym dniem w srodku - nie trend.
    checkins = [_ci(3, 6, 6), _ci(3, 6, 6), _ci(7, 3, 3), _ci(3, 6, 6), _ci(3, 6, 6), _ci(3, 6, 6)]
    wynik = detektor.detect(checkins)
    assert wynik.enough_data is True
    assert wynik.worsening is False
    assert wynik.suggestion is None


def test_poprawa_nie_wyzwala(detektor: TrendDetector) -> None:
    checkins = [_ci(s, 5, 5) for s in (10, 8, 6, 4, 2, 0)]  # poprawa
    wynik = detektor.detect(checkins)
    assert wynik.worsening is False


def test_stabilnie_nie_wyzwala(detektor: TrendDetector) -> None:
    checkins = [_ci(5, 5, 5) for _ in range(8)]
    wynik = detektor.detect(checkins)
    assert wynik.enough_data is True
    assert wynik.worsening is False


# --- progi konfigurowalne ---


def test_surowszy_prog_nie_wyzwala() -> None:
    # Spadek ~0.667/krok; przy min_decline=2.0 nie kwalifikuje sie.
    det = TrendDetector(TrendConfig(min_decline=2.0))
    checkins = [_ci(s, 5, 5) for s in (0, 2, 4, 6, 8, 10)]
    assert det.detect(checkins).worsening is False


def test_wiecej_wymaganych_spadkow_nie_wyzwala() -> None:
    # Wymagamy 5 kolejnych spadkow - krotka seria nie spelni.
    det = TrendDetector(TrendConfig(consecutive_declines=5))
    checkins = [_ci(s, 5, 5) for s in (0, 2, 4, 6, 8, 10)]
    assert det.detect(checkins).enough_data is False


def test_determinizm() -> None:
    det = TrendDetector()
    checkins = [_ci(s, 5, 5) for s in (0, 2, 4, 6, 8, 10)]
    assert det.detect(checkins) == det.detect(checkins)
