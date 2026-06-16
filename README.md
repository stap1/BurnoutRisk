# Burnout Risk Monitor

> Lokalne, offline-first narzędzie **edukacyjne** do oceny ryzyka wypalenia zawodowego, ze szczególnym uwzględnieniem środowiska IT.

![Status](https://img.shields.io/badge/status-MVP%20uko%C5%84czone-brightgreen)
![Etap](https://img.shields.io/badge/etap-Fazy%200--9%20uko%C5%84czone-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Tests](https://img.shields.io/badge/pytest-289%20zielonych-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Aplikacja desktopowa w Pythonie, która na podstawie ankiety psychometrycznej (21 pytań, 6 obszarów) buduje **profil ryzyka wypalenia**, oferuje moduł edukacyjny oraz deterministyczny plan wsparcia (coaching). Wszystkie dane pozostają **wyłącznie lokalnie** na urządzeniu użytkownika.

> [!IMPORTANT]
> **To nie jest narzędzie diagnostyczne ani medyczne.** Aplikacja ma charakter wyłącznie edukacyjny i informacyjny. Nie stawia rozpoznań, nie zastępuje kontaktu ze specjalistą. Jeśli mierzysz się z trudnym stanem, skontaktuj się z osobą lub instytucją oferującą profesjonalne wsparcie.

---

## Spis treści

- [O projekcie](#o-projekcie)
- [Kluczowe założenia](#kluczowe-założenia)
- [Stack technologiczny](#stack-technologiczny)
- [Architektura](#architektura)
- [Struktura repozytorium](#struktura-repozytorium)
- [Uruchomienie środowiska deweloperskiego](#uruchomienie-środowiska-deweloperskiego)
- [Testy](#testy)
- [Prywatność i bezpieczeństwo danych](#prywatność-i-bezpieczeństwo-danych)
- [Licencja](#licencja)

---

## O projekcie

Projekt powstaje w ramach przedmiotu **„Problemy społeczne i zawodowe informatyki"** (Projekt P1, Menedżerska Akademia Nauk Stosowanych w Warszawie). Temat zajęć - równowaga między życiem zawodowym a prywatnym - został w porozumieniu z prowadzącym rozszerzony na szersze i bardziej aktualne zagadnienie: **ryzyko wypalenia zawodowego w branży IT**, które dotyka coraz szerszych kręgów osób pracujących w tym sektorze.

Celem jest narzędzie, które:

- pozwala użytkownikowi spojrzeć na własną sytuację zawodową przez pryzmat sześciu obszarów ryzyka,
- robi to w sposób **bezpieczny psychologicznie** (bez straszenia, bez etykietowania, bez efektu „wyroku"),
- edukuje o wypaleniu w oparciu o rzetelne źródła,
- proponuje konkretne, drobne kroki wsparcia,
- i przez cały czas zapewnia dostęp do realnych zasobów pomocowych.

## Kluczowe założenia

Projekt jest prowadzony wokół jednej nadrzędnej zasady - **Primum Non Nocere** (po pierwsze nie szkodzić). Z niej wynikają konkretne decyzje, które odróżniają to narzędzie od typowego „kwestionariusza online":

- **Profil zamiast werdyktu.** Wynik prezentowany jest jako profil sześciu obszarów (gdzie są zasoby, gdzie napięcie), a nie jako jedna alarmująca liczba. Paleta stonowana, język informujący - nie straszący.
- **Miękkie lądowanie w ankiecie.** Pytania o trudne sytuacje (np. nękanie) można pominąć; ich kolejność jest tak ułożona, by nie zostawiać użytkownika z najcięższym pytaniem na końcu.
- **Ścieżka specjalna dla bezpieczeństwa.** Wysoki wynik w obszarze relacji/przemocy nie uruchamia „mikro-ćwiczeń", lecz kieruje do realnych kroków (HR, wsparcie) - bez bagatelizowania poważnego problemu.
- **Zawsze dostępny safety-net.** Zweryfikowane, ogólnopolskie zasoby wsparcia są dostępne z każdego ekranu.
- **Suwerenność danych.** Wszystko lokalnie, bez chmury i telemetrii; użytkownik w pełni kontroluje retencję i może usunąć dane w dowolnym momencie.

Szczegółowe uzasadnienia tych decyzji znajdują się w [dokumencie projektowym](../ProjectFiles/burnout_monitor_spec_v3_1.md).

## Stack technologiczny

| Warstwa | Technologia |
|---|---|
| Język / runtime | Python 3.11+ |
| GUI | tkinter + ttk (+ opcjonalny motyw `sv_ttk`) |
| Wykresy | matplotlib (osadzony w tkinter) |
| Baza danych | SQLite (`sqlite3`, tryb WAL) |
| Szyfrowanie | AES-GCM (pola wrażliwe) + Argon2id (KDF dla PIN) |
| Magazyn kluczy | `keyring` (systemowy menedżer poświadczeń) |
| Walidacja | Pydantic v2 |
| Testy | pytest |
| Pakowanie | PyInstaller (`--onedir`) |

Dobór narzędzi jest świadomie konserwatywny i zgodny z wytycznymi przedmiotu (czysty Python, biblioteka standardowa tam, gdzie to możliwe).

## Architektura

Projekt stosuje **ścisłe warstwowanie** z regułą zależności skierowaną do wewnątrz. Warstwa prezentacji (UI) jest traktowana jako cienka, **wymienialna** powłoka - logika domenowa nie wie, czy nad nią jest tkinter, czy w przyszłości inny interfejs.

```
┌─────────────────────────────────────────────┐
│  PRESENTATION (tkinter)                       │
│  Ekrany, formatowanie do wyświetlenia         │
└───────────────────────┬───────────────────────┘
                        │ przez fasadę (AppFacade)
┌───────────────────────▼───────────────────────┐
│  APPLICATION (serwisy + porty + DTO)           │
└───────────────────────┬───────────────────────┘
              używa      │      ▲ implementuje porty
┌──────────────────────▼──┐  ┌──┴────────────────┐
│  DOMAIN (czysta logika)  │  │  INFRASTRUCTURE   │
│  scoring, coaching,      │  │  SQLite, crypto,  │
│  reguły - ZERO I/O       │  │  keyring, eksport │
└──────────────────────────┘  └───────────────────┘
```

Zasada nadrzędna: **w warstwie domenowej nie ma żadnego I/O** (baza, pliki, sieć, czas - wstrzykiwane). Dzięki temu rdzeń (silnik scoringu, generator planu) jest w 100% testowalny w izolacji.

## Struktura repozytorium

> Warstwy w pełni zaimplementowane (Fazy 0-9).

Repozytorium aplikacji znajduje się w katalogu `BurnoutRiskApp/`. Dokumenty planistyczne (specyfikacja, `todo.md`) oraz `CLAUDE.md` leżą **o poziom wyżej**, w katalogu roboczym projektu - poza samym repozytorium kodu.

```
SoftwareHouse/BurnoutRiskApp/        # katalog roboczy (workspace)
├── CLAUDE.md                        # wytyczne operacyjne dla pracy z Claude Code
├── ProjectFiles/
│   ├── burnout_monitor_spec_v3_1.md # pełna specyfikacja techniczna (v3.1)
│   └── todo.md                      # plan wykonawczy (TDD, prompt po promptcie)
└── BurnoutRiskApp/                  # <-- REPOZYTORIUM APLIKACJI (git)
    ├── domain/              # czysta logika (zero I/O) - na razie typy wspólne i enumy
    │   ├── common/          # RiskBand, AreaStatus, Goal, ExportFormat
    │   ├── survey/          # (Faza 1) encje ankiety, ScoringEngine
    │   ├── coaching/        # (Faza 4) CoachPlanGenerator, TrendDetector
    │   └── education/       # (Faza 5) encje treści
    ├── application/         # (Faza 2+) serwisy, porty (ABC), DTO
    ├── infrastructure/      # (Faza 3+) repozytoria SQLite, crypto, keyring, eksport
    ├── presentation/        # (Faza 7) ekrany tkinter
    ├── data/                # dane statyczne JSON (pytania, treści, zasoby) - dodawane w Fazach 1/5
    ├── tests/               # testy odzwierciedlające warstwy
    │   ├── domain/
    │   ├── application/
    │   ├── infrastructure/
    │   └── smoke/
    ├── composition_root.py  # wiązanie zależności (szkielet)
    ├── app_facade.py        # fasada dla warstwy prezentacji (szkielet)
    ├── main.py              # entrypoint (szkielet)
    ├── pyproject.toml       # zależności + konfiguracja pytest
    ├── LICENSE.txt
    └── README.md
```

## Uruchomienie

Wymagania: **Python 3.11+**.

```bash
# 1. Sklonuj repozytorium i wejdź do katalogu aplikacji
git clone <adres-repozytorium>
cd BurnoutRiskApp

# 2. (zalecane) środowisko wirtualne
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# 3. Zależności deweloperskie
pip install -e ".[dev]"

# 4. Testy (bramka - powinny przejść na zielono)
pytest

# 5. Uruchomienie aplikacji
python main.py
```

### Pakowanie (plik wykonywalny)

```bash
pyinstaller BurnoutRiskMonitor.spec      # tryb --onedir
# wynik: dist/BurnoutRiskMonitor/BurnoutRiskMonitor.exe (+ dołączone data/*.json)
```

## Testy

Projekt prowadzony jest metodą **TDD** (test-first). Zielony wynik `pytest` jest bramką wymaganą przed przejściem do kolejnej fazy.

```bash
pytest                 # cały zestaw
pytest tests/domain    # tylko warstwa domenowa (rdzeń logiki)
pytest -k <wzorzec>    # pojedynczy test po nazwie
```

Struktura katalogu `tests/` odzwierciedla warstwy architektury. Najgęstsze pokrycie ma (i będzie miała) domena - zwłaszcza silnik scoringu.

## Prywatność i bezpieczeństwo danych

Aplikacja przetwarza dane dotyczące dobrostanu, które należą do szczególnej kategorii danych (zdrowie). Z tego powodu:

- **wszystko działa lokalnie** - brak komunikacji sieciowej, chmury i telemetrii,
- aplikacja domyślnie działa **anonimowo** (bez imienia i danych identyfikujących),
- wrażliwe pola tekstowe (notatki) są **szyfrowane** (AES-GCM); klucz przechowuje systemowy menedżer poświadczeń,
- opcjonalny **PIN** dodaje realną warstwę ochrony (Argon2id + envelope encryption), wraz ze ścieżką awaryjną (recovery) na wypadek jego utraty,
- użytkownik ma **pełną kontrolę nad retencją** - dane są przechowywane bezterminowo, dopóki sam ich nie usunie (kasowanie pojedynczych sesji lub pełny reset),
- **eksport danych** (CSV) to jedyne miejsce, w którym dane opuszczają bazę w postaci jawnej (niezaszyfrowanej) - dlatego przed zapisem aplikacja pokazuje **wyraźne ostrzeżenie i wymaga potwierdzenia**; plik trafia wyłącznie lokalnie, na ścieżkę wybraną przez użytkownika.

Szczegóły modelu bezpieczeństwa: [specyfikacja, sekcja 2](../ProjectFiles/burnout_monitor_spec_v3_1.md).

## Licencja

Projekt udostępniany na licencji **MIT**. Pełny tekst: [`LICENSE.txt`](./LICENSE.txt).

---

<sub>Projekt akademicki. Narzędzie edukacyjne, nie diagnostyczne.</sub>
