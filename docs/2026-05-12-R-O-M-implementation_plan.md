# Projekt-Status & Konzept Phase 4

## 1. Status Quo: Korrektheit der finanzmathematischen Berechnungen
Nach der systematischen Abarbeitung der kritischen Audit-Befunde (K1-K7) und dem Refactoring der Engine (Build 0050-0066) befindet sich der Rente-O-Mat auf einem **sehr hohen, professionellen Niveau**.

**Aktueller Stand der Mathematik:**
*   **Steuern (Multi-Year):** Wir nutzen eine BMF-nahe Näherung für das zu versteuernde Einkommen (zvE), berücksichtigen Vorsorgeaufwendungen und berechnen die Einkommensteuer (inkl. Grundfreibetrag, Progressionszonen) dynamisch pro Jahr.
*   **Abgaben:** Soli, Kirchensteuer und die Abgeltungsteuer (inkl. Teilfreistellungen und Sparerpauschbetrag) sind vollständig in die Cashflow-Loop integriert.
*   **Rente (EP-Logik):** Die Hochrechnung der Entgeltpunkte basiert auf Durchschnittsentgelten. Der Beitragsverlust bei Frührente und die Abschläge (0,3% pro Monat) werden monatsgenau berechnet.
*   **Altersteilzeit (ATZ):** Die gesetzliche RV-Aufstockung auf 80% des Vollzeit-Bruttos (§ 3 AltTZG) ist integriert, wodurch die Rentenprojektion nach einer ATZ nun hochpräzise ist.
*   **Closed-Loop Vermögen:** Zinseszins, Inflation, Entnahmepläne und Reinvestitionen von Überschüssen interagieren nun schleifenfrei miteinander (behoben in Build 0063).

**Fazit:** Das Fundament ist "audit-ready". Die Berechnungen sind robust genug, um darauf nun komplexe, algorithmische Strategien aufzubauen.

---

## 2. Konzept: "Auto-Modus" für Asset-Entnahmen
Aktuell muss der Nutzer für jedes Asset manuell Start/Ende und Raten festlegen. Der Auto-Modus wandelt das System von einem reinen "Rechner" zu einem **"Berater"**.

### Logik
Wenn in einem Jahr das Einkommen den Bedarf unterschreitet (`Überschuss/Defizit < 0`), löst die Engine einen Entnahme-Event aus. Anstatt manueller Entnahmepläne greift ein Algorithmus auf die Assets zu, um das Defizit auf 0 auszugleichen.

### Strategien (Wählbar in der UI)
1.  **"Liquidität zuerst" (Wasserfall-Modus):**
    *   Reihenfolge: Cash-Reserve -> Tagesgeld -> Festgeld -> Aktien/ETFs (Volatil).
    *   *Sinn:* Verhindert den Zwangsverkauf von volatilen Assets (ETFs) in schlechten Marktphasen ("Sequence of Returns Risk").
2.  **"Steuer-Optimiert":**
    *   Algorithmus entnimmt gezielt so viel Kapital aus abgeltungsteuerpflichtigen Assets, dass der jährliche Sparer-Pauschbetrag (1.000 € / 2.000 €) exakt ausgenutzt wird (Steuerfreier Gewinn).
    *   Erst danach wird aus steuerfreien Assets (z.B. nach 12 Jahren Haltefrist bei bestimmten Versicherungen) oder verlustfreien Cash-Beständen entnommen.
3.  **"Proportional" (Rebalancing):**
    *   Entnahme erfolgt anteilig aus allen Assets, um die ursprüngliche Asset-Allokation (z.B. 70% Aktien / 30% Anleihen) konstant zu halten.

### Umsetzung
*   Ein neuer Toggle im Vermögens-Tab: `Entnahme-Strategie: [Manuell] | [Auto: Wasserfall] | [Auto: Steueroptimiert]`.
*   In `engine.py` wird eine neue Funktion `_process_auto_withdrawals(defizit, assets, strategie)` eingefügt, die das Defizit iterativ deckt.

