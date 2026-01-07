# SOAP Converter Service (Python 3.10)

**Autor:** Paweł Baczkowski (130150)

Usługa sieciowa SOAP zrealizowana w ramach projektu zaliczeniowego. System umożliwia:

* konwersję plików **XML → JSON**,
* automatyczne wykrywanie formatu danych wejściowych,
* walidację spójności strukturalnej między formatami XML i JSON.

---

## 🎯 Temat projektu

**#2 XML ➔ JSON** (zgodnie z `TOPICS.md`)

---

## 🛠️ Funkcjonalności (Operacje SOAP)

* **ConvertXtoY**
  Konwersja dokumentów XML do JSON z zachowaniem struktury węzłów.

* **DetectFormat**
  Automatyczna analiza danych wejściowych (Base64) w celu rozpoznania formatu (**XML** lub **JSON**).

* **ValidateConversion**
  Logiczne porównanie plików XML i JSON w celu weryfikacji poprawności procesu konwersji.

* **ListSupportedConversions**
  Pobranie listy wspieranych par formatów.

---

## 🚀 Instrukcja uruchomienia

### 1. Przygotowanie środowiska (venv)

```bash
# Utworzenie wirtualnego środowiska
python -m venv .venv

# Aktywacja środowiska
# Windows:
.\.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

# Instalacja zależności
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

### 2. Uruchomienie serwera SOAP

W pierwszym terminalu:

```bash
python service/server.py
```

Serwer publikuje kontrakt **WSDL** pod adresem:

```
http://127.0.0.1:8000/service?wsdl
```

---

### 3. Testowanie klientem CLI (Terminal 2)

Wszystkie test można wykonać z innymi plikami z katalogu fixtures. 

#### A. Konwersja i wykrywanie formatu (poprawne dane)

```bash
# Konwersja catalog.xml
python client/cli.py convert --in tests/fixtures/catalog.xml --from xml --to json

# Wykrywanie formatu
python client/cli.py detect --in tests/fixtures/catalog.xml
```

#### B. Testowanie obsługi błędów (niepoprawne dane)

Usługa została zaprojektowana tak, aby poprawnie obsługiwać wyjątki i błędy parsowania danych wejściowych.

```bash
# Próba konwersji zwykłego tekstu
python client/cli.py convert --in tests/fixtures/SimpleText.txt --from xml --to json

# Próba konwersji pliku z błędną składnią XML
python client/cli.py convert --in tests/fixtures/WrongSyntax.xml --from xml --to json
```

W obu przypadkach serwer powinien zwrócić odpowiedź z informacją o błędzie, a klient zapisać raport ze statusem `error`.

#### C. Walidacja poprawności konwersji

```bash
python client/cli.py validate --src tests/fixtures/catalog.xml --dst reports/result_convert_1.json --srcfmt xml --dstfmt json
```

---

## 🧪 Testy i raportowanie

Uruchomienie testów automatycznych:

```bash
pytest tests/test_service.py
```

Wyniki konwersji oraz raporty techniczne (zawierające statusy `success` / `error` oraz czasy operacji) zapisywane są w katalogu `reports/`.

---

## 📁 Struktura projektu

```
soap-converter/
├─ service/
│  ├─ server.py            # Serwer SOAP (Spyne)
│  └─ impl/
│     └─ conversions.py    # Logika konwersji
├─ client/
│  └─ cli.py               # Klient CLI (Zeep)
├─ tests/
│  ├─ test_service.py      # Testy pytest
│  └─ fixtures/            # Pliki testowe:
│     ├─ catalog.xml       # Poprawny XML
│     ├─ config.xml        # Poprawny XML
│     ├─ corrupted.xml     # XML z błędami
│     ├─ SimpleText.txt    # Zwykły tekst (test błędów)
│     └─ WrongSyntax.xml   # Błędna składnia XML
├─ reports/                # Wyniki i raporty JSON
├─ requirements.txt        # Zależności
└─ README.md               # Dokumentacja
```
