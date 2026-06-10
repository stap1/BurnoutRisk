"""Testy CoachPlanGenerator: determinizm, progi, budżet, ścieżka A (Prompt 4.2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from domain.coaching import (
    BASE_THRESHOLD,
    PLAN_DAYS,
    SAFETY_NOTE,
    CoachPlanGenerator,
)
from domain.common import AreaStatus, Goal, RiskBand
from domain.survey import AreaScore, ScoringResult
from infrastructure.persistence.coach_actions_loader import load_coach_actions

ACTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "coach_actions.json"


@pytest.fixture(scope="module")
def generator() -> CoachPlanGenerator:
    return CoachPlanGenerator(load_coach_actions())


def _wynik(scores: dict[str, float | None]) -> ScoringResult:
    """Buduje ScoringResult z mapy obszar->score (None => INSUFFICIENT_DATA)."""
    area_scores = []
    for obszar in ("A", "B", "C", "D", "E", "F"):
        s = scores.get(obszar)
        if s is None:
            area_scores.append(
                AreaScore(
                    category_id=obszar, score=None,
                    status=AreaStatus.INSUFFICIENT_DATA, answered=0, question_count=3,
                )
            )
        else:
            area_scores.append(
                AreaScore(
                    category_id=obszar, score=s,
                    status=AreaStatus.RATED, answered=3, question_count=3,
                )
            )
    rated = [a for a in area_scores if a.status is AreaStatus.RATED]
    total = sum(a.score for a in rated) / len(rated) if rated else None
    return ScoringResult(
        total_score=total,
        risk_band=RiskBand.HIGH if total is not None else None,
        area_scores=tuple(area_scores),
        top_areas=tuple(a.category_id for a in rated),
        unrated_areas=tuple(
            a.category_id for a in area_scores if a.status is AreaStatus.INSUFFICIENT_DATA
        ),
    )


def test_determinizm(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"C": 80, "D": 75, "F": 65})
    p1 = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    p2 = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert p1 == p2


def test_plan_ma_14_dni(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"C": 80})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert len(plan.actions) == PLAN_DAYS
    assert [a.day for a in plan.actions] == list(range(1, PLAN_DAYS + 1))


def test_tylko_obszary_powyzej_progu(generator: CoachPlanGenerator) -> None:
    # C=80 (>60) priorytet; D=40 (<60) nie.
    wynik = _wynik({"C": 80, "D": 40})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    obszary = {a.area for a in plan.actions}
    assert obszary == {"C"}
    assert plan.focus_areas == ("C",)


def test_budzet_respektowany(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"C": 80, "F": 70})
    plan = generator.generate(wynik, goal=Goal.ENERGIA, daily_time_budget=5)
    assert all(a.minutes <= 5 for a in plan.actions)


def test_brak_obszarow_powyzej_progu_pusty_plan(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"C": 50, "D": 30})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan.actions == ()
    assert plan.escalation_flag is False
    assert plan.safety_note == SAFETY_NOTE  # nota zawsze obecna


def test_safety_note_zawsze_obecna(generator: CoachPlanGenerator) -> None:
    plan = generator.generate(_wynik({"C": 80}), goal=Goal.STRES, daily_time_budget=10)
    assert plan.safety_note == SAFETY_NOTE


# --- ścieżka obszaru A (§7) ---


def test_obszar_a_wysoki_ustawia_eskalacje_bez_dzialan_a(
    generator: CoachPlanGenerator,
) -> None:
    wynik = _wynik({"A": 80})
    plan = generator.generate(wynik, goal=Goal.RELACJE, daily_time_budget=10)
    assert plan.escalation_flag is True
    # Obszar A NIE generuje mikro-działań.
    assert all(a.area != "A" for a in plan.actions)
    assert "A" not in plan.focus_areas


def test_a_wysoki_z_innym_obszarem_eskalacja_i_dzialania_bf(
    generator: CoachPlanGenerator,
) -> None:
    wynik = _wynik({"A": 80, "C": 75})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan.escalation_flag is True
    obszary = {a.area for a in plan.actions}
    assert obszary == {"C"}  # B-F generuja, A nie
    assert "A" not in obszary


def test_a_ponizej_progu_brak_eskalacji(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"A": 50, "C": 80})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan.escalation_flag is False


def test_a_insufficient_data_brak_eskalacji(generator: CoachPlanGenerator) -> None:
    # A pominiete (A1/A2) -> INSUFFICIENT_DATA -> nie wnioskujemy eskalacji.
    wynik = _wynik({"A": None, "C": 80})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan.escalation_flag is False


# --- konfigurowalny próg ---


def test_prog_konfigurowalny_per_obszar(generator: CoachPlanGenerator) -> None:
    wynik = _wynik({"C": 55})
    # Domyślnie 55 < 60 -> brak. Z progiem C=50 -> priorytet.
    plan_domyslny = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan_domyslny.actions == ()

    plan_strojony = generator.generate(
        wynik, goal=Goal.STRES, daily_time_budget=10, thresholds={"C": 50}
    )
    assert {a.area for a in plan_strojony.actions} == {"C"}


def test_prog_bazowy_to_60(generator: CoachPlanGenerator) -> None:
    # Dokładnie na progu (60) NIE jest priorytetem (warunek to ostre >).
    wynik = _wynik({"C": BASE_THRESHOLD})
    plan = generator.generate(wynik, goal=Goal.STRES, daily_time_budget=10)
    assert plan.actions == ()


def test_cel_preferowany_w_doborze(generator: CoachPlanGenerator) -> None:
    # Dla obszaru F dzialania maja cel ENERGIA; przy goal=ENERGIA powinny wejsc.
    wynik = _wynik({"F": 80})
    plan = generator.generate(wynik, goal=Goal.ENERGIA, daily_time_budget=15)
    assert plan.actions
    assert all(a.area == "F" for a in plan.actions)
    # Pierwsze dzialanie ma cel zgodny z wyborem (preferencja celu).
    assert plan.actions[0].action_id.startswith("F")
