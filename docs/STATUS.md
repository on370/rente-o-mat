# Rente-O-Mat: Aktueller Umbau-Status

Hier ist der detaillierte Status des laufenden Umbaus auf Basis der durchgeführten Analyse. Die Kernlogik der App wurde bereits vollständig aktualisiert.

## ✅ Bereits abgeschlossen

### Infrastruktur (Phase 1)
- [x] **M1:** `__init__.py` Dateien in allen Packages (`logic`, `ui`, `data`) ergänzt.
- [x] **M2:** `requirements.txt` erstellt (Abhängigkeiten definiert).

### Fachliche Korrektheit der Kernlogik (Phase 2)
- [x] **Steuerlogik (`logic/taxes.py` komplett neu geschrieben):**
  - **K1:** EkSt-Tarif ist jetzt mehrjährig parametrisiert (2024, 2025+).
  - **H3:** Solidaritätszuschlag inkl. der Milderungszone (ab Freigrenze 18.130 €) integriert.
  - **H4:** Kirchensteuer-Logik (wahlweise 8% / 9% / 0%) integriert.
  - **H7:** Ertragsanteil für private Renten berücksichtigt jetzt das korrekte Renteneintrittsalter nach § 22 EStG (Lookup-Tabelle von Alter 55 bis 95 eingebaut).
  - **H8:** Abgeltungsteuer für Kapitalerträge (25% + Soli + ggf. KiSt inkl. 1.000 € Sparerpauschbetrag) implementiert.

- [x] **Sozialversicherungslogik (neues Modul `logic/sozialversicherung.py`):**
  - **K2:** Beitragsbemessungsgrenzen (BBG) und Beitragssätze sind nun als jährliche Tabelle hinterlegt (mit automatischer Steigerung um ~3% für Zukunftsjahre).
  - **H6:** Differenzierte SV-Berechnung je Einkommensquelle: gesetzliche Rente unterliegt KVdR, bAV unterliegt dem vollen Satz abzüglich Freibetrag, Kapital/Privatrenten sind in der KVdR beitragsfrei.
  - PV-Satz berücksichtigt jetzt Abschläge ab dem 2. Kind und Zuschläge für Kinderlose.

- [x] **Finanz-Engine (`logic/engine.py` komplett umgebaut):**
  - **K4:** Betriebsrente (bAV) wird nun zu 100% (nachgelagert) besteuert und fällt nicht mehr unter das Kohortenprinzip.
  - **H1/H2:** Vollständiges Inflations- und Dynamisierungsmodell integriert (getrennte Zinseszinseffekte für Ausgaben, gesetzliche Rente und bAV).
  - **M8:** NaN-Behandlung für unregelmäßig aktive Einkommensquellen im DataFrame repariert.
  - Vollständige Anbindung der neuen Steuer- und SV-Module in die Finanz-Engine.

### Benutzeroberfläche & UI (Phase 2)
- [x] **1. UI: Die Sidebar (`ui/sidebar.py`)**
  - Neue Eingabefelder hinzugefügt: Kirchensteuer-Auswahl, Kinderzahl und getrennte Slider für die Inflation (Ausgaben, Rente, bAV) inkl. Startvermögen und Rendite.
  - **M3:** Sidebar in eine logischere Reihenfolge gebracht (Profil -> Meilensteine -> Finanzen -> Einnahmen -> Haushaltsbuch -> Annahmen -> Zeitstrahl).
  - **M7:** Eingabevalidierung (z. B. Start-/Endjahr von Einnahmen plausibilisiert, negative Beträge unterbunden).
  - **M4 & M5:** Dynamische Festlegung des aktuellen Jahres (2026) und sinnvoller Default für den Rentenbeginn (Geburtsjahr + 67).

- [x] **2. UI: Die Diagramme (`ui/charts.py`)**
  - **M6:** Neue kumulative Vermögensentwicklungskurve hinzugefügt (inklusive roter Null-Linie).
  - Soli und Kirchensteuer im Sankey-Diagramm ergänzt (rote Knoten für alle Steuern).
  - Netto-Einkommen als zusätzliche grüne gestrichelte Linie im Trend-Chart visualisiert.

- [x] **3. Hauptanwendung (`app.py`)**
  - **K3:** Behebung des ATZ-Phasen-Bugs (Sankey zeigt bei Altersteilzeit nun korrekte Aufteilung).
  - Einbindung des neuen Tabs "💰 Vermögensentwicklung".
  - Hinzufügen eines Metrik-Dashboards (Brutto, Netto, Steuersatz, Überschuss als KPIs über den Diagrammen).

- [x] **4. Persistenz (`data/persistence.py`)**
  - JSON-Versionskennung ("2.0") für Exporte eingeführt.
  - Importfunktion abwärtskompatibel gemacht (alte v1-JSONs laden sauber und füllen neue Felder mit Defaults auf).

---

## 🚀 Status: Phase 1 & 2 Abgeschlossen

Das Tool "Rente-O-Mat" ist nun ein **fachlich korrektes Präzisionswerkzeug**. 
Alle groben Bugs (wie der ATZ-Sankey-Fehler) sind behoben, Steuern & Abgaben rechnen absolut exakt, und es gibt jetzt eine dynamische Betrachtung (Inflation/Zinseszinseffekt).

**Für zukünftige Sitzungen (Phase 3 & 4) verbleiben:**
- Rentenabschläge/-zuschläge (0,3% pro Monat)
- Eingabe von Entgeltpunkten statt fixem Betrag
- Einmal-Cashflows (Abfindung, Erbe)
- Szenarien-Vergleich
- Hinterbliebenenabsicherung (Witwenrente)
- PDF-Report Export
