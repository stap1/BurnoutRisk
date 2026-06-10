"""Testy zasobów wsparcia / safety-net (Prompt 5.1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from domain.safety import CrisisResources
from infrastructure.persistence.crisis_resources_loader import load_crisis_resources

CRISIS_PATH = Path(__file__).resolve().parents[2] / "data" / "crisis_resources.json"

# Numery zweryfikowane u źródła (policja.pl, gov.pl, 116sos.pl, liniawsparcia.pl, 116111.pl).
OCZEKIWANE_NUMERY = {"112", "116 123", "800 70 2222", "116 111"}


@pytest.fixture(scope="module")
def zasoby() -> CrisisResources:
    return load_crisis_resources()


def test_laduje_sie(zasoby: CrisisResources) -> None:
    assert isinstance(zasoby, CrisisResources)
    assert len(zasoby.resources) >= 1


def test_zawiera_zweryfikowane_numery(zasoby: CrisisResources) -> None:
    numery = {r.number for r in zasoby.resources}
    assert OCZEKIWANE_NUMERY <= numery


def test_kazdy_zasob_ma_komplet(zasoby: CrisisResources) -> None:
    for r in zasoby.resources:
        assert r.number.strip()
        assert r.name.strip()
        assert r.link.strip()
        assert r.link.startswith("https://")


def test_komunikat_ramowy_obecny(zasoby: CrisisResources) -> None:
    assert zasoby.framing_message.strip()


def test_data_weryfikacji_obecna(zasoby: CrisisResources) -> None:
    # Reguła okresowej re-weryfikacji (spec §8.2) - data musi istnieć.
    assert zasoby.verified_at


def test_brak_sztywnych_godzin_w_opisie(zasoby: CrisisResources) -> None:
    # §8.2: nie podajemy sztywnych godzin (np. "24h", "8:00-20:00") w treści,
    # odsyłamy do strony organizacji.
    import re

    wzorzec = re.compile(r"\b\d{1,2}[:.]\d{2}\b|\b24\s*h\b|\b24/7\b", re.IGNORECASE)
    for r in zasoby.resources:
        assert not wzorzec.search(r.description), f"Sztywne godziny w opisie {r.number}"


# --- błąd blokujący gdy brak danych (safety-net MUSI działać) ---


def test_brak_pliku_to_blad_blokujacy(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_crisis_resources(tmp_path / "nie_ma.json")


def test_pusta_lista_odrzucona() -> None:
    raw = {"wersja": "1.0", "zweryfikowano": "2026-06-10", "komunikat": "x", "zasoby": []}
    with pytest.raises(ValidationError):
        CrisisResources.from_dict(raw)


def test_niepelny_zasob_odrzucony() -> None:
    raw = {
        "wersja": "1.0",
        "zweryfikowano": "2026-06-10",
        "komunikat": "x",
        "zasoby": [{"numer": "", "nazwa": "X", "opis": "y", "link": "https://x"}],
    }
    with pytest.raises(ValidationError):
        CrisisResources.from_dict(raw)
