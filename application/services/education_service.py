"""EducationService - orkiestracja modułu edukacyjnego (Prompt 5.3).

Udostępnia tematy jako DTO, ocenia mini-quizy (sprawdzenie zrozumienia, NIE
samoocena stanu) i zapisuje postęp (first/last viewed, quiz_score). Zależy od
domeny (treść) i portu repozytorium; czas wstrzykiwany (`clock`).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import datetime

from application.dto.education import (
    EducationProgressDTO,
    EducationSectionDTO,
    EducationTopicDTO,
    QuizQuestionDTO,
)
from application.ports.repositories import IEducationRepository
from domain.education import EducationContent, EducationTopic


class EducationService:
    def __init__(
        self,
        content: EducationContent,
        repository: IEducationRepository,
        clock: Callable[[], datetime],
    ) -> None:
        self._content = content
        self._repository = repository
        self._clock = clock

    def get_topics(self) -> list[EducationTopicDTO]:
        return [self._to_dto(t) for t in self._content.topics]

    def get_topic(self, topic_id: str) -> EducationTopicDTO | None:
        try:
            return self._to_dto(self._content.topic_by_id(topic_id))
        except KeyError:
            return None

    def record_view(self, topic_id: str) -> EducationProgressDTO:
        """Odnotowuje obejrzenie tematu (first/last viewed)."""
        self._content.topic_by_id(topic_id)  # walidacja istnienia (KeyError)
        istniejacy = self._repository.get_progress(topic_id)
        teraz = self._clock()
        first = istniejacy.first_viewed_at if istniejacy else teraz
        progress = EducationProgressDTO(
            topic_id=topic_id,
            first_viewed_at=first,
            last_viewed_at=teraz,
            quiz_score=istniejacy.quiz_score if istniejacy else None,
        )
        self._repository.upsert_progress(progress)
        return progress

    def grade_quiz(self, topic_id: str, answers: Sequence[int]) -> int:
        """Liczy liczbę poprawnych odpowiedzi (deterministycznie)."""
        topic = self._content.topic_by_id(topic_id)
        if len(answers) != len(topic.quiz):
            raise ValueError(
                f"Oczekiwano {len(topic.quiz)} odpowiedzi, otrzymano {len(answers)}."
            )
        return sum(
            1 for odp, q in zip(answers, topic.quiz) if odp == q.correct_index
        )

    def submit_quiz(self, topic_id: str, answers: Sequence[int]) -> EducationProgressDTO:
        """Ocenia quiz i zapisuje wynik w postępie."""
        score = self.grade_quiz(topic_id, answers)
        istniejacy = self._repository.get_progress(topic_id)
        teraz = self._clock()
        first = istniejacy.first_viewed_at if istniejacy else teraz
        progress = EducationProgressDTO(
            topic_id=topic_id,
            first_viewed_at=first,
            last_viewed_at=teraz,
            quiz_score=score,
        )
        self._repository.upsert_progress(progress)
        return progress

    def get_progress(self, topic_id: str) -> EducationProgressDTO | None:
        return self._repository.get_progress(topic_id)

    @staticmethod
    def _to_dto(topic: EducationTopic) -> EducationTopicDTO:
        return EducationTopicDTO(
            id=topic.id,
            title=topic.title,
            sections=[
                EducationSectionDTO(heading=s.heading, body=s.body)
                for s in topic.sections
            ],
            key_points=list(topic.key_points),
            when_to_seek_help=topic.when_to_seek_help,
            quiz=[
                QuizQuestionDTO(
                    question=q.question,
                    options=list(q.options),
                    correct_index=q.correct_index,
                )
                for q in topic.quiz
            ],
        )
