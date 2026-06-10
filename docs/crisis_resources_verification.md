# Log weryfikacji zasobów wsparcia (safety-net)

Zgodnie ze spec §8.2 i §8.3 numery wsparcia są **okresowo re-weryfikowane** u
źródła (nie z pamięci). Poniżej ślad audytowy ostatniej weryfikacji przed
oddaniem projektu. Pole `app_meta.crisis_resources_verified_at` (zasilane z
`data/crisis_resources.json` → `zweryfikowano`) musi zgadzać się z najnowszym
wpisem w tej tabeli.

## Re-weryfikacja: 2026-06-10

| Numer | Organizacja | Charakter | Źródła potwierdzające |
|---|---|---|---|
| 112 | Numer alarmowy (ogólnoeuropejski) | całodobowy | `gov.pl` (portal „Numer alarmowy 112") |
| 116 123 | Instytut Psychologii Zdrowia PTP | bezpłatny, całodobowy 7/7 | `gov.pl`, `policja.pl`, `116sos.pl`, `psychologia.edu.pl` |
| 800 70 2222 | Fundacja ITAKA — „Centrum Wsparcia" | bezpłatny, całodobowy 7/7 (aktywne w 2026) | `liniawsparcia.pl`, `itaka.org.pl`, `gov.pl` |
| 116 111 | Fundacja Dajemy Dzieciom Siłę | bezpłatny, całodobowy 7/7 | `116111.pl`, `fdds.pl`, `gov.pl` |

**Wynik:** wszystkie numery, przypisania organizacyjne i opisy w
`data/crisis_resources.json` aktualne i poprawne — bez zmian.

## Zasady (przypomnienie)

- W treści aplikacji **nie podajemy sztywnych godzin** — odsyłamy do strony
  organizacji (godziny bywają rozbieżne między źródłami).
- 800 70 2222 jest finansowane w ramach programu rządowego o określonym
  horyzoncie — wymaga szczególnej uwagi przy kolejnych re-weryfikacjach.
- Przy każdej kolejnej re-weryfikacji: dopisać nową sekcję z datą powyżej i
  zaktualizować `zweryfikowano` w `data/crisis_resources.json`.
