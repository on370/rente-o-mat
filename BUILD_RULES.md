# Build-Regeln und Historie für RetireMe (Rente-O-Mat)

Diese Regeln und die lückenlose Historie sind verbindlich ("Eiserne Regeln") für die Weiterentwicklung des Projekts. Sie dienen der Nachvollziehbarkeit aller Entwicklungsschritte.

---

## 1. Build-Nummerierung und Regeln

*   **Hexadezimale Zählung:** Die Build-Nummer ist eine **4-stellige Hexadezimalzahl** (z.B. `0020`, `008F`, `009A`).
*   **Inkrementierung:** Bei **jeder funktionalen oder visuellen Änderung** am Quellcode wird die Build-Nummer um genau `1` (in HEX) erhöht.
*   **Zentrales Register:** Die Build-Nummer wird ausschließlich in `config.py` als Konstante `BUILD_ID` gepflegt. Hardcodierte Build-Nummern in Kommentaren anderer Dateien (z.B. `app.py`) sind unzulässig, um Synchronisationsfehler zu vermeiden.
*   **Versions-Format:** `X.Y [STAGE] (build HEX)` (z.B. `0.1 [BETA] (build 009B)`).

---

## 2. Vollständige Build-Historie (inklusive Anomalien)

Da in der Vergangenheit durch Prototyping, bulk commits und decimal slips Abweichungen entstanden sind, dokumentiert diese Tabelle alle Übergänge lückenlos und erklärt historische Anomalien:

| Build (HEX) | Typ / Status | Zugehörige Commits / Änderungen | Details & Erklärung der Anomalien |
| :--- | :--- | :--- | :--- |
| **`0020`** | Initial | Welcome Screen, Disclaimer Dialog, Versionierung | Start der manuellen Build-Zählung. |
| **`0021`** | Regulär | Umstellung auf statische Build-ID in `config.py` | Erste Fixierung der Build-ID im Code. |
| **`0022`** | Regulär | Dynamische Regelaltersgrenze und Button-Zentrierung | Anpassungen in `logic/rentenrecht.py` und UI. |
| **`0023`** | Regulär | Fix Slider-Bug bei ATZ-Dauer (min == max) | Fehlerbehebung in der Sidebar. |
| **`0024`** | Regulär | Rentenpunkte-Berechnung, Euro-Beträge, PDF-Planung | Vorbereitung für detaillierte Berechnungen. |
| **`0038`** | **Anomalie** | BAV und Assets Layout, Steuern/SV-Kernlogik | **Sprung `0024` -> `0038` (+20 Dez / +14 Hex):** Entstanden durch massives Offline-Prototyping und anschließenden Bulk-Commit. |
| **`003A`** | **Anomalie** | Rentenanpassung, Deprecated Warnings, Netto-Fix | **Sprung `0038` -> `003A` (+2 Hex):** Zwischenschritt `0039` wurde im Git-Log übersprungen. |
| **`003D`** | **Anomalie** | Kosmetik und Layout-Feinschliff | **Sprung `003A` -> `003D` (+3 Hex):** Zwischenschritte `003B` und `003C` wurden übersprungen. |
| **`0041`** | **Anomalie** | Slider-Verlagerung unter das Sankey-Diagramm | **Sprung `003D` -> `0041` (+4 Hex):** Zwischenschritte `003E`, `003F` und `0040` übersprungen. |
| **`0056`** | **Anomalie** | Sidebar Polishing, Export-Hilfe, Doku-Verschiebung | **Sprung `0041` -> `0056` (+21 Dez / +15 Hex):** Großer Sprung durch Offline-Refactoring der Dokumentation und Testskripte. |
| **`0060`** | Regulär | ATZ Datumsformatierung & Bugfixes | Fehlerbehebung bei den Datumsangaben. |
| **`0065`** | **Anomalie** | Widget Policy Fix (ATZ Dauer) | **Sprung `0060` -> `0065` (+5 Hex):** Zwischenschritte übersprungen. |
| **`0073`** | **Anomalie** | Legenden-basierte Meilensteine mit Symbolen | **Sprung `0065` -> `0073` (+14 Dez / +0E Hex):** Großer Chart-Umbau. |
| **`0076`** | Regulär | Warnings unterdrückt, PDF-Export Feinschliff | Stabilisierung des PDF-Exports. |
| **`0081`** | **Anomalie** | Fix Kaleido-Abhängigkeit & Doku-Update | **Sprung `0076` -> `0081` (+11 Dez / +0B Hex):** Mehrere kleinere visuelle Anpassungen in einem Schritt gebündelt. |
| **`0084`** | Regulär | Global Rerun Fix für Haushaltsbuch-Reset | Fehlerbehebung in der Session-State-Verwaltung. |
| **`0089`** | Regulär | Iterationen an der Diagrammdarstellung & Zwei-Achsen-Charts | Interne Entwicklungsversion. |
| **`0090`** | **Decimal Slip** | Diagramm-Finetuning, wählbare Dateinamen | **Sprung `0089` -> `0090` (+7 Hex):** Hier passierte ein Fehler – statt hexadezimal weiterzuzählen (nach `0089` kommt `008A`), wurde dezimal auf `90` erhöht. Dies übersprang 6 Hex-Stufen (`008A` bis `008F`). |
| **`0091`** | Regulär | Robuster Select Slider mit typsicherem State-Mapping | Letzter dokumentierter Build vor einer Serie von Iterationen. |
| **`0091` bis `009A`** | **Anomalie** | Siehe Liste unten (9 Iterationen ohne Inkrement) | **Stuck at `0091`:** Die Build-Nummer verharrte über 9 Iterationen hinweg fälschlicherweise auf `0091`, da der AI-Agent vergaß, `config.py` anzupassen. |
| **`009B`** | Korrektur | Behebung der Buildnummern-Verstummung | Rechnerischer Ausgleich der 9 vergessenen Iterationen seit `0091` (`0091` + 9 = `009A` + 1 = `009B`). |
| **`009C`** | Regulär | Behebung des `StreamlitValueAssignmentNotAllowedError` beim Importieren | Einführung eines dynamischen Keys für den `file_uploader`, um den Widget-Zustand sicher zurückzusetzen. |
| **`009D`** | Regulär | Hierarchisches Simulation-Sankey-Routing & Definitionen-Fix | Gruppenweises Aggregieren und Routen der Kategorien im Simulations-Sankey-Diagramm, Behebung der Namensauflösung im Details-Tab und Behebung des Scope-Fehlers bei den Inputs in der Sidebar. |
| **`009E`** | Regulär | Abwärtskompatibilität beim Profil-Import behoben | Behebung des `AttributeError` bei Alt-Profilen durch dynamisches Migrieren der flachen `ausgaben_input`-Datenstruktur in die neue hierarchische `haushaltsbuch_kategorien`-Struktur. |
| **`009F`** | Regulär | Kompakteres Budget-Layout & Kollabierbarkeit | Platzsparende Verlegung des Einstellungs-Zahnrads (⚙️) direkt neben den Kategorienamen sowie Einführung einer kollabierbaren Steuerung für Sammelkategorien über Session-State. |

