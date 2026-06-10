"""Loader biblioteki mikro-działań z JSON (Prompt 4.1) - granica I/O."""

from __future__ import annotations

import json
from pathlib import Path

from domain.coaching import CoachActionLibrary
from infrastructure.resources import data_file

DEFAULT_ACTIONS_PATH = data_file("coach_actions.json")


def load_coach_actions(path: Path | str | None = None) -> CoachActionLibrary:
    sciezka = Path(path) if path is not None else DEFAULT_ACTIONS_PATH
    if not sciezka.is_file():
        raise FileNotFoundError(f"Nie znaleziono pliku działań: {sciezka}")
    try:
        raw = json.loads(sciezka.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Niepoprawny JSON w pliku działań {sciezka}: {exc}") from exc
    return CoachActionLibrary.from_dict(raw)
