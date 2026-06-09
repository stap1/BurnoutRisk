"""Entrypoint aplikacji Burnout Risk Monitor.

Uruchomienie: `python main.py`. W Fazie 0 jedynie buduje fasadę i kończy pracy -
okno tkinter dochodzi w Fazie 7.
"""

from __future__ import annotations

from composition_root import build_app_facade


def main() -> None:
    """Punkt startowy: zbuduj fasadę, a w przyszłości uruchom UI."""
    _facade = build_app_facade()
    # Faza 7: tutaj powstanie i uruchomi się główne okno tkinter (z motywem sv_ttk
    # i graceful fallback do ttk). Na razie sam montaż zależności.


if __name__ == "__main__":
    main()
