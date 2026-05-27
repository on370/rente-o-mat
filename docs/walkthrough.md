# 🚀 Walkthrough: Rente-O-Mat Upgrade (Phase 1 & 2)

Wir haben den Rente-O-Mat erfolgreich von einem reinen "Status-Quo"-Prototypen zu einem **fachlich hochpräzisen Finanzplanungstool** umgebaut.

Alle gefundenen Fehler wurden behoben und die Berechnungslogik entspricht nun dem aktuellen deutschen Steuer- und Sozialversicherungsrecht (Stand 2024/2025).

Hier ist eine Zusammenfassung der wichtigsten Änderungen:

## 1. Bugfixes & Stabilität (Phase 1)
- **ATZ-Sankey-Bug behoben:** Die Altersteilzeit wurde im Sankey-Diagramm zuvor nicht korrekt dargestellt. Das Diagramm spaltet das Brutto in der Aktivphase der ATZ nun korrekt in "ATZ-Gehalt" und "AG-Aufstockung" auf.
- **Python-Infrastruktur:** Es wurden `__init__.py` Dateien hinzugefügt und eine `requirements.txt` angelegt, um die App robuster zu machen.
- **Dynamisches Jahr:** Die App startet nun immer relativ zum aktuellen Jahr (aktuell 2026), nicht mehr fest verdrahtet.

## 2. Fachliche Präzision: Steuern & Abgaben (Phase 2)
- **Mehrjähriger Einkommensteuertarif:** Die App nutzt nun die korrekten Grenzwerte für 2024 und 2025+ (Grundfreibetrag 12.096€).
- **Solidaritätszuschlag & Kirchensteuer:** Beide Steuerarten wurden integriert. Der Soli berücksichtigt die korrekte Milderungszone, die Kirchensteuer ist über die Sidebar als Option (Keine, 8%, 9%) wählbar.
- **Abgeltungsteuer:** Kapitalerträge werden nun getrennt vom regulären Einkommen mit der Abgeltungsteuer (25% + Soli + KiSt) unter Berücksichtigung des Sparerpauschbetrags (1.000€) versteuert.
- **Dynamische Sozialabgaben:** Die Beitragsbemessungsgrenzen (BBG) und Sätze wurden als Tabelle hinterlegt und steigen für Zukunftsjahre um ca. 3% pro Jahr. 
- **Kinder-Bonus in der Pflegeversicherung:** Die Anzahl der Kinder kann nun in der Sidebar eingegeben werden, wodurch der PV-Beitrag gemäß aktueller Gesetzeslage sinkt.
- **bAV & Private Renten:** Die Betriebsrente wird nun richtigerweise zu 100% nachgelagert besteuert (kein Kohortenprinzip mehr!). Private Renten ermitteln ihren Ertragsanteil automatisch anhand des tatsächlichen Renteneintrittsalters.

## 3. Dynamisierung & Vermögensaufbau (Das Herzstück)
- **Inflation & Anpassungen:** In der Sidebar gibt es einen neuen Reiter "⚙️ Annahmen". Hier können nun getrennte Inflationsraten für die Ausgaben (Allgemeine Inflation) sowie Anpassungsraten für die Gesetzliche Rente und die bAV definiert werden. Die App berechnet den Zinseszinseffekt über Jahrzehnte hinweg.
- **Startvermögen & Rendite:** Nutzer können ein Startvermögen und eine erwartete Kapitalrendite hinterlegen.
- **Neuer Tab "💰 Vermögensentwicklung":** Ein komplett neues Diagramm zeigt die kumulative Entwicklung des Kapitals. Wenn die Ausgaben die Einnahmen übersteigen, schrumpft das Vermögen. Fällt es unter die rote Null-Linie, zeigt die App auf den ersten Blick, ab wann das Geld ausgeht.

## 4. UI/UX Verbesserungen
- **Sidebar-Struktur:** Die Sidebar wurde in eine logische Reihenfolge gebracht (Profil -> Meilensteine -> Finanzen -> Einnahmen -> Haushaltsbuch -> Annahmen).
- **KPI-Dashboard:** Über dem Sankey-Diagramm stehen nun die wichtigsten Kennzahlen des gewählten Jahres als große, gut lesbare Metriken (Brutto, Netto, Steuerlast, Überschuss).
- **Rückwärtskompatibilität:** Die Export-Funktion erzeugt nun "v2.0" JSONs. Wenn alte "v1" Dateien importiert werden, füllt die App fehlende Werte (wie Inflation oder Kirchensteuer) automatisch mit sicheren Standardwerten auf.

---

> [!TIP]
> **Probieren Sie es aus!** Starten Sie die App lokal mit `streamlit run app.py` und laden Sie bei Bedarf eine alte JSON-Datei hoch, um den nahtlosen Übergang und die neuen Features zu testen. Die neuen Steuer- und SV-Berechnungen werden sofort die Zahlen in den Diagrammen verändern.

Die Basis ist damit grundsolide. Für eine zukünftige Iteration stehen dann Features wie **Rentenabschläge**, **Szenarien-Vergleich** oder **PDF-Exporte** auf der Liste!

