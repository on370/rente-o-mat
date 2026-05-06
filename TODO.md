# Rente-O-Mat Projekt-Status & TODO

## ✅ Erledigt
- [x] Grundstruktur der Streamlit App (Sidebar, Tabs)
- [x] Basis-Steuerlogik (EStG 2024, Progressionsvorbehalt)
- [x] Duale Sankey-Visualisierung mit intelligenter Defizit-Logik (Links)
- [x] Globaler Zeitstrahl-Slider (Start 2026)
- [x] Dynamische Einnahme-Engine (Hinzufügen/Löschen von Quellen)
- [x] **Refactoring: Modularisierung** (logic/engine.py, ui/sidebar.py, ui/charts.py)
- [x] **ATZ-Evolution:** Split in Aktiv- (A) und Passivphase (P) mit 50/50 Berechnung
- [x] **Plausibilitäts-Check:** ATZ-Berechnung relativ zum Rentenbeginn
- [x] **UI/UX Optimierung:** Native Sidebar-Expander, Phasen-Statusbanner
- [x] **Zeitliche Entwicklung:** Umstellung auf Stacked Bar Chart mit detaillierten Quellen
- [x] **Steuer-Analyse:** Optionale Anzeige der effektiven Steuerquote (%) im Trend-Chart
- [x] Git-Housekeeping: .gitignore und README.md angelegt
- [x] **Persistenz (JSON Export/Import)**: v2.0 mit Versionskontrolle
- [x] **Steuer-Engine v2:** Multi-Year Tarife, Soli, Kirchensteuer, Abgeltungsteuer
- [x] **SV-Engine v2:** Dynamische BBG, PV-Kinderstaffelung, bAV-Freibetrag
- [x] **Dynamisierung:** Getrennte Inflation für Ausgaben, GRV und bAV
- [x] **Vermögenskurve:** Neuer Tab mit kumulativer Kapitalentwicklung
- [x] **Transparenz vorzeitiger Renteneintritt (Abschläge)**
    - [x] Visualisierung des theoretischen vollen Rentenbetrags (67 Jahre) als Einkunft im Sankey und Trend-Chart
    - [x] Visualisierung des Renten-Abschlags als roten Abzug/Defizit-Posten
    - [x] Trend-Chart: Rentenabschlag als gestrichelten roten Balken *on top* gesetzt
    - [x] Sankey: Verbindung und Schrift für "Rentenabschlag" explizit rot gefärbt
- [x] **Steuersatz-Visualisierung**
    - [x] Sinnvolle Visualisierung des ansteigenden Steuersatzes im Zeitverlauf
- [x] **Erweiterte Rentenlogik & bAV Einmalzahlung**
    - [x] bAV Einmalzahlung (Kapitalauszahlung): Steuer (Fünftelregelung) und SV (120-Monate-Regel) integriert
    - [x] UX für Einmalzahlung: Alternative Eingabe, Fiktive Verrentung (Entnahmeplan) steuerfrei ins Sankey integriert

- [x] **Präzise Rentenprojektion (EP-Logik)**
    - [x] Durchschnittsentgelt zur Berechnung von EP-Sätzen integriert (45.358 €)
    - [x] EP-Zuwachs bis zum Rentenstart wird dynamisch hochgerechnet
    - [x] Beitragsverlust (fehlende EP) wird separat berechnet und visualisiert
    - [x] Info-Box mit Tooltips zur Erläuterung der Renten-Details ergänzt

## ⏳ In Arbeit / Nächste Schritte (Phase 3 & 4)
- [ ] **Befristete Ausgaben (Kredite/Unterhalt)**
    - [ ] UI-Komponente zum Hinzufügen von Ausgaben mit Enddatum
    - [ ] Engine-Logik zur zeitlichen Begrenzung von Ausgaben
- [x] **Break-Even-Analyse**
    - [x] Vergleich Frührente vs. Regelrente (kumulierte Summen)
    - [x] Neuer Strategie-Tab mit Break-Even-Visualisierung
- [ ] **Individuelle Vermögenswerte (Depot, Tagesgeld, etc.)**
    - [ ] Verwaltung mehrerer benannter Vermögenswerte unter "Finanzen Aktuell"
    - [ ] Individuelle Verzinsung pro Vermögenswert
    - [ ] Anbindung bAV-Einmalzahlung (siehe [Konzept](docs/konzept_bav_vermoegen.md))

## 📅 Geplant (Spätere Sitzungen)
- [ ] **100% Transparenz & Vertrauen**
    - [ ] **Prüf- und Audit-Modus:** Neuer Tab, in dem der Nutzer ein Jahr wählt und ein detailliertes, mathematisches Protokoll aller Rechenschritte als "Beweis" erhält.
    - [ ] **PDF-Report Export:** Vollumfänglicher Bericht mit Charts, Tabellen und Methodik/Rechtsgrundlagen-Anhang.
- [ ] **Szenarien-Vergleich**
    - [ ] Gegenüberstellung von Modellen (z.B. "Früher in Rente" vs. "ATZ")
- [ ] **Hinterbliebenenabsicherung** (Witwenrente)
- [ ] **PKV-Integration** (fixer Monatsbeitrag im Alter statt KVdR)
