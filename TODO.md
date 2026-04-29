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

## ⏳ In Arbeit / Nächste Schritte
- [ ] **Modul 3.6: Persistenz (JSON Export/Import)**
    - [ ] Export der gesamten Session-Daten (Profil, Einnahmen, Ausgaben) als JSON-File
    - [ ] Import-Funktion zum Wiederherstellen von gespeicherten Szenarien

## 📅 Geplant (Spätere Sitzungen)
- [ ] **Modul 3.4: Erweiterte Steuer- & SV-Engine**
    - [ ] Präzise KV/PV Logik (KVdR vs. Freiwillig)
    - [ ] Abgeltungsteuer für Kapitalerträge
- [ ] **Szenarien-Vergleich**
    - [ ] Gegenüberstellung von Modellen (z.B. "Früher in Rente" vs. "ATZ")
