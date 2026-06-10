"""AppFacade - jedyny punkt styku warstwy prezentacji z resztą systemu.

Wystawia metody odpowiadające przypadkom użycia (spec §1.2.2), przyjmuje i zwraca
DTO (Pydantic). Encje domenowe NIE wyciekają do prezentacji. Zależności są
wstrzykiwane w composition root (ręczna iniekcja, bez frameworka DI).
"""

from __future__ import annotations

from collections.abc import Sequence

from application.dto import (
    CheckInDTO,
    CheckInResultDTO,
    CoachConfigDTO,
    CoachPlanDTO,
    CrisisResourceDTO,
    EducationProgressDTO,
    EducationTopicDTO,
    QuestionDTO,
    SafetyNetDTO,
    SessionSummaryDTO,
    SurveyAnswersDTO,
    SurveyFormDTO,
    SurveyResultDTO,
)
from application.services import CoachService, EducationService, SurveyService
from domain.safety import CrisisResources
from domain.survey import SurveyDefinition
from infrastructure.persistence.wipe import WipeService


class AppFacade:
    def __init__(
        self,
        *,
        survey_definition: SurveyDefinition,
        survey_service: SurveyService,
        coach_service: CoachService,
        education_service: EducationService,
        crisis_resources: CrisisResources,
        wipe_service: WipeService,
        keyring_safe: bool,
    ) -> None:
        self._definition = survey_definition
        self._survey = survey_service
        self._coach = coach_service
        self._education = education_service
        self._crisis = crisis_resources
        self._wipe = wipe_service
        self._keyring_safe = keyring_safe

    # --- start / stan ---

    def is_keyring_safe(self) -> bool:
        """False → UI pokazuje uczciwe ostrzeżenie o słabej ochronie (§12.6)."""
        return self._keyring_safe

    # --- ankieta ---

    def get_survey_form(self) -> SurveyFormDTO:
        questions = [
            QuestionDTO(
                id=q.id,
                category=q.category,
                text=q.text,
                is_skippable=q.is_skippable,
                display_order=q.display_order,
            )
            for q in self._definition.questions_in_display_order
        ]
        return SurveyFormDTO(
            questions=questions,
            answer_scale=[list(p) for p in self._definition.answer_scale],  # type: ignore[misc]
        )

    def submit_survey(self, answers: SurveyAnswersDTO) -> SurveyResultDTO:
        return self._survey.submit_survey(answers)

    def get_history(self) -> list[SessionSummaryDTO]:
        return self._survey.get_history()

    def get_session(self, session_id: str) -> SurveyResultDTO | None:
        return self._survey.get_session(session_id)

    # --- coaching ---

    def create_coach_plan(self, config: CoachConfigDTO) -> CoachPlanDTO:
        return self._coach.create_plan(config)

    def get_latest_plan(self) -> CoachPlanDTO | None:
        return self._coach.get_latest_plan()

    def update_coach_action(
        self, action_id: str, *, completed: bool, rating: int | None
    ) -> None:
        self._coach.update_action(action_id, completed=completed, rating=rating)

    def submit_checkin(self, checkin: CheckInDTO) -> CheckInResultDTO:
        return self._coach.submit_checkin(checkin)

    # --- edukacja ---

    def get_education_disclaimer(self) -> str:
        return self._education.get_disclaimer()

    def get_education_topics(self) -> list[EducationTopicDTO]:
        return self._education.get_topics()

    def get_education_topic(self, topic_id: str) -> EducationTopicDTO | None:
        return self._education.get_topic(topic_id)

    def record_topic_view(self, topic_id: str) -> EducationProgressDTO:
        return self._education.record_view(topic_id)

    def submit_quiz(self, topic_id: str, answers: Sequence[int]) -> EducationProgressDTO:
        return self._education.submit_quiz(topic_id, answers)

    def get_education_progress(self, topic_id: str) -> EducationProgressDTO | None:
        return self._education.get_progress(topic_id)

    # --- safety-net (dostępny zawsze, z każdego ekranu) ---

    def get_safety_net(self) -> SafetyNetDTO:
        return SafetyNetDTO(
            framing_message=self._crisis.framing_message,
            resources=[
                CrisisResourceDTO(
                    number=r.number,
                    name=r.name,
                    description=r.description,
                    link=r.link,
                )
                for r in self._crisis.resources
            ],
        )

    # --- kasowanie / retencja ---

    def delete_session(self, session_id: str) -> bool:
        return self._wipe.delete_session(session_id)

    def wipe_all_data(self) -> None:
        self._wipe.full_wipe()