---

## 3. Konzept: Sonderentnahmen (Einmalausgaben)
Für große, punktuelle Lebensereignisse (Weltreise, neues Dach, Autokauf, Schenkung an Kinder).

### Datenmodell & UI
*   Neuer Eingabebereich in der Sidebar analog zu "Befristete Ausgaben".
*   Felder: `Titel` (z.B. "Wohnmobil"), `Jahr` (z.B. 2038), `Betrag` (z.B. 60.000 €), `Inflationsgebunden` (Ja/Nein).
*   *Finanzierung:* Wahlweise "Aus dem Cashflow/Vermögen decken" oder "Über Kredit finanzieren" (erzeugt automatisch eine befristete Ausgabe für die Tilgung in den Folgejahren).

### Logik in der Engine
*   Im spezifizierten Jahr wird der Betrag massiv auf den `Bedarf` aufgeschlagen.
*   Dies erzeugt eine hohe Liquiditätsunterdeckung.
*   In Kombination mit dem **Auto-Modus** (siehe Konzept 2) verkauft die Engine automatisch die notwendigen Assets (z.B. das Tagesgeld-Konto leert sich, ggf. müssen ETFs angetastet werden), um die Weltreise zu finanzieren.

---

## 4. Konzept: Tab "Dein Briefing" (Reporting & PDF)
Ein neuer, 5. Tab, der als "Executive Summary" für den Nutzer dient. Ideal zum Ausdrucken, Mitnehmen zur Bank oder als Diskussionsgrundlage mit dem Partner.

### Aufbau (Kollabierbare Sektionen)
1.  **Management Summary:** Die 3 wichtigsten Kennzahlen (z.B. "Dein Vermögen reicht bis Alter 92", "Break-Even der Rente ist 2041", "Gesamtsteuersatz im Alter: 14%").
2.  **Dein Status Quo:** Die aktuelle Cashflow-Situation (Textuelle Zusammenfassung des Sankeys 1).
3.  **Die Timeline (Meilensteine):** Eine chronologische Liste der Events (z.B. "2029: Beginn ATZ (Aktiv)", "2032: Beginn ATZ (Passiv)", "2035: Renteneintritt mit 10,8% Abschlag").
4.  **Szenario-Parameter & Rechtliches:** Vollständige Transparenz. Auflistung aller getroffenen Annahmen (Inflation 2%, Gehaltsdynamik 1%) und Hinweis auf die genutzten Rechtsstände (z.B. "EStG Stand 2024", "RV-Beitragsbemessungsgrenze dynamisiert", "ATZ-Aufstockung nach § 3 AltTZG").
5.  **Beispielrechnung (Deep Dive):** Detaillierter Rechenweg für ein kritisches Jahr (z.B. das erste Rentenjahr), um die Mathematik nachvollziehbar zu machen (Brutto -> zvE -> Steuern -> Netto).

### PDF Export
Da Streamlit native HTML-zu-PDF Exporte schwer macht, verwenden wir die Bibliothek `fpdf2` (rein Python, keine Systemabhängigkeiten).
*   Wir bauen eine Klasse `BriefingPDFGenerator`, die die berechneten Daten (Sankeys als Bilder, Tabellen als Text) nimmt und ein sauberes, mehrseitiges PDF-Dokument rendert.
*   Am Ende des Tabs gibt es einen dicken Button: **"📄 Komplettes Briefing als PDF herunterladen"**.

---

## Offene Fragen zur Abstimmung
1. **Priorität:** Mit welchem Konzept (Auto-Modus, Sonderentnahmen oder Briefing-Tab) wollen wir als Erstes in die Implementierung starten?
2. **Auto-Modus:** Sollen wir mit der einfachen "Wasserfall"-Strategie (Liquide Mittel zuerst) starten und Steueroptimierung später als Premium-Feature hinzufügen?
