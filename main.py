"""Entrypoint aplikacji Burnout Risk Monitor.

Uruchomienie: `python main.py`. Buduje fasadę (composition root) i uruchamia
okno tkinter (z motywem sv_ttk i graceful fallback do ttk).
"""

from __future__ import annotations

from composition_root import build_app_facade
from presentation.app import BurnoutApp


def main() -> None:
    facade = build_app_facade()
    app = BurnoutApp(facade)
    app.mainloop()


if __name__ == "__main__":
    main()