---

### Die 9 vergessenen Iterationen während Build `0091` (Stuck-Phase):
Während die Buildnummer auf `0091` festklebte, wurden folgende 9 funktionale/visuelle Iterationen durchgeführt, die nun in `009B`/`009C` zusammengeführt sind:
1. **Iter. 1 (Turn 1):** Dreigeteilte Jahresbalken im Trend-Chart angepasst (Zerpflückung/Lücken behoben).
2. **Iter. 2 (Turn 2):** Abstände zwischen zusammengehörigen Jahresbalken deutlich verschmalert.
3. **Iter. 3 (Turn 3):** Meilenstein-Markierungen horizontal an den tatsächlichen Rasterstrichen ausgerichtet.
4. **Iter. 4 (Turn 4):** Einführung von geteilten Jahresübergängen (`2027(01)` und `2027(02-12)`) auf dem zeitlichen Sankey-Slider.
5. **Iter. 5 (Turn 5):** Behebung des Streamlit `ValueError: 2027 is not in iterable` bei der Slider-Interaktion.
6. **Iter. 6 (Turn 6):** Korrektur der Slider-Beschriftung für geteilte Jahre und Legenden-Punkte.
7. **Iter. 7 (Turn 7):** Vereinheitlichung der Legenden-Darstellung über alle (geteilten und ungeteilten) Jahre hinweg.
8. **Iter. 8 (Turn 8):** Persistenz-Fix (Speichern und Laden von Rentenbeginn-Monat, Richtigstellung Geburtsjahr 1966 -> Default 2033).
9. **Iter. 9 (Turn 9):** UX-Optimierung (automatisches Ausblenden des Import-Buttons und der Datei nach Upload, Umbenennung in "Export").
