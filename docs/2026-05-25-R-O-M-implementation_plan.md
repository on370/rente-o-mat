# Rente-O-Mat: Implementierungsplan (25. Mai 2026)

## Zielsetzung
Behebung aller im Audit (`AUDIT_REPORT_V2.md`) identifizierten Fehler und architektonischen Schwachstellen. Besonderer Fokus liegt auf der **Korrektur der kritischen Berechnungsfehler in der Einkommensteuerlogik (Tarif 2025)**, um eine verlässliche und mathematisch einwandfreie Finanzplanung für v1.0 zu gewährleisten.

---

## 🔴 Phase 1: Kritische Berechnungsfehler (P0 - Blocker für Release)
*Diese Punkte verfälschen die Kernberechnungen und müssen als erstes gelöst werden.*

### 1. EkSt-Tarifparameter 2025 korrigieren (C1)
**Datei:** `logic/taxes.py`
- **Aufgabe:** Aktualisierung des Dictionaries `TARIF_PARAMETER[2025]` gemäß dem geltenden Steuerfortentwicklungsgesetz.
- **Korrekturen:**
  - `zone3_ende`: 68480 (bisher 66760)
  - `zone3_a`: 176.64 (bisher 181.19)
  - `zone3_c`: 1015.13 (bisher 991.21)
  - `zone4_abzug`: 10911.92 (bisher 10636.31)
  - `zone5_abzug`: 19246.67 (bisher 18971.06)
- **Beibehalten:** `grundfreibetrag` (12096), `zone2_ende` (17443), `zone2_a` (932.30), `zone2_b` (1400.0).

### 2. EkSt-Tarif 2024 Fix für höhere Einkommen (C3)
**Datei:** `logic/taxes.py`
- **Aufgabe:** Die Tarifparameter für 2024 führen ab 30.000 € zvE zu systematisch zu niedrigen Steuern. 
- **Maßnahme:** Den 2024-Tarif (`TARIF_PARAMETER[2024]`) anhand des offiziellen § 32a EStG 2024 prüfen. Insbesondere die Abzugsbeträge der Zonen 4 und 5 (`zone4_abzug`, `zone5_abzug`) sowie die `zone3_a`/`zone3_b` Koeffizienten neu berechnen und anpassen.

### 3. Solidaritätszuschlag jahresabhängig machen (C2, H3)
**Datei:** `logic/taxes.py`
- **Aufgabe:** `SOLI_FREIGRENZE_SINGLE` darf keine statische Konstante (`18130`) mehr sein.
- **Maßnahme:** Die Signatur von `berechne_soli(steuer_ekst, splitting=False)` um den Parameter `jahr` (Default `2026`) erweitern.
- **Logik:**
  - Für `jahr <= 2024`: Freigrenze = 18.130 €
  - Für `jahr >= 2025`: Freigrenze = 19.950 €

---

## 🟠 Phase 2: Hohe Priorität (Wichtige fachliche Anpassungen)
*Verhindern systematische Abweichungen in langfristigen Projektionen.*

### 1. Gesetzliche Rundung bei der EkSt (H2)
**Datei:** `logic/taxes.py`
- **Aufgabe:** Umsetzung von § 32a Abs. 1 S. 2 EStG (Abrunden auf volle Euro).
- **Maßnahme:** 
  - In `berechne_einkommensteuer`: Das übergebene `zve` direkt am Anfang abrunden (`math.floor(zve)`).
  - Das finale Steuerergebnis (`steuer`) ebenfalls abrunden (`math.floor(steuer)`), bevor es zurückgegeben wird.

### 2. Konstanten auf Stand 2025 aktualisieren (H4, H5)
**Datei:** `config.py`
- **Aufgabe:** Aktualisierung veralteter 2024er Konstanten.
- **Maßnahme:** 
  - `RENTENWERT_AKTUELL` auf `40.79` setzen (Juli 2025).
  - `DURCHSCHNITTSENTGELT_AKTUELL` aktualisieren (z.B. auf den vorläufigen Wert 2025, ca. 50.400 €, genauer Wert recherchieren).
  - Optional/Zusätzlich: In `logic/rentenrecht.py` das Durchschnittsentgelt analog zur Beitragsbemessungsgrenze (BBG) dynamisieren, damit die EP-Rechnung auch für 2030+ realistisch bleibt.

