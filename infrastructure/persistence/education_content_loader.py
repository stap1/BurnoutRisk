"""Loader treści edukacyjnych z JSON (Prompt 5.2) - granica I/O."""

from __future__ import annotations

import json
from pathlib import Path

from domain.education import EducationContent
from infrastructure.resources import data_file

DEFAULT_EDUCATION_PATH = data_file("education_content.json")


def load_education_content(path: Path | str | None = None) -> EducationContent:
    sciezka = Path(path) if path is not None else DEFAULT_EDUCATION_PATH
    if not sciezka.is_file():
        raise FileNotFoundError(f"Nie znaleziono pliku treści edukacyjnych: {sciezka}")
    try:
        raw = json.loads(sciezka.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Niepoprawny JSON w treści edukacyjnej {sciezka}: {exc}") from exc
    return EducationContent.from_dict(raw)
