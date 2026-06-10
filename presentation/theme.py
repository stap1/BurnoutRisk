"""Inicjalizacja motywu z graceful fallback (spec §1.1.2, §12.6).

Próbujemy nałożyć `sv_ttk` (kosmetyka). Brak biblioteki lub błąd NIGDY nie blokuje
startu - cicho wracamy do standardowego `ttk`. Motyw to wyłącznie warstwa wyglądu,
nie wpływa na logikę ani strukturę widoków.
"""

from __future__ import annotations

import tkinter as tk


def apply_theme(root: tk.Misc) -> bool:
    """Próbuje nałożyć sv_ttk. Zwraca True, jeśli się udało; False przy fallbacku."""
    try:
        import sv_ttk

        sv_ttk.set_theme("light")
        return True
    except Exception:
        # Graceful fallback do domyślnego ttk - aplikacja działa dalej.
        return False
