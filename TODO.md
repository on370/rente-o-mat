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

## ⏳ In Arbeit / Nächste Schritte (Phase 3 & 4)
- [ ] **Erweiterte Rentenlogik**
    - [ ] Rentenabschläge/-zuschläge (0,3% pro Monat)
    - [ ] Eingabe von Entgeltpunkten statt fixem Betrag
    - [ ] Einmal-Cashflows (Abfindung, Erbe)
- [ ] **Szenarien-Vergleich**
    - [ ] Gegenüberstellung von Modellen (z.B. "Früher in Rente" vs. "ATZ")
- [ ] **Hinterbliebenenabsicherung** (Witwenrente)
- [ ] **PDF-Report Export**
- [ ] **PKV-Integration** (fixer Monatsbeitrag im Alter statt KVdR)
