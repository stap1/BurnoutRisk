"""DTO ankiety przepływające na granicach warstw (Prompt 2.1).

DTO są walidowanymi obiektami Pydantic. Encje domenowe nie wyciekają do
prezentacji - na granicy stoją te struktury (spec §1.2.2). Tu mieszka też
walidacja zakresów (0-4) i spójności pominięcia.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from domain.common import AreaStatus, RiskBand


class AnswerDTO(BaseModel):
    """Pojedyncza odpowiedź z UI.

    Albo udzielona (`raw_answer` 0-4, `skipped=False`), albo świadomie pominięta
    ("wolę nie odpowiadać": `raw_answer=None`, `skipped=True`). `raw_answer=None`
    oznacza zawsze brak danych - nigdy zero.
    """

    model_config = ConfigDict(extra="forbid")

    question_id: str
    raw_answer: int | None = Field(default=None, ge=0, le=4)
    skipped: bool = False

    @model_validator(mode="after")
    def _spojnosc_pominiecia(self) -> AnswerDTO:
        if self.skipped and self.raw_answer is not None:
            raise ValueError(
                f"{self.question_id}: pytanie pominięte nie może mieć raw_answer."
            )
        if not self.skipped and self.raw_answer is None:
            raise ValueError(
                f"{self.question_id}: brak odpowiedzi musi być oznaczony jako skipped."
            )
        return self


class SurveyAnswersDTO(BaseModel):
    """Komplet odpowiedzi przekazywany do `submit_survey`."""

    model_config = ConfigDict(extra="forbid")

    answers: list[AnswerDTO] = Field(min_length=1)

    @model_validator(mode="after")
    def _unikalne_pytania(self) -> SurveyAnswersDTO:
        ids = [a.question_id for a in self.answers]
        if len(ids) != len(set(ids)):
            raise ValueError("Odpowiedzi zawierają zduplikowane identyfikatory pytań.")
        return self

    def to_raw_mapping(self) -> dict[str, int | None]:
        """Mapuje odpowiedzi na wejście ScoringEngine: skipped -> None."""
        return {
            a.question_id: (None if a.skipped else a.raw_answer)
            for a in self.answers
        }

    @property
    def question_ids(self) -> set[str]:
        return {a.question_id for a in self.answers}


class QuestionDTO(BaseModel):
    """Pytanie ankiety przygotowane pod prezentację (kolejność wyświetlania)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    category: str
    text: str
    is_skippable: bool
    display_order: int


class SurveyFormDTO(BaseModel):
    """Komplet do wyświetlenia ankiety: pytania (wg kolejności) + skala odpowiedzi."""

    model_config = ConfigDict(extra="forbid")

    questions: list[QuestionDTO]
    answer_scale: list[tuple[int, str]]


class AreaScoreDTO(BaseModel):
    """Wynik obszaru przygotowany pod prezentację (z nazwą obszaru)."""

    model_config = ConfigDict(extra="forbid")

    category_id: str
    name: str
    score: float | None
    status: AreaStatus
    band: RiskBand | None = None


class SurveyResultDTO(BaseModel):
    """Wynik sesji ankiety na granicy do prezentacji."""

    model_config = ConfigDict(extra="forbid")

    session_id: str | None = None
    created_at: datetime | None = None
    total_score: float | None
    risk_band: RiskBand | None
    area_scores: list[AreaScoreDTO]
    top_areas: list[str]
    unrated_areas: list[str]


class SessionSummaryDTO(BaseModel):
    """Skrót sesji na liście historii."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    created_at: datetime
    total_score: float | None
    risk_band: RiskBand | None
