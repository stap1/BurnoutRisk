"""DTO modułu edukacyjnego na granicach warstw (Prompt 5.3)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuizQuestionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str
    options: list[str]
    correct_index: int


class EducationSectionDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    heading: str
    body: str


class EducationTopicDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    sections: list[EducationSectionDTO]
    key_points: list[str]
    when_to_seek_help: str
    quiz: list[QuizQuestionDTO]


class EducationProgressDTO(BaseModel):
    """Postęp w temacie: kiedy pierwszy/ostatni raz oglądany, wynik quizu."""

    model_config = ConfigDict(extra="forbid")

    topic_id: str
    first_viewed_at: datetime
    last_viewed_at: datetime
    quiz_score: int | None = Field(default=None, ge=0)
