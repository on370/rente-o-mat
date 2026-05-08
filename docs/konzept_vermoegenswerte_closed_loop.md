# Konzept: Geschlossene Vermögens-Simulation (Closed-Loop)

## 1. Zielsetzung
Bisher wurden Entnahmepläne (Einnahmen) und das Startvermögen (Tab Vermögen) weitgehend getrennt voneinander simuliert. Um eine realistische Prognose zu ermöglichen, müssen beide Systeme in einen geschlossenen Kreislauf überführt werden: Jede Entnahme, die das monatliche Budget erhöht, muss das entsprechende Kapitalvermögen mindern.

## 2. Das Asset-Modell
Ein Vermögenswert (Asset) wird durch folgende Parameter definiert:
- **Name:** (z.B. "Welt-ETF", "Tagesgeld")
- **Startwert:** Kapital zum Simulationsbeginn (€)
- **Erwartete Rendite:** Jährlicher Zinssatz (% p.a.)
- **Steuertyp:** (z.B. Abgeltungsteuer-pflichtig, Steuerfrei)
- **Verknüpfte Entnahme:** ID oder Name eines Entnahmeplans

## 3. Der Simulations-Zyklus (Monatlich/Jährlich)
In jedem Simulationsjahr $t$ führt die Engine für jedes Asset $i$ folgende Schritte aus:

### Schritt 1: Brutto-Zuwachs
Das Kapital verzinst sich basierend auf der individuellen Rendite $r_i$:
$$K_{t, \text{brutto}} = K_{t-1} \cdot (1 + r_i)$$

### Schritt 2: Steuerliche Behandlung (Abgeltungsteuer)
Falls das Asset steuerpflichtig ist, wird auf den Gewinn ($K_{t, \text{brutto}} - K_{t-1}$) die Abgeltungsteuer angewendet:
- Berücksichtigung des Sparerpauschbetrags (aktuell 1.000 €).
- Abzug von 25% Kapitalertragsteuer (+ Soli/KiSt).
$$K_{t, \text{netto}} = K_{t, \text{brutto}} - \text{Steuer}$$

### Schritt 3: Entnahme (Transfer ins Budget)
Falls ein Entnahmeplan $E_i$ aktiv ist:
1. Der Betrag $E_i \cdot 12$ wird vom $K_{t, \text{netto}}$ abgezogen.
2. Falls $K_{t, \text{netto}} < (E_i \cdot 12)$, wird nur der Restbetrag entnommen und der Entnahmeplan für die Zukunft deaktiviert (Asset erschöpft).
3. Der entnommene Betrag fließt als **Einnahme** in die Berechnung des monatlichen Überschusses/Defizits ein.

### Schritt 4: Reinvestition von Überschüssen
Falls die Gesamtsimulation am Jahresende einen **Überschuss** ausweist, kann dieser (optional/konfigurierbar) in ein Ziel-Asset reinvestiert werden, anstatt "nutzlos" zu verpuffen.

## 4. Visualisierung (UI-Implikationen)
- **Sankey:** Die Einnahmequelle zeigt nun explizit an, aus welchem Asset sie gespeist wird (z.B. "Entnahme: Welt-ETF").
- **Vermögens-Tab:** Statt einer einzelnen Kurve können die Assets als **Stacked Area Chart** (gestapelte Flächen) dargestellt werden, um das "Abschmelzen" einzelner Töpfe sichtbar zu machen.
- **Pleite-Indikator:** Wenn das letzte liquide Asset auf 0 fällt, markiert die Simulation diesen Zeitpunkt als kritisches Datum.

## 5. Abgrenzung zur bAV-Einmalzahlung
Während die bAV-Einmalzahlung erst bei Auszahlung (nach SV-Abzug über 10 Jahre) in ein Asset migriert, existieren "normale" Vermögenswerte von Beginn an und speisen sich aus bereits versteuertem Einkommen (abzüglich der Abgeltungsteuer auf die Gewinne).
