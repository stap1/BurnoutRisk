"""Regresja #1: CoachConfigDTO dopuszcza tylko budżety {5,10,15}."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from application.dto import CoachConfigDTO
from domain.common import Goal


@pytest.mark.parametrize("budzet", [5, 10, 15])
def test_dozwolone_budzety(budzet: int) -> None:
    dto = CoachConfigDTO(based_on_session_id="s1", goal=Goal.STRES, daily_time_budget=budzet)
    assert dto.daily_time_budget == budzet


@pytest.mark.parametrize("zly", [1, 3, 4, 7, 20])
def test_odrzuca_budzet_spoza_listy(zly: int) -> None:
    with pytest.raises(ValidationError):
        CoachConfigDTO(based_on_session_id="s1", goal=Goal.STRES, daily_time_budget=zly)
