"""Testy definicji ankiety (Prompt 1.1).

Sprawdzamy strukturę i kompletność danych (`questions.json`) oraz walidację
encji domenowych. Test czyta plik przez stdlib `json` i buduje definicję czystą
metodą `SurveyDefinition.from_dict` - bez zależności od warstwy infrastruktury.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.survey import Category, Question, SurveyDefinition

QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"

# Oczekiwane stałe wg spec §3.1 / §4.2.
OCZEKIWANE_WAGI = {"A": 26, "B": 20, "C": 20, "D": 16, "E": 10, "F": 8}
OCZEKIWANE_LICZBY_PYTAN = {"A": 4, "B": 4, "C": 4, "D": 3, "E": 3, "F": 3}
PYTANIA_ODWRACANE = {"A4", "B3", "E1", "E2", "F1", "F2", "F3"}
PYTANIA_POMIJALNE = {"A1", "A2", "B4"}
WSZYSTKIE_ID = {
    f"{kat}{i}"
    for kat, n in OCZEKIWANE_LICZBY_PYTAN.items()
    for i in range(1, n + 1)
}


@pytest.fixture(scope="module")
def definicja() -> SurveyDefinition:
    raw = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return SurveyDefinition.from_dict(raw)


def test_wczytuje_sie_jako_survey_definition(definicja: SurveyDefinition) -> None:
    assert isinstance(definicja, SurveyDefinition)


def test_kompletnosc_21_pytan(definicja: SurveyDefinition) -> None:
    assert len(definicja.questions) == 21
    assert {q.id for q in definicja.questions} == WSZYSTKIE_ID


def test_szesc_kategorii(definicja: SurveyDefinition) -> None:
    assert {c.id for c in definicja.categories} == set(OCZEKIWANE_WAGI)


def test_sumy_wag_kategorii_rowne_100(definicja: SurveyDefinition) -> None:
    assert sum(c.weight for c in definicja.categories) == 100
    assert {c.id: c.weight for c in definicja.categories} == OCZEKIWANE_WAGI


def test_liczba_pytan_w_kategoriach(definicja: SurveyDefinition) -> None:
    for c in definicja.categories:
        assert len(c.question_ids) == OCZEKIWANE_LICZBY_PYTAN[c.id]


def test_pytania_odwracane(definicja: SurveyDefinition) -> None:
    odwracane = {q.id for q in definicja.questions if q.is_reversed}
    assert odwracane == PYTANIA_ODWRACANE


def test_pytania_pomijalne(definicja: SurveyDefinition) -> None:
    pomijalne = {q.id for q in definicja.questions if q.is_skippable}
    assert pomijalne == PYTANIA_POMIJALNE


def test_display_order_to_permutacja_1_do_21(definicja: SurveyDefinition) -> None:
    kolejnosci = sorted(q.display_order for q in definicja.questions)
    assert kolejnosci == list(range(1, 22))


def test_kolejnosc_lekkie_ciezkie_neutralne(definicja: SurveyDefinition) -> None:
    # spec §4.2: otwarcie F,E (lekkie) -> środek A,B (ciężkie) -> domknięcie C,D.
    bloki = [q.category for q in definicja.questions_in_display_order]
    # Bloki kategorii w kolejności wyświetlania, bez powtórzeń sąsiednich.
    sekwencja_blokow = [k for i, k in enumerate(bloki) if i == 0 or k != bloki[i - 1]]
    assert sekwencja_blokow == ["F", "E", "A", "B", "C", "D"]


def test_kazde_pytanie_ma_tresc_pl(definicja: SurveyDefinition) -> None:
    for q in definicja.questions:
        assert q.text.strip(), f"Puste pytanie {q.id}"


def test_tresci_pytan_sa_unikalne(definicja: SurveyDefinition) -> None:
    tresci = [q.text for q in definicja.questions]
    assert len(tresci) == len(set(tresci))


# --- Walidacja: błędne struktury muszą być odrzucone ---


def _poprawny_minimalny_raw() -> dict:
    return {
        "kategorie": [
            {"id": "A", "nazwa": "A", "waga": 60},
            {"id": "B", "nazwa": "B", "waga": 40},
        ],
        "pytania": [
            {"id": "A1", "kategoria": "A", "tresc": "t", "kolejnosc": 1},
            {"id": "B1", "kategoria": "B", "tresc": "t", "kolejnosc": 2},
        ],
    }


def test_from_dict_buduje_z_poprawnych_danych() -> None:
    d = SurveyDefinition.from_dict(_poprawny_minimalny_raw())
    assert len(d.questions) == 2
    assert d.category_by_id("A").question_ids == ("A1",)


def test_odrzuca_sume_wag_inna_niz_100() -> None:
    raw = _poprawny_minimalny_raw()
    raw["kategorie"][0]["waga"] = 50  # suma = 90
    with pytest.raises(ValidationError):
        SurveyDefinition.from_dict(raw)


def test_odrzuca_zduplikowane_id_pytania() -> None:
    raw = _poprawny_minimalny_raw()
    raw["pytania"][1]["id"] = "A1"
    raw["pytania"][1]["kategoria"] = "A"
    with pytest.raises(ValidationError):
        SurveyDefinition.from_dict(raw)


def test_odrzuca_pytanie_z_nieistniejaca_kategoria() -> None:
    raw = _poprawny_minimalny_raw()
    raw["pytania"][0]["kategoria"] = "Z"
    with pytest.raises(ValidationError):
        SurveyDefinition.from_dict(raw)


def test_odrzuca_dziurawe_display_order() -> None:
    raw = _poprawny_minimalny_raw()
    raw["pytania"][1]["kolejnosc"] = 5  # 1 i 5 zamiast 1 i 2
    with pytest.raises(ValidationError):
        SurveyDefinition.from_dict(raw)


def test_question_jest_niemutowalne() -> None:
    q = Question(id="A1", category="A", text="t", display_order=1)
    with pytest.raises(ValidationError):
        q.id = "A2"  # type: ignore[misc]


def test_category_jest_niemutowalne() -> None:
    c = Category(id="A", name="A", weight=100, question_ids=("A1",))
    with pytest.raises(ValidationError):
        c.weight = 50  # type: ignore[misc]
