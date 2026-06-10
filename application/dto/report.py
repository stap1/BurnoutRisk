"""DTO raportowania / postępu (Prompt 8.1)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TrendPointDTO(BaseModel):
    """Punkt na osi czasu (etykieta + wartość)."""

    model_config = ConfigDict(extra="forbid")

    label: str
    value: float


class AgencySummaryDTO(BaseModel):
    """Warstwa sprawczości (spec §6.3.1 pkt 3) - co się udało, nie tylko krzywa."""

    model_config = ConfigDict(extra="forbid")

    completed_actions: int
    total_actions: int
    checkin_count: int
    improved_areas: list[str]
    worsened_areas: list[str]


class ProgressReportDTO(BaseModel):
    """Komplet danych do ProgressPage: trendy + warstwa sprawczości."""

    model_config = ConfigDict(extra="forbid")

    session_trend: list[TrendPointDTO]
    checkin_trend: list[TrendPointDTO]
    agency: AgencySummaryDTO