## 5. P0-Audit Korrekturen: Steuern & Soli (Phase 1 / Build 00A2)
- **Korrektur ESt-Tarif 2024:** Der Grundfreibetrag wurde auf exakt 11.784 € angehoben und alle Progressionskoeffizienten und Abzugsbeträge der rückwirkend geänderten Gesetzeslage angepasst, um einen absolut stetigen Übergang an den Bereichsgrenzen zu gewährleisten.
- **Korrektur ESt-Tarif 2025+:** Alle Parameter wurden exakt an das Steuerfortentwicklungsgesetz angepasst (Grundfreibetrag 12.096 €, Ende Zone 3 bei 68.480 €, Steigungsfaktor `zone3_a = 176,64` und Integrationskonstante `zone3_c = 1.015,13 €`).
- **Jahresabhängiger Solidaritätszuschlag:** Die Soli-Besteuerung passt sich nun dynamisch an das Steuerjahr der Berechnung an. Für Jahre bis einschließlich 2024 gilt die Freigrenze von 18.130 € (Einzelveranlagung), ab 2025 steigt sie automatisch auf den neuen gesetzlichen Grenzwert von 19.950 € (bzw. 39.900 € bei Zusammenveranlagung).
- **Durchgängiger Jahresbezug in der Engine:** Die Weichenlogik in `logic/engine.py` reicht das Berechnungsjahr (`jahr`) an alle `berechne_soli`-Schnittstellen weiter, wodurch die Entlastungswirkung der angehobenen Soli-Freigrenze ab 2025 im zeitlichen Verlauf der Rentensimulation perfekt abgebildet wird.
- **Umfassende Testabdeckung:** Alle 75 mathematischen und fachlichen Testfälle in der Testsuite `testing/audit_comprehensive.py` wurden auf die neuen Tarife aktualisiert und laufen zu 100% grün durch.

## 6. Phase 2 Audit Anpassungen: Gesetzliche Präzision & Stand 2025 (Build 00A4)
- **Gesetzliche Rundung bei der Einkommensteuer (§ 32a Abs. 1 EStG):** Sowohl das zu versteuernde Einkommen (zvE) als auch das berechnete Steuerergebnis werden nun mathematisch korrekt auf den nächsten vollen Euro abgerundet (`math.floor`). Dies eliminiert Cent-Abweichungen und entspricht exakt der Arbeitsweise professioneller Steuersoftware.
- **Aktualisierung der Konstanten auf Rechtsstand 2025:**
  - `RENTENWERT_AKTUELL` wurde auf den ab 1. Juli 2025 gesetzlich gültigen Wert von **40,79 €** angehoben (eine Steigerung um 3,74%).
  - `DURCHSCHNITTSENTGELT_AKTUELL` wurde auf den vorläufigen gesetzlichen Wert für 2025 von **50.493 €** angepasst. Dies gewährleistet eine hochpräzise und zeitlich exakte Berechnung der Entgeltpunkte (EP) bei gehaltsbasierten Rentenszenarien.
- **Präziser Sonderausgabenabzug für Vorsorgeaufwendungen im Ruhestand:** Die steuerliche Entlastung in der Rentenphase wird nun sauber über `berechne_vorsorgeaufwendungen_steuerlich` ermittelt. Dabei werden die tatsächlichen Beiträge des Rentners zur Basis-Krankenversicherung (96% des KVdR-Beitrags, da kein Krankengeldanspruch) und Pflegeversicherung (100% abziehbar) präzise pro Einnahmequelle bestimmt.

## 7. Phase 3 Audit Anpassungen: UX-Details & logische Konsistenz (Build 00A5)
- **Altersteilzeit-Korrektur in der Infobox:** Der EP-Zuwachs in der Sidebar-Infobox berücksichtigt bei aktiver Altersteilzeit (ATZ) nun exakt die 80%ige Beitragsleistung des Arbeitgebers auf das fiktive Vollzeit-Brutto (Blockmodell). Dies verhindert eine zuvor naive Überberechnung der Rentenpunkte im Informationstext.
- **Monatsgenaue Break-Even-Berechnung:** Die Graphenschnittstelle im Strategie-Check ermittelt den Break-Even-Punkt nun hochpräzise, indem sie im Kalenderjahr des Rentenbeginns nur die echten Bezugsmonate (z. B. 6 Monate Rente bei Beginn im Juli) anrechnet, anstatt wie zuvor ganze Jahre zu pauschalisieren.
- **Einmaliger bAV-KV-Freibetrag bei mehreren Quellen:** Bei mehreren parallelen bAV-Bezügen (z. B. einer monatlichen Betriebsrente und dem monatlichen 1/120-Anteil einer Einmalzahlung) summiert die SV-Engine die Einnahmen nun auf und wendet den gesetzlichen KV-Freibetrag (187,25 € in 2025) nur exakt einmal an. Die Beiträge werden anschließend für das Sankey-Diagramm anteilig aufgeteilt.
- **Konsistenter Sparerpauschbetrag über alle Kapitalquellen:** Der Sparerpauschbetrag von 1.000 € wird pro Kalenderjahr nun über alle Kapitalerträge (sowohl manuell erfasste Kapital-Einnahmen im Ruhestand als auch die Depotgewinne aus der Asset-Simulation) hinweg exakt einmal gewährt.



