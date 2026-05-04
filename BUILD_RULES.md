# Build-Regeln für RetireMe (Rente-O-Mat)

Diese Regeln sind verbindlich ("Eiserne Regeln") für die Weiterentwicklung des Projekts.

## 1. Build-Nummerierung
- Die Build-Nummer ist eine **4-stellige Hexadezimalzahl** (z.B. `0020`).
- Sie wird bei **jeder funktionalen oder visuellen Änderung** am Quellcode um genau `1` erhöht.
- Die Build-Nummer wird manuell in der Datei `config.py` als Konstante `BUILD_ID` gepflegt.

## 2. Versions-Format
- Das Format lautet: `X.Y [STAGE] (build HEX)`
- Beispiel: `0.1 [BETA] (build 0020)`
- `X.Y`: Major.Minor Version.
- `STAGE`: Entwicklungsstadium (z.B. [BETA], [DEV], [RC]).

## 3. Historie (Auszug)
- build 0020: Start der manuellen Build-Zählung, Integration Disclaimer-Dialog, Versionierung fixiert.
- build 0021: Umstellung auf statische Build-ID.
- build 0022: Dynamische Regelaltersgrenze (logic/rentenrecht.py) und Button-Zentrierung.
- build 0023: Fix Slider-Bug bei ATZ-Dauer (min==max).
