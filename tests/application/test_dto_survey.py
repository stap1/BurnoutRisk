"""Testy DTO ankiety (Prompt 2.1): zakresy 0-4, spójność pominięcia, mapowanie."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from application.dto import AnswerDTO, SurveyAnswersDTO
from application.ports import (
    ICoachRepository,
    ICryptoService,
    IEducationRepository,
    IKeyStore,
    ISurveyRepository,
)


# --- AnswerDTO: zakres 0-4 ---


@pytest.mark.parametrize("raw", [0, 1, 2, 3, 4])
def test_answer_akceptuje_zakres_0_4(raw: int) -> None:
    a = AnswerDTO(question_id="C1", raw_answer=raw)
    assert a.raw_answer == raw
    assert a.skipped is False


@pytest.mark.parametrize("zly", [-1, 5, 10])
def test_answer_odrzuca_poza_zakresem(zly: int) -> None:
    with pytest.raises(ValidationError):
        AnswerDTO(question_id="C1", raw_answer=zly)


# --- AnswerDTO: spójność pominięcia ---


def test_answer_skipped_poprawne() -> None:
    a = AnswerDTO(question_id="A1", raw_answer=None, skipped=True)
    assert a.skipped is True
    assert a.raw_answer is None


def test_answer_skipped_z_wartoscia_to_blad() -> None:
    with pytest.raises(ValidationError):
        AnswerDTO(question_id="A1", raw_answer=2, skipped=True)


def test_answer_brak_wartosci_bez_skipped_to_blad() -> None:
    with pytest.raises(ValidationError):
        AnswerDTO(question_id="A1", raw_answer=None, skipped=False)


def test_answer_odrzuca_nieznane_pole() -> None:
    with pytest.raises(ValidationError):
        AnswerDTO(question_id="A1", raw_answer=1, foo="bar")  # type: ignore[call-arg]


# --- SurveyAnswersDTO ---


def test_survey_answers_wymaga_co_najmniej_jednej() -> None:
    with pytest.raises(ValidationError):
        SurveyAnswersDTO(answers=[])


def test_survey_answers_odrzuca_duplikaty() -> None:
    with pytest.raises(ValidationError):
        SurveyAnswersDTO(
            answers=[
                AnswerDTO(question_id="C1", raw_answer=1),
                AnswerDTO(question_id="C1", raw_answer=2),
            ]
        )


def test_to_raw_mapping_skipped_daje_none() -> None:
    dto = SurveyAnswersDTO(
        answers=[
            AnswerDTO(question_id="C1", raw_answer=3),
            AnswerDTO(question_id="A1", raw_answer=None, skipped=True),
        ]
    )
    mapping = dto.to_raw_mapping()
    assert mapping == {"C1": 3, "A1": None}


def test_question_ids_property() -> None:
    dto = SurveyAnswersDTO(
        answers=[
            AnswerDTO(question_id="C1", raw_answer=3),
            AnswerDTO(question_id="C2", raw_answer=1),
        ]
    )
    assert dto.question_ids == {"C1", "C2"}


# --- Porty są abstrakcyjne (nie da się utworzyć bez implementacji) ---


@pytest.mark.parametrize(
    "port",
    [
        ISurveyRepository,
        ICoachRepository,
        IEducationRepository,
        ICryptoService,
        IKeyStore,
    ],
)
def test_porty_sa_abstrakcyjne(port: type) -> None:
    with pytest.raises(TypeError):
        port()  # type: ignore[abstract]
