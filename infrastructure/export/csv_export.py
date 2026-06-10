"""Eksport sesji do CSV (Prompt 8.2, spec §10.1).

Nagłówki i etykiety są NEUTRALNE (nazwy obszarów A-F, „Wynik (0-100)"), bez
terminów o klinicznym/stygmatyzującym brzmieniu. Plik zapisywany lokalnie; żadnej
wysyłki. UWAGA: to jedyne miejsce, gdzie dane opuszczają bazę w postaci jawnej -
ostrzeżenie i potwierdzenie egzekwuje warstwa wyżej (fasada/UI).
"""

from __future__ import annotations

import csv
from pathlib import Path

from application.dto import CoachPlanDTO, SurveyResultDTO
from domain.common import AreaStatus

STATUS_PL = {
    AreaStatus.RATED: "oceniony",
    AreaStatus.INSUFFICIENT_DATA: "za mało danych",
}


def export_session_to_csv(
    path: Path | str,
    result: SurveyResultDTO,
    plan: CoachPlanDTO | None = None,
) -> None:
    sciezka = Path(path)
    # utf-8-sig: poprawne polskie znaki po otwarciu w arkuszach (np. Excel).
    with sciezka.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)

        w.writerow(["Sesja"])
        w.writerow(["Data", result.created_at.isoformat() if result.created_at else ""])
        w.writerow([
            "Wynik ogólny (0-100)",
            "" if result.total_score is None else round(result.total_score),
        ])
        w.writerow([])

        w.writerow(["Obszar", "Wynik (0-100)", "Status"])
        for a in result.area_scores:
            w.writerow([
                a.name,
                "" if a.score is None else round(a.score),
                STATUS_PL.get(a.status, ""),
            ])

        if plan is not None and plan.actions:
            w.writerow([])
            w.writerow(["Plan - dzień", "Działanie", "Ukończono", "Ocena (0-5)"])
            for akcja in plan.actions:
                w.writerow([
                    akcja.scheduled_day,
                    akcja.description,
                    "tak" if akcja.completed_date else "nie",
                    "" if akcja.rating is None else akcja.rating,
                ])
