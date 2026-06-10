# Konzept: Erweiterte Zielgruppen für den Rente-O-Mat
**Datum:** 2026-06-07

## Ausgangslage
Der Rente-O-Mat ist aktuell stark auf Angestellte zugeschnitten, die Beiträge in die gesetzliche Rentenversicherung (GRV) einzahlen. Andere Lebensentwürfe und Beschäftigungsarten (z.B. Beamte, verkammerte Freiberufler in Versorgungswerken, Selbständige) sind derzeit nur über Umwege abbildbar.

Das Ziel dieses Konzepts ist es, diese Zielgruppen nativ zu unterstützen, **ohne** die komplexe Berechnungslogik der bestehenden Kern-Engine tiefgreifend umzubauen. Die Lösung liegt in der Abstraktion des Begriffs "Gesetzliche Rente" zu einer allgemeinen "Basisversorgung (Säule 1)".

## 1. Journalisten & Kreative (KSK)
Die Künstlersozialkasse (KSK) ist mathematisch und systemisch identisch mit der gesetzlichen Rentenversicherung (GRV). Die KSK übernimmt lediglich den fiktiven "Arbeitgeberanteil".
- **Umsetzung:** KSK-Versicherte können das Tool exakt so nutzen wie reguläre Angestellte.
- **UI-Anpassung:** Lediglich im Tooltip oder Label kann ergänzt werden: *(gilt auch für KSK-Versicherte)*.

## 2. Ärzte, Apotheker, Anwälte (Berufsständische Versorgungswerke)
Versorgungswerke zahlen im Alter eine Rente aus, die Berechnung der Anwartschaften unterscheidet sich jedoch von der GRV (keine klassischen Entgeltpunkte).
- **Umsetzung (Eingabe-Bypass):** Einführung eines Schalters *"Art der Basisversorgung"*. Wird *"Versorgungswerk"* gewählt, wird die komplexe Berechnung über Entgeltpunkte ausgeblendet.
- **Dateneingabe:** Der Nutzer gibt stattdessen direkt die Werte aus seiner letzten Standmitteilung ein ("Bisher erreichte monatliche Rente" und "Hochrechnung bis Rentenbeginn").
- **Verarbeitung:** Das Tool nutzt diese absoluten Euro-Werte anstelle der berechneten GRV-Rente und wendet die bestehenden Inflations- und Dynamik-Slider darauf an.

## 3. Beamte (Pension)
Beamte erhalten ein Ruhegehalt (Pension), das sich prozentual aus dem letzten ruhegehaltsfähigen Dienstbezug speist.
- **Umsetzung (Eingabe-Bypass):** Über den Schalter *"Art der Basisversorgung"* wählt der Nutzer *"Beamtenversorgung"*.
- **Dateneingabe:** Der Beamte trägt schlicht seine erwartete monatliche Brutto-Pension ein. Die Berechnung der Rente entfällt, die Kern-Simulation nutzt diesen Startwert als fixen monatlichen Cashflow.

## 4. Krankenversicherung im Alter (Der mathematische Knackpunkt)
Die Krankenversicherung verhält sich je nach System unterschiedlich, was zwingend abgebildet werden muss:
- **Angestellte (GRV):** Krankenversicherung der Rentner (KVdR) mit prozentualem Abzug von der Rente (aktueller Status Quo im Tool).
- **Versorgungswerk:** Oft freiwillig gesetzlich (Beitrag bemisst sich an allen Einkünften, gedeckelt) oder privat versichert (PKV).
- **Beamte:** Beihilfeberechtigt mit festem monatlichem PKV-Beitrag, unabhängig von der Pensionshöhe.

### Lösungsansatz für die Krankenversicherung
Bei den allgemeinen Annahmen wird ein neuer Schalter für die *"Krankenversicherung im Alter"* hinzugefügt:
1. **Gesetzlich (Prozentual):** Wie bisher (ca. 11% Abzug direkt von der Bruttorente).
2. **Privat / Fixbetrag:** Der Nutzer trägt seinen erwarteten festen monatlichen PKV-Beitrag im Alter ein (z.B. 400 €).
   - **Verarbeitung:** In diesem Fall zieht das Tool *0%* von der Bruttorente bzw. Pension ab. Stattdessen wird der Fixbetrag (z.B. 400 €) als feste Position zu den regulären monatlichen Ausgaben im Ruhestand addiert.

## Fazit
Durch die Einführung von:
1. Einem Dropdown für die "Art der Versorgung" (Angestellt, Versorgungswerk, Beamte, Keine)
2. Einer direkten Eingabemöglichkeit für Euro-Werte (als Bypass für die Rentenpunkte-Mathematik)
3. Einem Schalter für die Art der Krankenversicherung im Alter (Prozentual vs. Fixbetrag)

...lassen sich alle relevanten Erwerbsbiografien flexibel abbilden, ohne dass tiefgreifende architektonische Änderungen an der Simulation Engine (Rente-O-Mat) vorgenommen werden müssen.