### 3. Vorsorgeaufwendungen im Rentenbezug (H1)
**Dateien:** `logic/sozialversicherung.py` & `logic/engine.py`
- **Aufgabe:** Die Funktion `berechne_vorsorgeaufwendungen_steuerlich` liefert in der Phase "Rente" bisher hartcodiert `0.0` zurück.
- **Maßnahme:** Die KVdR- und PV-Beiträge in der Funktion korrekt berechnen und zurückgeben. Die Logik in `engine.py` (die bisher manuell `sv * 12` übergibt) entsprechend anpassen, um Code-Duplikation oder logische Konflikte zu vermeiden.

---

## 🟡 Phase 3: Mittlere Priorität (UX & Logik-Details)
*Verfeinern das Nutzererlebnis und beheben Randgruppen-Fehler.*

### 1. EP-Zuwachs in der Infobox korrigieren (M1)
**Datei:** `ui/sidebar.py`
- **Aufgabe:** Die Infobox berechnet den Rentenpunkte-Zuwachs naiv (`jahre_bis_beginn * ep_pro_jahr`). Bei aktiver ATZ (nur 80% des normalen EP-Zuwachses) zeigt sie folglich zu hohe Werte an.
- **Maßnahme:** Die Logik aus der Engine in die Sidebar übernehmen (Berücksichtigung von `atz_simulieren` und `atz_dauer`).

### 2. Break-Even-Berechnung monatsgenau / unterjährig machen (M5)
**Datei:** `logic/engine.py` (`calculate_break_even_data`)
- **Aufgabe:** Der Break-Even iteriert aktuell nur in ganzen Jahren (`for j in range(2026, 2100)`).
- **Maßnahme:** Für das exakte Übergangsjahr (Rentenbeginn z.B. 2032,5) die monatelange Auszahlung (z.B. nur 6 Monate Rente) berücksichtigen, um die kumulierte Summe und somit den Schnittpunkt der Graphen hochpräzise zu ermitteln.

### 3. bAV Einmalzahlung (SV-Freibetrag 120-Monate) (M3)
**Datei:** `logic/sozialversicherung.py`
- **Aufgabe:** Bei der 120-Monats-Verteilung der bAV-Einmalzahlung sicherstellen, dass der gesetzliche SV-Freibetrag korrekt abgezogen wird. Besonders wichtig: Keine doppelte Gewährung des Freibetrags, wenn gleichzeitig eine reguläre laufende bAV bezogen wird.

### 4. Sparerpauschbetrag konsistent abziehen (M6)
**Datei:** `logic/engine.py` & `logic/taxes.py`
- **Aufgabe:** Der Sparerpauschbetrag (1.000 €) darf pro Jahr nur **einmal** abgezogen werden.
- **Maßnahme:** Kapitalerträge aus manuell erfassten "Entnahmeplänen" und automatisch generierten Gewinnen aus der globalen Asset-Simulation aufsummieren und zentral besteuern.

---

## ⚪ Phase 4: Code-Qualität & Testing (P3)
*Langfristige Wartbarkeit sicherstellen.*

### 1. Unit-Test Suite aufsetzen (L1)
**Ordner:** `tests/`
- **Aufgabe:** Umwandlung des Auditskripts (`testing/audit_comprehensive.py`) in echte `pytest` Unit-Tests (`test_taxes.py`, `test_sv.py`, `test_rentenrecht.py`).

### 2. Tote Code-Pfade entfernen (L3)
**Datei:** `logic/pdf_export.py`
- **Aufgabe:** Entfernen der unbenutzten Variable `income_sources` und der dazugehörigen Code-Zeilen am Ende der Datei (Bug-Fix Rest).

### 3. Einheitliche Dynamisierungs-Skalierung (L2)
**Datei:** `logic/engine.py`
- **Aufgabe:** Die `gehalts_dynamik` wird momentan manuell durch 100 geteilt.
- **Maßnahme:** Prozent-Parameter einheitlich innerhalb der Hilfsfunktion `_dynamisiere_betrag` behandeln.
