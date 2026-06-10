"""TrendDetector - reaktywna detekcja utrzymującego się trendu (Prompt 4.3, §6.3).

Czyta serię check-inów (stres/sen/energia 0-10) i liczy **złożony wskaźnik
samopoczucia**. Kierunki ujednolicone: stres rośnie = gorzej, sen/energia rosną =
lepiej, więc stres jest odwracany. Wskaźnik: wyższy = lepiej.

Sugestia pojawia się tylko przy trendzie **utrzymującym się** (kilka kolejnych
spadków rolującej średniej, nie pojedynczy odczyt). Poniżej minimum danych - cicho,
bez straszenia "za mało danych". Progi są jawnymi, konfigurowalnymi stałymi (do
strojenia na realnych danych). Ton sugestii: miękki, nie-diagnostyczny.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

SKALA_MAX = 10

# Miękka, nie-diagnostyczna sugestia (spec §6.3). Prezentacja może ją opakować.
SOFT_SUGGESTION = (
    "Ostatnio bywało ciężej niż zwykle - może warto zajrzeć do kilku rzeczy, które "
    "pomagają. Jeśli taki stan się utrzymuje, rozważ kontakt ze specjalistą."
)


@dataclass(frozen=True)
class TrendConfig:
    """Jawne, konfigurowalne progi detekcji (do strojenia na danych testowych)."""

    rolling_window: int = 3       # ile check-inów uśrednia wskaźnik rolujący
    consecutive_declines: int = 2  # ile kolejnych spadków = trend (nie pojedynczy)
    min_decline: float = 0.5       # minimalny spadek rolującej średniej na krok (0-10)


class CheckinPoint(BaseModel):
    """Pojedynczy check-in jako wejście detektora (kolejność chronologiczna)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stress: int = Field(ge=0, le=SKALA_MAX)
    sleep: int = Field(ge=0, le=SKALA_MAX)
    energy: int = Field(ge=0, le=SKALA_MAX)


class TrendResult(BaseModel):
    """Wynik detekcji. `worsening` steruje pokazaniem miękkiej sugestii."""

    model_config = ConfigDict(frozen=True)

    enough_data: bool
    worsening: bool
    suggestion: str | None = None


class TrendDetector:
    def __init__(self, config: TrendConfig | None = None) -> None:
        self._cfg = config or TrendConfig()

    def wellbeing_index(self, checkin: CheckinPoint) -> float:
        """Złożony wskaźnik 0-10 (wyższy = lepiej); stres odwrócony."""
        return (checkin.sleep + checkin.energy + (SKALA_MAX - checkin.stress)) / 3

    def detect(self, checkins: Sequence[CheckinPoint]) -> TrendResult:
        cfg = self._cfg
        n = len(checkins)
        minimum = cfg.rolling_window + cfg.consecutive_declines

        if n < minimum:
            # Poniżej minimum danych - cicho, bez sugestii.
            return TrendResult(enough_data=False, worsening=False, suggestion=None)

        well = [self.wellbeing_index(c) for c in checkins]
        w = cfg.rolling_window
        rolling = [
            sum(well[i - w + 1 : i + 1]) / w for i in range(w - 1, n)
        ]
        diffs = [rolling[i] - rolling[i - 1] for i in range(1, len(rolling))]

        ostatnie = diffs[-cfg.consecutive_declines :]
        worsening = all(d <= -cfg.min_decline for d in ostatnie)

        return TrendResult(
            enough_data=True,
            worsening=worsening,
            suggestion=SOFT_SUGGESTION if worsening else None,
        )
