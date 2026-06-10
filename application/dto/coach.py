"""DTO coachingu na granicach warstw (Prompt 4.4)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from domain.common import Goal

SKALA_MAX = 10


class CoachActionDTO(BaseModel):
    """Mikro-działanie planu w odczycie (z bazy)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    action_type: str
    description: str
    scheduled_day: int
    completed_date: str | None = None
    rating: int | None = Field(default=None, ge=0, le=5)


class CoachPlanDTO(BaseModel):
    """Plan coachingu w odczycie."""

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: datetime
    based_on_session_id: str | None
    goal: Goal
    daily_time_budget: int
    escalation_flag: bool
    focus_areas: list[str]
    actions: list[CoachActionDTO]


class CoachConfigDTO(BaseModel):
    """Konfiguracja z wizarda coachingu (cel + budżet czasu)."""

    model_config = ConfigDict(extra="forbid")

    based_on_session_id: str
    goal: Goal
    daily_time_budget: int = Field(ge=1)


class CheckInDTO(BaseModel):
    """Dzienny check-in (notatka szyfrowana w infrastrukturze)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    plan_id: str | None = None
    date: str
    stress: int = Field(ge=0, le=SKALA_MAX)
    sleep: int = Field(ge=0, le=SKALA_MAX)
    energy: int = Field(ge=0, le=SKALA_MAX)
    note: str | None = None


class OutcomeDTO(BaseModel):
    """Okresowa ocena efektu (komentarz szyfrowany)."""

    model_config = ConfigDict(extra="forbid")

    id: str | None = None
    plan_id: str
    date: str
    perceived_burnout: int = Field(ge=0, le=SKALA_MAX)
    comments: str | None = None


class CheckInResultDTO(BaseModel):
    """Wynik zapisu check-inu: id + ewentualna miękka sugestia trendowa."""

    model_config = ConfigDict(extra="forbid")

    checkin_id: str
    trend_enough_data: bool
    trend_worsening: bool
    trend_suggestion: str | None = None
