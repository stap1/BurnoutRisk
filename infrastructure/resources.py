"""Rozwiązywanie ścieżek do danych statycznych (działa w dev i w bundlu PyInstaller).

W trybie spakowanym (--onedir) PyInstaller rozpakowuje dołączone dane do katalogu
wskazywanego przez `sys._MEIPASS`. W trybie deweloperskim dane leżą w `data/` w
korzeniu repozytorium. Ten helper ujednolica oba przypadki.
"""

from __future__ import annotations

import sys
from pathlib import Path


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        baza = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return baza / "data"
    # infrastructure/resources.py -> parents[1] = korzeń repozytorium
    return Path(__file__).resolve().parents[1] / "data"


def data_file(name: str) -> Path:
    return data_dir() / name
