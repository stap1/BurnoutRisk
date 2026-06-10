# Code review — Burnout Risk Monitor (2026-06-10)

Przegląd kodu po ukończeniu MVP (Fazy 0–9). Tryb: `/code-review` na maksymalnym
poziomie (recall — priorytet: wyłapać każdy realny błąd).

## Zakres i metoda

- `git diff @{upstream}...HEAD` oraz `git diff HEAD` były **puste** (cała praca
  scommitowana i wypchnięta, `HEAD == origin/main`, drzewo czyste). Ostatni commit
  to wyłącznie README/audyt, dlatego przeglądowi poddano **rdzeń kodu aplikacji**
  napisany w Fazach 1–9.
- Zastosowano kąty: skan linia-po-linii, audyt usuniętego zachowania, tracer
  cross-file, pułapki językowe (Python), poprawność wrapperów, oraz kąty
  sprzątające (reuse / uproszczenia / wydajność / altitude).
- Każde znalezisko zweryfikowano, czytając dokładny kod (cytat linii).

Stan bazowy: **289 testów zielonych**, pokrycie domeny 92% (scoring/generator/
trend/results/enumy 100%). W warstwie bezpieczeństwa/scoringu/persystencji
(transakcje, AES-GCM, renormalizacja wag, envelope/PIN) nie znaleziono usterek.

## Znaleziska

| # | Plik:linia | Waga | Rodzaj | Status |
|---|---|---|---|---|
| 1 | `domain/coaching/plan.py:134` (+ `application/dto/coach.py:49`) | wysoka (crash) | poprawność | ✅ naprawione |
| 2 | `presentation/views/coach.py:154` | wysoka (utrata danych) | poprawność | ✅ naprawione |
| 3 | `presentation/views/pin.py:83` | średnia/niska | odporność | ✅ naprawione |
| 4 | `domain/survey/scoring.py` (`score`/`total_score`) | niska | wydajność | ✅ naprawione |
| 5 | `application/services/report_service.py` | niska | wydajność | ✅ naprawione |
| 6 | `application/services/report_service.py` / `survey_repository.py` | niska | determinizm | ✅ naprawione |

> Wszystkie naprawione w commicie poprawkowym; **301 testów zielonych** (12 nowych testów regresyjnych).

### 1. ZeroDivisionError w generatorze planu przy budżecie < 5 (crash)

**Mechanizm:** `CoachConfigDTO.daily_time_budget` miał ograniczenie tylko
`Field(ge=1)`. W `CoachPlanGenerator._rozloz_dzialania` dla budżetu < 5
`for_area_and_budget` zwraca pustą listę, a `lista[liczniki[obszar] % len(lista)]`
dzieli przez zero.

**Scenariusz:** `facade.create_coach_plan(CoachConfigDTO(..., daily_time_budget=3))`
→ `ZeroDivisionError`. UI oferuje tylko 5/10/15, ale publiczne API fasady
przyjmowało 1-4.

**Naprawa:** (a) DTO ograniczone do `{5, 10, 15}` (walidator); (b) generator
odporny — pomija obszary bez pasujących działań, a gdy żaden nie ma kandydatów,
zwraca pusty plan zamiast crashować.

### 2. Oznaczenie „ukończone" kasuje wcześniej ustawioną ocenę

**Mechanizm:** `_oznacz` wysyłał `rating=akcja.rating` (wartość z DTO z chwili
wczytania planu, nieaktualizowana po wyborze oceny), zamiast bieżącej wartości
z combobox.

**Scenariusz:** wybór oceny 4 (zapis do bazy) → zaznaczenie checkboxa „ukończone"
→ zapis `rating=None` (stare DTO) → utrata oceny.

**Naprawa:** ujednolicenie zapisu w jednej metodzie `_zapisz_akcje(akcja, combo,
done_var)` używanej przez checkbox i combobox; rating zawsze czytany z combobox.

### 3. `_wylacz` (PIN) nie łapie `KeyRecoveryNeeded`

**Mechanizm:** obsługiwany był tylko `WrongPinError`; przy uszkodzonej/brakującej
kopercie `disable_pin` rzuca `KeyRecoveryNeeded`, który wybijał obsługę zdarzenia
tkinter.

**Naprawa:** `_wylacz` łapie też `KeyRecoveryNeeded` i kieruje użytkownika do
ścieżki recovery (reset).

### 4. Podwójne liczenie wyniku obszarów w `ScoringEngine.score`

**Mechanizm:** `score()` wołało `area_scores()`, a następnie `total_score()`,
które ponownie liczyło `area_scores()` (i rekodowanie).

**Naprawa:** wydzielono `_area_scores_from_recoded` i `_total_from_area_map`;
`score()` rekoduje i liczy obszary raz, total liczony z gotowej mapy. Publiczne
`area_scores`/`total_score` bez zmian sygnatur.

### 5. Wielokrotne `get_history()` w raporcie

**Mechanizm:** `get_progress_report` pobierał historię osobno w `_session_trend`
i dwukrotnie w `_agency`/`_porownaj_ostatnie_sesje`.

**Naprawa:** historia pobierana raz i przekazywana do funkcji pomocniczych.

### 6. Brak deterministycznego tie-breakera w kolejności sesji

**Mechanizm:** `get_history` sortował tylko `started_at DESC`; przy identycznym
znaczniku porównanie dwóch ostatnich sesji mogło się odwrócić.

**Naprawa:** dodano wtórny klucz sortowania (`id DESC`) w zapytaniu, co czyni
kolejność deterministyczną.

## Wnioski

Brak usterek krytycznych dla bezpieczeństwa danych ani dla rdzenia scoringu.
Dwie realne usterki funkcjonalne (#1 crash, #2 utrata oceny) oraz jedna luka
odporności (#3) naprawione wraz z testami regresyjnymi; trzy poprawki
jakościowe (#4–#6) bez zmian zachowania widocznego dla użytkownika.

**Wynik po naprawach:** `pytest` 301 zielonych (1 skip środowiskowy tkinter),
pokrycie rdzenia domeny utrzymane na 100%.
