"""Testy enumów domenowych (Prompt 0.2)."""

from __future__ import annotations

from domain.common import AreaStatus, ExportFormat, Goal, RiskBand


def test_risk_band_ma_cztery_pasma() -> None:
    assert {b.name for b in RiskBand} == {"LOW", "MODERATE", "HIGH", "VERY_HIGH"}


def test_area_status_ma_dwa_stany() -> None:
    assert {s.name for s in AreaStatus} == {"RATED", "INSUFFICIENT_DATA"}


def test_goal_pokrywa_cele_wizarda() -> None:
    # Cele coachingu wg spec §6.2: energia / stres / granice / relacje.
    assert {g.name for g in Goal} == {"ENERGIA", "STRES", "GRANICE", "RELACJE"}


def test_export_format_csv_i_pdf() -> None:
    assert {f.name for f in ExportFormat} == {"CSV", "PDF"}


def test_enumy_sa_str_serializowalne() -> None:
    # Dziedziczą po str => wygodne na granicach DTO i w zapisie do bazy.
    assert RiskBand.LOW == "LOW"
    assert AreaStatus.RATED.value == "RATED"
    assert Goal.STRES == "STRES"
    assert ExportFormat.CSV == "CSV"
