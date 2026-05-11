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
