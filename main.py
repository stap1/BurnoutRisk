"""Entrypoint aplikacji Burnout Risk Monitor.

Uruchomienie: `python main.py`. Buduje fasadę (composition root) i uruchamia
okno tkinter. Jeśli włączony jest tryb PIN - prosi o PIN przed startem; przy
problemie z kluczem proponuje recovery (reset), nigdy nie kończy cichym crashem.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from app_facade import AppFacade
from composition_root import PinRequiredError, build_app_facade, reset_app
from infrastructure.crypto import KeyRecoveryNeeded, WrongPinError
from presentation.app import BurnoutApp


def _odblokuj_pinem() -> AppFacade | None:
    """Pętla podawania PIN-u z opcją recovery. Zwraca fasadę lub None (rezygnacja)."""
    root = tk.Tk()
    root.withdraw()
    try:
        while True:
            pin = simpledialog.askstring(
                "PIN", "Podaj PIN, aby odblokować dane:", show="•", parent=root
            )
            if pin is None:
                return None  # użytkownik anulował
            try:
                return build_app_facade(pin=pin)
            except (WrongPinError, KeyRecoveryNeeded):
                reset = messagebox.askyesno(
                    "Nie udało się odblokować",
                    "Nieprawidłowy PIN lub uszkodzony klucz.\n\n"
                    "Czy zresetować aplikację? To nieodwracalnie usunie dane, ale "
                    "przywróci pełną używalność.",
                    parent=root,
                )
                if reset:
                    reset_app()
                    return build_app_facade()
    finally:
        root.destroy()


def main() -> None:
    try:
        facade = build_app_facade()
    except PinRequiredError:
        facade = _odblokuj_pinem()
        if facade is None:
            return  # rezygnacja z odblokowania

    app = BurnoutApp(facade)
    app.mainloop()


if __name__ == "__main__":
    main()
