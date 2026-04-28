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
- [x] **Refactoring: Modularisierung** (Aufteilung in logic, ui, data)

## ⏳ In Arbeit / Nächste Schritte
- [ ] **UI/UX Optimierung**
    - [ ] Umbenennen von "Zentrale Parameter" zu "Profil" + Feld 'Name'
    - [ ] Sidebar-Abschnitte klappbar machen (Expander)
    - [ ] Phasen-Anzeige (Erwerb, ATZ, Ruhest.) direkt neben der Jahreszahl am Slider
    - [ ] Markierungen auf dem Slider-Track (Raute für Rente, Dreieck für ATZ) - *Technisch via Overlay oder Legende*
- [ ] **Modul 3.6: Persistenz (JSON Export/Import)**
    - [ ] Export der gesamten Session-Daten als JSON-File
    - [ ] Import-Funktion zum Wiederherstellen von Szenarien

## 📅 Geplant (Spätere Sitzungen)
- [ ] **Modul 3.4: Erweiterte Steuer- & SV-Engine**
    - [ ] Präzise KV/PV Logik (KVdR vs. Freiwillig)
    - [ ] Abgeltungsteuer für Kapitalerträge
- [ ] **Szenarien-Vergleich**
    - [ ] Side-by-side Vergleich von verschiedenen Renteneintrittsaltern
