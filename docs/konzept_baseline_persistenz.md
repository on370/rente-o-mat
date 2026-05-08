# Konzept: Baseline-Persistenz und Time-Drift-Korrektur

## 1. Das Problem
Finanzplanung ist ein dynamischer Prozess. Ein 2026 erstelltes Profil enthält Momentaufnahmen (z.B. Vermögen, Rentenpunkte). Wird dieses Profil 2028 erneut geladen, ist die "damalige Zukunft" (2026-2028) bereits Vergangenheit.
Ohne Korrektur würde die Simulation 2028 mit den (veralteten) Werten von 2026 starten, was zu einer massiven Fehlprognose führt.

## 2. Die Lösung: Baseline-Snapshot
Jedes Profil speichert ein Meta-Datum `baseline_year`. Alle quantitativen Werte im Profil sind strikt an dieses Jahr gekoppelt.

### Beispiel-Datensatz:
- `baseline_year`: 2026
- `startvermoegen`: 50.000 €
- `ep_heute`: 35.0
- `aktuelles_brutto`: 5.000 €

## 3. Der Update-Workflow beim Laden
Beim Import einer Profildatei wird das `baseline_year` mit dem `system_current_year` verglichen.

### Fall 1: baseline_year == system_current_year
Keine Aktion erforderlich. Die Simulation startet wie gewohnt.

### Fall 2: baseline_year < system_current_year (Time-Drift)
Das System erkennt, dass Daten veraltet sind und bietet dem Nutzer zwei Wege an:

#### A. Die "Fortschreibung" (Auto-Projection)
Die Engine simuliert die Jahre zwischen `baseline_year` und `system_current_year` basierend auf den im Profil hinterlegten Annahmen (Sparrate, Zinsen, Inflation, Gehalt).
1. **Berechnung:** Wie viel Vermögen hätte sich laut Plan bis heute ansammeln müssen? Wie viele EP wurden gesammelt?
2. **Vorschlag:** Die neuen Werte werden dem Nutzer präsentiert: *"Laut Plan müsstest du jetzt 62.000 € haben. Korrekt?"*
3. **Migration:** Nach Bestätigung/Korrektur wird das `baseline_year` auf das aktuelle Jahr aktualisiert.

#### B. Der "Kassensturz" (Manual Update)
Der Nutzer wird aufgefordert, die Kern-Werte (Vermögen, EP, Gehalt) manuell für das neue Startjahr zu validieren.

## 4. Umgang mit Meilensteinen
Absolute Meilensteine (z.B. "Rentenbeginn im Jahr 2040") bleiben beim Zeit-Drift unberührt.
Relative Angaben (z.B. "Dauer der Altersteilzeit: 6 Jahre") müssen hingegen kritisch geprüft werden, da sie sich bei einem späteren Startpunkt der Simulation ggf. verkürzen oder verschieben könnten, wenn sie in der Vergangenheit liegen würden.

## 5. Implementierungs-Strategie
1. **Erweiterung des JSON-Schemas:** Hinzufügen von `baseline_year` und `last_updated_at`.
2. **Update-Manager:** Eine neue UI-Komponente in Streamlit, die beim Import erscheint, falls ein Drift erkannt wird.
3. **Drift-Simulation:** Nutzung der bestehenden `calculate_financials_for_year` Logik, um die Differenzjahre schnell hochzurechnen.
