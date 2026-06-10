"""Testy eksportu CSV (Prompt 8.2)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from application.dto import AreaScoreDTO, SurveyResultDTO
from domain.common import AreaStatus, RiskBand
from infrastructure.export import export_session_to_csv


def _result() -> SurveyResultDTO:
    return SurveyResultDTO(
        session_id="s1",
        created_at=datetime(2026, 6, 10, 12, 0, 0),
        total_score=50.0,
        risk_band=RiskBand.HIGH,
        area_scores=[
            AreaScoreDTO(category_id="C", name="Obciążenie i stres", score=70.0,
                         status=AreaStatus.RATED, band=RiskBand.VERY_HIGH),
            AreaScoreDTO(category_id="A", name="Relacje i bezpieczeństwo psychospołeczne",
                         score=None, status=AreaStatus.INSUFFICIENT_DATA, band=None),
        ],
        top_areas=["C"],
        unrated_areas=["A"],
    )


def test_eksport_tworzy_plik_z_neutralnymi_naglowkami(tmp_path: Path) -> None:
    plik = tmp_path / "eksport.csv"
    export_session_to_csv(plik, _result())
    tresc = plik.read_text(encoding="utf-8-sig")
    assert "Obszar" in tresc
    assert "Wynik (0-100)" in tresc
    assert "Obciążenie i stres" in tresc
    # Neutralne slownictwo - bez terminow klinicznych.
    assert "diagnoz" not in tresc.lower()


def test_eksport_obejmuje_status_za_malo_danych(tmp_path: Path) -> None:
    plik = tmp_path / "eksport.csv"
    export_session_to_csv(plik, _result())
    tresc = plik.read_text(encoding="utf-8-sig")
    assert "za mało danych" in tresc


def test_eksport_total_score(tmp_path: Path) -> None:
    plik = tmp_path / "eksport.csv"
    export_session_to_csv(plik, _result())
    assert "50" in plik.read_text(encoding="utf-8-sig")
