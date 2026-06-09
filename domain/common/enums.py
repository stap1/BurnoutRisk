"""Enumy domenowe wspólne dla całej aplikacji.

Te typy są częścią rdzenia domeny - nie mają żadnego I/O i są używane przez
ScoringEngine, CoachPlanGenerator oraz DTO na granicach warstw.

Uwaga o słownictwie: pasma `RiskBand` są WEWNĘTRZNE (logika kolorów, progi
coachingu, trend). Słownictwo widoczne dla użytkownika jest miękkie i powstaje
w warstwie prezentacji - patrz spec §5.4 i §5.5.
"""

from __future__ import annotations

from enum import Enum


class RiskBand(str, Enum):
    """Wewnętrzne pasmo ryzyka wyliczane z wyniku (0-100).

    Granice pasm (spec §5.5): 0-24 / 25-49 / 50-69 / 70-100.
    Te same pasma stosują się analogicznie do wyniku obszaru (`S_obszar`).
    """

    LOW = "LOW"            # 0-24   - ton spokojny, wzmacniający
    MODERATE = "MODERATE"  # 25-49  - ton informujący
    HIGH = "HIGH"          # 50-69  - ton troskliwy, zachęcający do działania
    VERY_HIGH = "VERY_HIGH"  # 70-100 - troskliwy, wsparcie, BEZ języka alarmu


class AreaStatus(str, Enum):
    """Status oceny pojedynczego obszaru A-F (spec §3.2, §5).

    Obszar poniżej progu minimalnej liczby odpowiedzi nie jest oceniany
    (jego wynik to `None`, nie zero) i prezentowany jest neutralnie.
    """

    RATED = "RATED"                          # obszar oceniony (wystarczająco danych)
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"  # za mało odpowiedzi, wynik = None


class Goal(str, Enum):
    """Cel wybierany w wizardzie coachingu (spec §6.2).

    Steruje doborem mikro-działań z biblioteki. Wartości w języku projektu (PL).
    """

    ENERGIA = "ENERGIA"    # odbudowa zasobów, sen, regeneracja
    STRES = "STRES"        # redukcja obciążenia i napięcia
    GRANICE = "GRANICE"    # granice pracy/odpoczynku, dostępność
    RELACJE = "RELACJE"    # relacje, uznanie, wsparcie społeczne


class ExportFormat(str, Enum):
    """Format eksportu raportu (spec §10)."""

    CSV = "CSV"  # podstawowy
    PDF = "PDF"  # opcjonalny
