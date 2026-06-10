"""Regresja #1: generator nie crashuje przy budżecie poniżej najkrótszego działania."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.coaching import CoachPlanGenerator
from domain.common import AreaStatus, Goal, RiskBand
from domain.survey import AreaScore, ScoringResult
from infrastructure.persistence.coach_actions_loader import load_coach_actions


@pytest.fixture(scope="module")
def generator() -> CoachPlanGenerator:
    return CoachPlanGenerator(load_coach_actions())


def _wynik_C80() -> ScoringResult:
    obszary = []
    for o in ("A", "B", "C", "D", "E", "F"):
        if o == "C":
            obszary.append(AreaScore(category_id="C", score=80.0, status=AreaStatus.RATED, answered=4, question_count=4))
        else:
            obszary.append(AreaScore(category_id=o, score=None, status=AreaStatus.INSUFFICIENT_DATA, answered=0, question_count=3))
    return ScoringResult(
        total_score=80.0, risk_band=RiskBand.VERY_HIGH,
        area_scores=tuple(obszary), top_areas=("C",),
        unrated_areas=("A", "B", "D", "E", "F"),
    )


def test_budzet_ponizej_minimum_daje_pusty_plan_bez_crasha(generator: CoachPlanGenerator) -> None:
    # Budżet 3 < najkrótsze działanie (5 min) -> brak kandydatów; ma zwrócić pusty
    # plan, nie ZeroDivisionError.
    plan = generator.generate(_wynik_C80(), goal=Goal.STRES, daily_time_budget=3)
    assert plan.actions == ()


def test_budzet_5_nadal_generuje(generator: CoachPlanGenerator) -> None:
    plan = generator.generate(_wynik_C80(), goal=Goal.STRES, daily_time_budget=5)
    assert len(plan.actions) == 14
    assert all(a.minutes <= 5 for a in plan.actions)
