"""DTO safety-netu na granicy do prezentacji (Prompt 6.1)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CrisisResourceDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: str
    name: str
    description: str
    link: str


class SafetyNetDTO(BaseModel):
    """Komunikat ramowy + lista zasobów wsparcia."""

    model_config = ConfigDict(extra="forbid")

    framing_message: str
    resources: list[CrisisResourceDTO]
