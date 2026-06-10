"""Główne okno aplikacji - nawigacja, motyw, safety-net, alert keyring (Prompt 7.1).

Cienka powłoka nad `AppFacade`. Trzyma kontener ekranów (ramek) i przełącza je
przez `show_view`. Safety-net jest dostępny z KAŻDEGO ekranu (stopka + menu, §8.1).
Przy niebezpiecznym backendzie keyring pokazuje uczciwe ostrzeżenie (§12.6).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app_facade import AppFacade
from presentation import palette
from presentation.theme import apply_theme
from presentation.views.base import BaseView
from presentation.widgets.safety_net import SafetyNetDialog

OSTRZEZENIE_KEYRING = (
    "Uwaga: Twój system nie udostępnia bezpiecznego magazynu poświadczeń. "
    "Szyfrowanie lokalne może nie być w pełni skuteczne."
)


class BurnoutApp(tk.Tk):
    def __init__(self, facade: AppFacade) -> None:
        super().__init__()
        self.facade = facade
        self.title("Burnout Risk Monitor - narzędzie edukacyjne")
        self.geometry("900x680")
        self.minsize(720, 560)

        self.theme_applied = apply_theme(self)
        self._zbuduj_menu()

        # Uczciwe ostrzeżenie o słabej ochronie (nie udajemy ochrony, której nie ma).
        if not facade.is_keyring_safe():
            baner = ttk.Label(
                self,
                text=OSTRZEZENIE_KEYRING,
                background=palette.NEUTRALNY,
                padding=8,
                wraplength=860,
            )
            baner.pack(fill="x")

        self._kontener = ttk.Frame(self)
        self._kontener.pack(fill="both", expand=True)

        self._stopka()

        self._views: dict[str, BaseView] = {}
        self._zbuduj_views()

    # --- nawigacja ---

    def register_view(self, name: str, view: BaseView) -> None:
        self._views[name] = view
        view.place(in_=self._kontener, x=0, y=0, relwidth=1, relheight=1)

    def show_view(self, name: str) -> None:
        view = self._views[name]
        view.tkraise()
        view.on_show()

    def _zbuduj_views(self) -> None:
        # Ekrany 7.2-7.3. Wynik (7.4) i kolejne dochodzą później - do tego czasu
        # "wynik" wskazuje na zaślepkę.
        from presentation.views.coach import CoachView
        from presentation.views.education import EducationView
        from presentation.views.pin import PinView
        from presentation.views.progress import ProgressView
        from presentation.views.result import ResultView
        from presentation.views.survey import SurveyView
        from presentation.views.welcome import WelcomeView

        self.register_view("start", WelcomeView(self._kontener, self))
        self.register_view("ankieta", SurveyView(self._kontener, self))
        self.register_view("wynik", ResultView(self._kontener, self))
        self.register_view("coaching", CoachView(self._kontener, self))
        self.register_view("edukacja", EducationView(self._kontener, self))
        self.register_view("postep", ProgressView(self._kontener, self))
        self.register_view("pin", PinView(self._kontener, self))
        self.show_view("start")

    # --- safety-net (zawsze dostępny) ---

    def open_safety_net(self) -> SafetyNetDialog:
        return SafetyNetDialog(self, self.facade.get_safety_net())

    def _stopka(self) -> None:
        stopka = ttk.Frame(self, padding=(12, 6))
        stopka.pack(fill="x", side="bottom")
        ttk.Button(
            stopka,
            text="Potrzebuję wsparcia",
            command=self.open_safety_net,
        ).pack(side="right")
        ttk.Label(
            stopka,
            text="Narzędzie edukacyjne - nie zastępuje diagnozy ani kontaktu ze specjalistą.",
            foreground=palette.TEKST_PRZYGASZONY,
        ).pack(side="left")

    def _zbuduj_menu(self) -> None:
        menubar = tk.Menu(self)
        ustawienia = tk.Menu(menubar, tearoff=0)
        ustawienia.add_command(
            label="PIN i prywatność", command=lambda: self.show_view("pin")
        )
        menubar.add_cascade(label="Ustawienia", menu=ustawienia)
        widok = tk.Menu(menubar, tearoff=0)
        widok.add_command(label="Mój postęp", command=lambda: self.show_view("postep"))
        menubar.add_cascade(label="Postęp", menu=widok)
        pomoc = tk.Menu(menubar, tearoff=0)
        pomoc.add_command(label="Wsparcie (safety-net)", command=self.open_safety_net)
        menubar.add_cascade(label="Pomoc", menu=pomoc)
        self.config(menu=menubar)
