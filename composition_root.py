"""Composition root - jedyne miejsce wiązania konkretnych implementacji.

Ręczna iniekcja zależności (bez frameworka DI): tworzy repozytoria, serwisy
i crypto z infrastruktury, składa je w serwisy aplikacji i wstrzykuje do AppFacade.

To jest szkielet z Fazy 0 - wypełni się wiązaniami w kolejnych fazach.
"""

from __future__ import annotations

from app_facade import AppFacade


def build_app_facade() -> AppFacade:
    """Buduje gotową do użycia fasadę z wszystkimi zależnościami.

    W Fazie 0 zwraca pustą fasadę; wiązania (SQLite, crypto, keyring, serwisy)
    dochodzą w Fazach 2-8.
    """
    return AppFacade()
