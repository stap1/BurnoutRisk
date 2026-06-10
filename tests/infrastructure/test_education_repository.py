"""Testy EducationService + SqliteEducationRepository (Prompt 5.3)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from application.services import EducationService
from infrastructure.persistence.database import init_database
from infrastructure.persistence.education_content_loader import load_education_content
from infrastructure.persistence.education_repository import SqliteEducationRepository

CZAS_1 = datetime(2026, 6, 10, 8, 0, 0)
CZAS_2 = datetime(2026, 6, 12, 9, 0, 0)


@pytest.fixture
def conn(tmp_path: Path):
    c = init_database(tmp_path / "baza.db")
    yield c
    c.close()


@pytest.fixture
def content():
    return load_education_content()


def _service(content, conn, czas) -> EducationService:
    return EducationService(content, SqliteEducationRepository(conn), clock=lambda: czas)


def test_get_topics_zwraca_dto(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    tematy = svc.get_topics()
    assert len(tematy) >= 5
    assert all(t.quiz for t in tematy)


def test_get_topic_po_id(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    jakis = content.topics[0].id
    assert svc.get_topic(jakis) is not None
    assert svc.get_topic("nie-ma") is None


def test_record_view_zapisuje_first_i_last(content, conn) -> None:
    tid = content.topics[0].id
    svc1 = _service(content, conn, CZAS_1)
    p1 = svc1.record_view(tid)
    assert p1.first_viewed_at == CZAS_1
    assert p1.last_viewed_at == CZAS_1
    assert p1.quiz_score is None

    # Ponowne obejrzenie pozniej: first bez zmian, last zaktualizowany.
    svc2 = _service(content, conn, CZAS_2)
    p2 = svc2.record_view(tid)
    assert p2.first_viewed_at == CZAS_1
    assert p2.last_viewed_at == CZAS_2


def test_grade_quiz_liczy_poprawne(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    temat = content.topics[0]
    poprawne = [q.correct_index for q in temat.quiz]
    assert svc.grade_quiz(temat.id, poprawne) == len(temat.quiz)

    # Wszystkie zle (przesuniecie indeksu): 0 punktow tylko jesli rozne.
    zle = [(q.correct_index + 1) % len(q.options) for q in temat.quiz]
    assert svc.grade_quiz(temat.id, zle) == 0


def test_grade_quiz_zla_liczba_odpowiedzi(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    tid = content.topics[0].id
    with pytest.raises(ValueError):
        svc.grade_quiz(tid, [0])


def test_submit_quiz_zapisuje_wynik(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    temat = content.topics[0]
    poprawne = [q.correct_index for q in temat.quiz]
    progress = svc.submit_quiz(temat.id, poprawne)
    assert progress.quiz_score == len(temat.quiz)

    # Odczyt przez repo potwierdza trwalosc.
    odczyt = svc.get_progress(temat.id)
    assert odczyt is not None
    assert odczyt.quiz_score == len(temat.quiz)


def test_submit_quiz_po_view_zachowuje_first_viewed(content, conn) -> None:
    temat = content.topics[0]
    _service(content, conn, CZAS_1).record_view(temat.id)
    p = _service(content, conn, CZAS_2).submit_quiz(
        temat.id, [q.correct_index for q in temat.quiz]
    )
    assert p.first_viewed_at == CZAS_1
    assert p.last_viewed_at == CZAS_2


def test_get_progress_brak_to_none(content, conn) -> None:
    svc = _service(content, conn, CZAS_1)
    assert svc.get_progress(content.topics[0].id) is None
