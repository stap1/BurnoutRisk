"""Testy SurveyService (Prompt 2.2) z atrapami portów."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from application.dto import AnswerDTO, SessionSummaryDTO, SurveyAnswersDTO
from application.ports import ISurveyRepository
from application.services import SurveyService, SurveyValidationError
from domain.common import RiskBand
from domain.survey import ScoringResult, SurveyDefinition

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"
STALY_CZAS = datetime(2026, 6, 10, 12, 0, 0)


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


class FakeSurveyRepository(ISurveyRepository):
    """Atrapa portu - rejestruje ostatni zapis, zwraca stały identyfikator."""

    def __init__(self) -> None:
        self.saved: list[dict] = []
        self.history: list[SessionSummaryDTO] = []

    def save_survey(self, *, answers, risk_scores, result, created_at) -> str:  # type: ignore[override]
        self.saved.append(
            {
                "answers": answers,
                "risk_scores": risk_scores,
                "result": result,
                "created_at": created_at,
            }
        )
        return "sesja-123"

    def get_history(self) -> list[SessionSummaryDTO]:
        return self.history

    def get_session(self, session_id: str):  # type: ignore[override]
        return None


def _pelne_odpowiedzi(definicja: SurveyDefinition, raw: int = 2) -> SurveyAnswersDTO:
    """Komplet poprawnych odpowiedzi (każde pytanie udzielone wartością raw)."""
    return SurveyAnswersDTO(
        answers=[AnswerDTO(question_id=q.id, raw_answer=raw) for q in definicja.questions]
    )


@pytest.fixture
def repo() -> FakeSurveyRepository:
    return FakeSurveyRepository()


@pytest.fixture
def service(definicja: SurveyDefinition, repo: FakeSurveyRepository) -> SurveyService:
    return SurveyService(definicja, repo, clock=lambda: STALY_CZAS)


def test_submit_zwraca_result_dto(service: SurveyService, definicja: SurveyDefinition) -> None:
    wynik = service.submit_survey(_pelne_odpowiedzi(definicja, raw=2))
    assert wynik.session_id == "sesja-123"
    assert wynik.created_at == STALY_CZAS
    # wszystkie raw=2 -> kazdy obszar S=50 -> total=50 -> HIGH
    assert wynik.total_score == 50.0
    assert wynik.risk_band == RiskBand.HIGH
    assert {a.category_id for a in wynik.area_scores} == {"A", "B", "C", "D", "E", "F"}


def test_submit_wola_zapis_raz_z_wynikiem(
    service: SurveyService, repo: FakeSurveyRepository, definicja: SurveyDefinition
) -> None:
    service.submit_survey(_pelne_odpowiedzi(definicja))
    assert len(repo.saved) == 1
    zapis = repo.saved[0]
    assert isinstance(zapis["result"], ScoringResult)
    assert zapis["created_at"] == STALY_CZAS


def test_area_score_dto_ma_nazwy(service: SurveyService, definicja: SurveyDefinition) -> None:
    wynik = service.submit_survey(_pelne_odpowiedzi(definicja))
    nazwy = {a.category_id: a.name for a in wynik.area_scores}
    assert nazwy["A"]  # niepusta nazwa obszaru


def test_skipped_pomijalnego_jest_ok(
    service: SurveyService, definicja: SurveyDefinition
) -> None:
    # A1 jest pomijalne - "wole nie odpowiadac".
    answers = []
    for q in definicja.questions:
        if q.id == "A1":
            answers.append(AnswerDTO(question_id="A1", raw_answer=None, skipped=True))
        else:
            answers.append(AnswerDTO(question_id=q.id, raw_answer=2))
    wynik = service.submit_survey(SurveyAnswersDTO(answers=answers))
    assert wynik.total_score is not None


def test_pominiecie_obowiazkowego_to_blad(
    service: SurveyService, definicja: SurveyDefinition
) -> None:
    # A3 nie jest pomijalne.
    answers = []
    for q in definicja.questions:
        if q.id == "A3":
            answers.append(AnswerDTO(question_id="A3", raw_answer=None, skipped=True))
        else:
            answers.append(AnswerDTO(question_id=q.id, raw_answer=2))
    with pytest.raises(SurveyValidationError):
        service.submit_survey(SurveyAnswersDTO(answers=answers))


def test_brak_pytania_to_blad(service: SurveyService, definicja: SurveyDefinition) -> None:
    answers = [
        AnswerDTO(question_id=q.id, raw_answer=2)
        for q in definicja.questions
        if q.id != "D3"  # pomijamy jedno
    ]
    with pytest.raises(SurveyValidationError):
        service.submit_survey(SurveyAnswersDTO(answers=answers))


def test_nieznane_pytanie_to_blad(service: SurveyService, definicja: SurveyDefinition) -> None:
    answers = [AnswerDTO(question_id=q.id, raw_answer=2) for q in definicja.questions]
    answers.append(AnswerDTO(question_id="Z9", raw_answer=1))
    with pytest.raises(SurveyValidationError):
        service.submit_survey(SurveyAnswersDTO(answers=answers))


def test_blad_walidacji_nie_zapisuje(
    service: SurveyService, repo: FakeSurveyRepository, definicja: SurveyDefinition
) -> None:
    answers = [
        AnswerDTO(question_id=q.id, raw_answer=2)
        for q in definicja.questions
        if q.id != "D3"
    ]
    with pytest.raises(SurveyValidationError):
        service.submit_survey(SurveyAnswersDTO(answers=answers))
    assert repo.saved == []


def test_get_history_deleguje(
    service: SurveyService, repo: FakeSurveyRepository
) -> None:
    repo.history = [
        SessionSummaryDTO(
            session_id="s1",
            created_at=STALY_CZAS,
            total_score=42.0,
            risk_band=RiskBand.MODERATE,
        )
    ]
    assert service.get_history() == repo.history
