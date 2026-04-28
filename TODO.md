# RetireMe Projekt-Status & TODO

## ✅ Erledigt
- [x] Grundstruktur der Streamlit App (Sidebar, Tabs)
- [x] Basis-Steuerlogik (EStG 2024, Progressionsvorbehalt)
- [x] Haushaltsbuch mit Renten-Anpassungsfaktoren
- [x] Duale Sankey-Visualisierung mit intelligenter Defizit-Logik
- [x] Globaler Zeitstrahl-Slider (Start 2026)
- [x] Dynamische Einnahme-Engine (Hinzufügen/Löschen von Quellen)
- [x] Automatisierte Phasen-Erkennung (Aktiv, ATZ, Rente)
- [x] Langfrist-Trend (Flächendiagramm Einkommen vs. Bedarf)
- [x] Vertikale Meilenstein-Marker im Trend-Chart inkl. Beschriftung

## ⏳ In Arbeit / Nächste Schritte
- [ ] **Modul 3.6: Persistenz (JSON Export/Import)**
    - [ ] Export der gesamten Session-Daten als JSON-File
    - [ ] Import-Funktion zum Wiederherstellen von Szenarien
- [ ] **Refactoring: Modularisierung**
    - [ ] Aufspaltung der `app.py` in logische Module (`logic/`, `ui/`, `data/`)

## 📅 Geplant (Spätere Sitzungen)
- [ ] **Modul 3.4: Erweiterte Steuer- & SV-Engine**
    - [ ] Präzise KV/PV Logik (KVdR vs. Freiwillig)
    - [ ] Abgeltungsteuer für Kapitalerträge
- [ ] **Szenarien-Vergleich**
    - [ ] Side-by-side Vergleich von verschiedenen Renteneintrittsaltern
