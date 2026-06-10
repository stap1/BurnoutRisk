"""Paleta kolorów - STONOWANA, NIE-semaforowa (spec §5.4).

Twardy zakaz alarmowej czerwieni. Wyższe ryzyko = spokojniejszy, cieplejszy, ale
nie alarmujący odcień. Te kolory służą wyłącznie subtelnemu różnicowaniu profilu
obszarów i tła - nigdy do straszenia.
"""

from __future__ import annotations

from domain.common import RiskBand

# Bazowe tło/teksty - neutralne, miękkie.
TLO = "#f4f3ef"
TEKST = "#2e2c29"
TEKST_PRZYGASZONY = "#6b675f"
AKCENT = "#5b7a8c"  # przygaszony błękit (linki, akcje)

# Obszary "za mało danych" - wyszarzone, neutralne (spec §5.3).
NEUTRALNY = "#cfccc4"

# Pasma ryzyka - stonowane odcienie. BRAK czerwieni alarmowej.
PASMA: dict[RiskBand, str] = {
    RiskBand.LOW: "#9bb8a4",        # spokojna szałwia
    RiskBand.MODERATE: "#d9c9a3",   # piaskowy
    RiskBand.HIGH: "#cda98c",       # przygaszona glina
    RiskBand.VERY_HIGH: "#b9a0a8",  # przygaszony wrzos (NIE czerwień)
}


def kolor_pasma(band: RiskBand | None) -> str:
    """Kolor dla pasma ryzyka; None (brak danych) → neutralny."""
    if band is None:
        return NEUTRALNY
    return PASMA.get(band, NEUTRALNY)
