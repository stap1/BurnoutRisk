"""Test integracyjny AppFacade + composition root (Prompt 6.1).

Buduje pełną fasadę na bazie tymczasowej i z atrapą keyring, po czym przechodzi
przez główne przypadki użycia end-to-end (ankieta → wynik → plan → check-in →
edukacja → safety-net → wipe)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from app_facade import AppFacade
from application.dto import (
    AnswerDTO,
    CheckInDTO,
    CoachConfigDTO,
    SurveyAnswersDTO,
)
from composition_root import build_app_facade
from domain.common import Goal


class FakeKeyring:
    def __init__(self) -> None:
        self._store: dict[tuple[str, str], str] = {}

    def get_password(self, service: str, username: str) -> str | None:
        return self._store.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        self._store[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._store.pop((service, username), None)


@pytest.fixture
def facade(tmp_path: Path) -> AppFacade:
    return build_app_facade(
        db_path=tmp_path / "baza.db",
        keyring_backend=FakeKeyring(),
        clock=lambda: datetime(2026, 6, 10, 12, 0, 0),
    )


def _komplet_odpowiedzi(facade: AppFacade, raw: int = 4) -> SurveyAnswersDTO:
    form = facade.get_survey_form()
    return SurveyAnswersDTO(
        answers=[AnswerDTO(question_id=q.id, raw_answer=raw) for q in form.questions]
    )


def test_buduje_fasade(facade: AppFacade) -> None:
    assert isinstance(facade, AppFacade)
    assert facade.is_keyring_safe() is True  # FakeKeyring jest "bezpieczny"


def test_get_survey_form(facade: AppFacade) -> None:
    form = facade.get_survey_form()
    assert len(form.questions) == 21
    # Kolejność wyświetlania rosnąca.
    kolejnosc = [q.display_order for q in form.questions]
    assert kolejnosc == sorted(kolejnosc)
    assert len(form.answer_scale) == 5  # skala 0-4


def test_submit_survey_i_historia(facade: AppFacade) -> None:
    wynik = facade.submit_survey(_komplet_odpowiedzi(facade, raw=4))
    assert wynik.session_id is not None
    historia = facade.get_history()
    assert len(historia) == 1
    assert historia[0].session_id == wynik.session_id
    # Odczyt szczegółów sesji.
    assert facade.get_session(wynik.session_id) is not None


def test_pelny_przeplyw_coachingu(facade: AppFacade) -> None:
    # Wysoki wynik w obszarze C (zbyt dużo pracy/stres) -> plan z działaniami C.
    form = facade.get_survey_form()
    answers = []
    for q in form.questions:
        if q.category == "C":
            answers.append(AnswerDTO(question_id=q.id, raw_answer=4))
        else:
            # niskie ryzyko gdzie indziej (odwracane=4 -> 0)
            answers.append(AnswerDTO(question_id=q.id, raw_answer=4 if q_is_reversed(q) else 0))
    wynik = facade.submit_survey(SurveyAnswersDTO(answers=answers))

    plan = facade.create_coach_plan(
        CoachConfigDTO(
            based_on_session_id=wynik.session_id,
            goal=Goal.STRES,
            daily_time_budget=10,
        )
    )
    assert plan.daily_time_budget == 10
    assert len(plan.actions) == 14
    assert facade.get_latest_plan() is not None

    # Check-in -> wynik z polem trendu (jeden check-in: za mało danych, cicho).
    wynik_ci = facade.submit_checkin(
        CheckInDTO(plan_id=plan.id, date="2026-06-10", stress=7, sleep=4, energy=4, note="trudny dzień")
    )
    assert wynik_ci.trend_enough_data is False
    assert wynik_ci.trend_suggestion is None


def q_is_reversed(q) -> bool:  # pomocnik czytelności w teście
    return q.id in {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}


def test_edukacja_przez_fasade(facade: AppFacade) -> None:
    tematy = facade.get_education_topics()
    assert len(tematy) >= 5
    temat = tematy[0]
    facade.record_topic_view(temat.id)
    progress = facade.submit_quiz(temat.id, [q.correct_index for q in temat.quiz])
    assert progress.quiz_score == len(temat.quiz)


def test_safety_net_przez_fasade(facade: AppFacade) -> None:
    sn = facade.get_safety_net()
    assert sn.framing_message.strip()
    numery = {r.number for r in sn.resources}
    assert {"112", "116 123", "800 70 2222", "116 111"} <= numery


def test_wipe_przez_fasade(facade: AppFacade) -> None:
    wynik = facade.submit_survey(_komplet_odpowiedzi(facade))
    assert facade.get_history()
    facade.wipe_all_data()
    assert facade.get_history() == []


def test_delete_session_przez_fasade(facade: AppFacade) -> None:
    wynik = facade.submit_survey(_komplet_odpowiedzi(facade))
    assert facade.delete_session(wynik.session_id) is True
    assert facade.get_history() == []
