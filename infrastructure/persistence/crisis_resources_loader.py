"""Loader zasobów wsparcia z JSON (Prompt 5.1) - granica I/O.

Brak pliku / niepoprawny JSON / pusta lista = błąd blokujący. Safety-net musi
działać; nie udajemy, że wsparcie jest dostępne, gdy danych nie ma (spec §12.6).
"""

from __future__ import annotations

import json
from pathlib import Path

from domain.safety import CrisisResources

DEFAULT_CRISIS_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "crisis_resources.json"
)


def load_crisis_resources(path: Path | str | None = None) -> CrisisResources:
    sciezka = Path(path) if path is not None else DEFAULT_CRISIS_PATH
    if not sciezka.is_file():
        raise FileNotFoundError(
            f"Brak pliku zasobów wsparcia (safety-net wymagany): {sciezka}"
        )
    try:
        raw = json.loads(sciezka.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Niepoprawny JSON w pliku zasobów wsparcia {sciezka}: {exc}"
        ) from exc
    return CrisisResources.from_dict(raw)
