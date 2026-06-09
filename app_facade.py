"""AppFacade - jedyny punkt styku warstwy prezentacji z resztą systemu.

Wystawia metody odpowiadające przypadkom użycia (spec §1.2.2), przyjmuje i zwraca
DTO (Pydantic). Encje domenowe NIE wyciekają do prezentacji.

To jest szkielet z Fazy 0 - sygnatury wypełnią się implementacją w kolejnych
fazach (serwisy są wstrzykiwane przez composition_root).
"""

from __future__ import annotations


class AppFacade:
    """Fasada aplikacji. Zależności wstrzykiwane w composition root (bez frameworka DI)."""

    def __init__(self) -> None:
        # Serwisy/porty zostaną wstrzyknięte w kolejnych fazach (patrz composition_root.py).
        ...

    # Metody przypadków użycia (sygnatury wg spec §1.2.2) dochodzą w Fazach 2-8:
    #   start_new_survey, submit_survey, get_history, get_session_detail,
    #   create_coach_plan, submit_checkin, get_progress, get_education_topics,
    #   export_last_session, wipe_all_data.
