# Konzept: Hybrid-Behandlung der bAV-Einmalzahlung

## 1. Problemstellung
Die betriebliche Altersvorsorge (bAV) als Einmalzahlung stellt das System vor eine Herausforderung:
- **Rechtlich** wird sie wie eine Rente behandelt (SV-Beiträge über 120 Monate, Besteuerung ggf. nach Fünftelregelung).
- **Ökonomisch** ist sie jedoch ein Kapitalzufluss, der zum Vermögen zählt und dort verzinst wird.
- **Nutzererwartung:** Der Nutzer möchte sehen, wie diese Einmalzahlung sein monatliches Budget ("Netto") erhöht, ohne dass das Kapital sofort "verpufft".

## 2. Aktuelle Implementierung (Build 0038)
Aktuell ist die Logik strikt getrennt:
1. **Engine:** Berechnet den Netto-Zuwachs (Kapitalzuwachs_Sonder) einmalig im Startjahr der Auszahlung.
2. **Abzüge:** Die Sozialversicherung (KV/PV) wird monatlich vom restlichen Einkommen über 10 Jahre abgezogen (120-Monats-Regel).
3. **Vermögen:** Der Netto-Betrag fließt ins Gesamtvermögen und wird dort global verzinst.

## 3. Zielkonzept (Geplant für Phase 4)
Um die bAV-Einmalzahlung intuitiver zu machen, führen wir das Konzept der **"Asset-Migration"** ein.

### A. Automatischer Transfer in Assets
Statt die Einmalzahlung in einem globalen "Topf" verschwinden zu lassen, wird sie nach der Versteuerung in ein dediziertes Asset (z.B. "bAV-Depot") gebucht.
- Dieses Asset kann einen **individuellen Zinssatz** haben.
- Es bleibt als eigenständiger Posten in der Vermögensbilanz sichtbar.

### B. Virtueller Entnahmeplan (Der "Brückenschlag")
Der Nutzer kann für dieses Asset einen Entnahmeplan definieren:
1. **Logik:** Ein fester Betrag (oder ein Prozentsatz) wird monatlich aus dem Asset entnommen.
2. **Sankey-Integration:** Diese Entnahme erscheint im Sankey-Diagramm als **"Einnahmequelle (Privat/Entnahme)"**.
3. **Vermögens-Integration:** Das Kapital im Asset wird monatlich um die Entnahme gemindert, aber gleichzeitig verzinst.

## 4. Mathematisches Modell
Das Vermögen $V$ des bAV-Assets im Monat $m$ berechnet sich dann wie folgt:

$$V_{m} = V_{m-1} \cdot (1 + \frac{r}{12}) - E + Z_{m}$$

Wobei:
- $r$ = Jährlicher Zinssatz des Assets
- $E$ = Monatliche Entnahme (für das Sankey-Budget)
- $Z_{m}$ = Einmaliger Zufluss (nur im Startmonat)

## 5. Zusammenfassung der Vorteile
- **Transparenz:** Der Nutzer sieht genau, wie lange die bAV-Einmalzahlung sein Budget um Betrag X erhöht.
- **Flexibilität:** Man kann entscheiden, ob man das Geld "verlebt" (Entnahmeplan) oder "vererbt" (Kapitalerhalt).
- **Korrektheit:** Die steuerliche Belastung (SV über 10 Jahre) bleibt korrekt an die Person gekoppelt, während das Geld ökonomisch arbeitet.
