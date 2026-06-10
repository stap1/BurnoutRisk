"""Testy treści edukacyjnych i mini-quizów (Prompt 5.2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.education import QUIZ_PYTANIA_NA_TEMAT, EducationContent
from infrastructure.persistence.education_content_loader import load_education_content

EDU_PATH = Path(__file__).resolve().parents[2] / "data" / "education_content.json"

# Zakazane słownictwo (spec §9.3): nie diagnozuje, nie nazywa „wypalonym".
ZAKAZANE = ["jesteś wypalony", "masz wypalenie", "diagnozujemy", "twój etap to"]


@pytest.fixture(scope="module")
def tresc() -> EducationContent:
    return load_education_content()


def test_laduje_sie(tresc: EducationContent) -> None:
    assert isinstance(tresc, EducationContent)
    assert len(tresc.topics) >= 5


def test_unikalne_id_tematow(tresc: EducationContent) -> None:
    ids = [t.id for t in tresc.topics]
    assert len(ids) == len(set(ids))


def test_kazdy_temat_ma_5_pytan(tresc: EducationContent) -> None:
    for t in tresc.topics:
        assert len(t.quiz) == QUIZ_PYTANIA_NA_TEMAT


def test_quiz_ma_poprawny_indeks(tresc: EducationContent) -> None:
    for t in tresc.topics:
        for q in t.quiz:
            assert 0 <= q.correct_index < len(q.options)
            assert len(q.options) >= 2


def test_kazdy_temat_ma_kiedy_szukac_pomocy(tresc: EducationContent) -> None:
    for t in tresc.topics:
        assert t.when_to_seek_help.strip()


def test_kazdy_temat_ma_wazne_w_skrocie(tresc: EducationContent) -> None:
    for t in tresc.topics:
        assert t.key_points


def test_zastrzezenie_nie_diagnoza(tresc: EducationContent) -> None:
    assert "diagnoz" in tresc.disclaimer.lower()


def test_ton_bez_zakazanego_slownictwa(tresc: EducationContent) -> None:
    # Skanujemy całą treść pod kątem języka diagnozującego.
    fragmenty: list[str] = [tresc.disclaimer]
    for t in tresc.topics:
        fragmenty.append(t.title)
        fragmenty.append(t.when_to_seek_help)
        fragmenty.extend(t.key_points)
        for s in t.sections:
            fragmenty.extend([s.heading, s.body])
        for q in t.quiz:
            fragmenty.append(q.question)
            fragmenty.extend(q.options)
    polaczone = " ".join(fragmenty).lower()
    for zakaz in ZAKAZANE:
        assert zakaz not in polaczone, f"Zakazane słownictwo: {zakaz!r}"


def test_topic_by_id(tresc: EducationContent) -> None:
    pierwszy = tresc.topics[0]
    assert tresc.topic_by_id(pierwszy.id) is pierwszy
    with pytest.raises(KeyError):
        tresc.topic_by_id("nie-ma")


# --- walidacja błędnych danych ---


def test_quiz_o_zlej_liczbie_pytan_odrzucony() -> None:
    raw = {
        "wersja": "1.0",
        "zastrzezenie": "to nie diagnoza",
        "tematy": [
            {
                "id": "t1",
                "tytul": "T",
                "sekcje": [{"naglowek": "h", "tresc": "b"}],
                "wazne_w_skrocie": ["x"],
                "kiedy_szukac_pomocy": "y",
                "quiz": [
                    {"pytanie": "q", "odpowiedzi": ["a", "b"], "poprawna": 0}
                ],
            }
        ],
    }
    with pytest.raises(ValidationError):
        EducationContent.from_dict(raw)


def test_zly_indeks_poprawnej_odpowiedzi() -> None:
    raw = {
        "wersja": "1.0",
        "zastrzezenie": "to nie diagnoza",
        "tematy": [
            {
                "id": "t1",
                "tytul": "T",
                "sekcje": [{"naglowek": "h", "tresc": "b"}],
                "wazne_w_skrocie": ["x"],
                "kiedy_szukac_pomocy": "y",
                "quiz": [
                    {"pytanie": f"q{i}", "odpowiedzi": ["a", "b"], "poprawna": 9}
                    for i in range(5)
                ],
            }
        ],
    }
    with pytest.raises(ValidationError):
        EducationContent.from_dict(raw)
