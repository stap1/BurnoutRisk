"""Wykresy trendu (matplotlib) ze stonowaną paletą (Prompt 8.1, spec §6.3.1 pkt 4).

Buduje figurę z trendem wyniku sesji i złożonego wskaźnika check-inów. Paleta
kojąca, nie-alarmowa (bez czerwieni). Sama figura nie pokazuje trendu „nago" -
ProgressView dokłada warstwę sprawczości i następny krok.
"""

from __future__ import annotations

from matplotlib.figure import Figure

from application.dto import ProgressReportDTO
from presentation import palette

LINIA = palette.AKCENT
LINIA_DRUGA = "#8c9a7b"  # przygaszona oliwka


def build_progress_figure(report: ProgressReportDTO) -> Figure:
    fig = Figure(figsize=(7.2, 4.4), dpi=100, facecolor=palette.TLO)

    osie = fig.subplots(2, 1)
    _rysuj(
        osie[0], report.session_trend,
        tytul="Wynik ogólny w czasie", kolor=LINIA,
    )
    _rysuj(
        osie[1], report.checkin_trend,
        tytul="Samopoczucie (check-iny)", kolor=LINIA_DRUGA,
    )
    fig.tight_layout()
    return fig


def _rysuj(ax, punkty, *, tytul: str, kolor: str) -> None:  # noqa: ANN001
    ax.set_facecolor(palette.TLO)
    ax.set_title(tytul, fontsize=10, color=palette.TEKST)
    ax.tick_params(colors=palette.TEKST_PRZYGASZONY, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(palette.NEUTRALNY)

    if not punkty:
        ax.text(
            0.5, 0.5, "Za mało danych, by pokazać wykres",
            ha="center", va="center", transform=ax.transAxes,
            color=palette.TEKST_PRZYGASZONY, fontsize=9,
        )
        ax.set_xticks([])
        ax.set_yticks([])
        return

    wartosci = [p.value for p in punkty]
    ax.plot(
        range(len(wartosci)), wartosci,
        marker="o", color=kolor, linewidth=2, markersize=4,
    )
    ax.set_xticks(range(len(punkty)))
    ax.set_xticklabels([p.label for p in punkty], rotation=30, ha="right")
    ax.grid(True, color=palette.NEUTRALNY, linewidth=0.5, alpha=0.6)
