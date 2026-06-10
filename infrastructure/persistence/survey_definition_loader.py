"""Loader definicji ankiety z pliku JSON (Prompt 1.1).

To jedyne miejsce z I/O dla definicji ankiety - czyta plik z dysku i przekazuje
surowy słownik do czystej walidacji domenowej (`SurveyDefinition.from_dict`).
Dzięki temu domena pozostaje wolna od operacji plikowych.
"""

from __future__ import annotations

import json
from pathlib import Path

from domain.survey import SurveyDefinition

# data/questions.json względem korzenia repozytorium (ten plik leży w
# infrastructure/persistence/, więc cofamy się o dwa poziomy).
DEFAULT_QUESTIONS_PATH = Path(__file__).resolve().parents[2] / "data" / "questions.json"


def load_survey_definition(path: Path | str | None = None) -> SurveyDefinition:
    """Wczytuje i waliduje definicję ankiety.

    Brak pliku lub niepoprawny JSON kończy się czytelnym wyjątkiem (dane statyczne
    są wymagane do startu) - nigdy cichy, częściowy stan.
    """
    sciezka = Path(path) if path is not None else DEFAULT_QUESTIONS_PATH
    if not sciezka.is_file():
        raise FileNotFoundError(f"Nie znaleziono pliku definicji ankiety: {sciezka}")

    try:
        raw = json.loads(sciezka.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Niepoprawny JSON w pliku ankiety {sciezka}: {exc}") from exc

    return SurveyDefinition.from_dict(raw)
