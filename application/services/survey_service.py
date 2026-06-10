"""SurveyService - orkiestracja przypadku użycia ankiety (warstwa aplikacji).

Zależy WYŁĄCZNIE od domeny (definicja + ScoringEngine) i portu repozytorium.
Nie zna SQLite ani szczegółów zapisu. Czas jest wstrzykiwany (`clock`), by serwis
pozostał testowalny i deterministyczny.

Przepływ submit_survey (spec §4.1, §4.3): walidacja kompletności/zakresów →
scoring (ScoringEngine) → atomowy zapis (port) → zwrot SurveyResultDTO.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime

from application.dto.survey import (
    AreaScoreDTO,
    SessionSummaryDTO,
    SurveyAnswersDTO,
    SurveyResultDTO,
)
from application.ports.repositories import ISurveyRepository
from domain.survey import ScoringEngine, ScoringResult, SurveyDefinition, risk_band


class SurveyValidationError(ValueError):
    """Niespójne/niekompletne odpowiedzi ankiety (prezentacja pokaże komunikat)."""


class SurveyService:
    def __init__(
        self,
        definition: SurveyDefinition,
        repository: ISurveyRepository,
        clock: Callable[[], datetime],
    ) -> None:
        self._definition = definition
        self._repository = repository
        self._clock = clock
        self._engine = ScoringEngine(definition)

    def submit_survey(self, answers: SurveyAnswersDTO) -> SurveyResultDTO:
        """Waliduje, liczy i zapisuje sesję; zwraca wynik jako DTO."""
        self._waliduj(answers)

        mapping = answers.to_raw_mapping()
        risk_scores = self._engine.recode(mapping)
        result = self._engine.score(mapping)
        created_at = self._clock()
        session_id = self._repository.save_survey(
            answers=answers,
            risk_scores=risk_scores,
            result=result,
            created_at=created_at,
        )
        return self._do_result_dto(result, session_id=session_id, created_at=created_at)

    def get_history(self) -> list[SessionSummaryDTO]:
        return self._repository.get_history()

    def get_session(self, session_id: str) -> SurveyResultDTO | None:
        return self._repository.get_session(session_id)

    # --- szczegóły ---

    def _waliduj(self, answers: SurveyAnswersDTO) -> None:
        oczekiwane = {q.id for q in self._definition.questions}
        podane = answers.question_ids

        nieznane = podane - oczekiwane
        if nieznane:
            raise SurveyValidationError(
                f"Nieznane identyfikatory pytań: {sorted(nieznane)}."
            )
        brakujace = oczekiwane - podane
        if brakujace:
            raise SurveyValidationError(
                f"Brak odpowiedzi na pytania: {sorted(brakujace)}."
            )

        po_id = {a.question_id: a for a in answers.answers}
        for q in self._definition.questions:
            a = po_id[q.id]
            if a.skipped and not q.is_skippable:
                raise SurveyValidationError(
                    f"Pytanie {q.id} jest obowiązkowe - nie można go pominąć."
                )

    def _do_result_dto(
        self,
        result: ScoringResult,
        *,
        session_id: str | None,
        created_at: datetime | None,
    ) -> SurveyResultDTO:
        nazwy = {c.id: c.name for c in self._definition.categories}
        area_scores = [
            AreaScoreDTO(
                category_id=a.category_id,
                name=nazwy[a.category_id],
                score=a.score,
                status=a.status,
                band=risk_band(a.score) if a.score is not None else None,
            )
            for a in result.area_scores
        ]
        return SurveyResultDTO(
            session_id=session_id,
            created_at=created_at,
            total_score=result.total_score,
            risk_band=result.risk_band,
            area_scores=area_scores,
            top_areas=list(result.top_areas),
            unrated_areas=list(result.unrated_areas),
        )
