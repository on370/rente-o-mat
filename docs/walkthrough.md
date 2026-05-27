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

## 8. Phase 4 Audit Anpassungen: Code-Qualität, Unit-Tests & Fehlerbereinigung (Build 00A6)
- **Moderne Unit-Test-Suite (`tests/`):** Wir haben eine umfassende, standardkonforme Test-Suite mit `pytest` aufgesetzt. In 4 dedizierten Testmodulen (Steuerlogik, Sozialversicherung inklusive doppelter bAV-Freibeträge, Rentenrecht inklusive Regelaltersgrenzen und Abschlägen sowie der gesamten Engine-Simulation) werden alle Kernbereiche mit insgesamt 21 Testfunktionen und 78 präzisen Detail-Prüfungen abgedeckt. Die Suite läuft zu 100% fehlerfrei durch.
- **Bereinigung toter Code-Pfade:** Ungenutzte Altlasten (wie `exclude` und `income_sources` am Ende von `logic/pdf_export.py`) wurden rückstandslos entfernt.
- **Vereinheitlichung der Gehalts-Dynamisierung:** In `logic/engine.py` wurde die Gehaltsanpassung über die Jahre hinweg sauber auf die zentrale Hilfsfunktion `_dynamisiere_betrag` umgestellt.
- **Startfehler-Behebung & NameError-Beseitigung:** Behebung des `NameError: name 'jahre_bis_beginn' is not defined`-Fehlers in `ui/sidebar.py`, der beim Starten von Streamlit auftrat, indem die Definition der Variablen sauber vor ihrer Verwendung in den Berechnungen platziert wurde.
- **Buildnummern-Erhöhung:** Erhöhung der Build-ID auf `"00A6"` in `config.py` und Nachführung aller relevanten historischen Aufzeichnungen.

## 9. Detailverbesserung: Monatsgenaue & chronologische Timeline im Briefing-Tab (Build 00A7)
- **Monatsgenaue Angabe:** Die Meilenstein-Timeline im "Briefing" Tab zeigt nun nicht mehr nur bloße Jahreszahlen (z. B. `2032`), sondern gibt den exakten Eintrittsmonat im deutschen Langformat an (z. B. `Juli 2032`). Hierzu wurde die bewährte Formatierungsfunktion `fmt_jahr_monat_de` aus dem PDF-Export-Modul wiederverwendet.
- **Chronologische Sortierung:** Die Ereignisse in der Timeline (Start der Simulation, Beginn/Ende der ATZ, Renteneintritt, Start weiterer Einnahmen und einmalige Sonderausgaben) werden nun chronologisch nach ihrem tatsächlichen Eintrittszeitpunkt (Dezimaljahr) sortiert und ausgegeben, anstatt wie zuvor in statischer Reihenfolge gelistet zu werden.
- **Sonderausgaben-Integration:** Einmalige Sonderausgaben werden nun ebenfalls vollautomatisch mit ihrem exakten Fälligkeitsmonat und -jahr sowie dem formatierten Betrag in die Timeline aufgenommen.
- **Präzisions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00A7"` angehoben.

## 10. Detailverbesserung: Ausgaben-Sektion & Auditoren-Tabs im Briefing (Build 00A8)
- **Detaillierte Ausgaben-Sektion (`🛒 Deine Ausgaben`):** Einbindung einer neuen, einklappbaren Sektion im Briefing-Tab zur lückenlosen Auflistung aller laufenden Budgetkategorien aus dem Haushaltsbuch. Die Tabelle stellt den monatlichen Betrag während des Erwerbslebens (100%), den individuellen prozentualen Minderungsanteil im Ruhestand sowie den prognostizierten monatlichen Ruhestandsbetrag übersichtlich nebeneinander. Am Ende wird eine Summenzeile gebildet.
- **Befristete & einmalige Ausgaben:** Sofern definiert, werden auch alle befristeten Zusatzausgaben (inklusive jährlichem Planungszeitraum) sowie alle einmaligen Sonderausgaben (inklusive exaktem Fälligkeitsmonat und -jahr) sauber in Formaten für Planungsdaten gelistet.
- **100% Transparenz für Auditoren:** Der einklappbare Entwickler-Bereich wurde um komfortable Streamlit-Tabs erweitert. Hierdurch können Gutachter nun nicht mehr nur die `engine.py`, sondern alle vier relevanten Quellcode-Dateien der inneren Fachlogik direkt in der Benutzeroberfläche einsehen:
  - `🖥️ Engine (engine.py)` (Steuerungs- und Simulationslogik)
  - `⚖️ Einkommensteuer (taxes.py)` (Steuertarife 2024/2025, Splitting, Milderungszone Soli)
  - `🏥 Sozialversicherung (sozialversicherung.py)` (BBG-Dynamisierung, Sätze nach Kinderzahl, KV-Freibetrag)
  - `👴 Rentenrecht (rentenrecht.py)` (Regelaltersgrenzen, Rentenabschläge, EP-Berechnungen)
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00A8"` angehoben.

## 11. Betriebssicherheit & Haushaltsbuch-Validierung (Build 00A9)
- **Echtzeit-Namenskollisionsschutz im UI:** Beim Erstellen von neuen Kategorien oder Sammelkategorien (Gruppen) sowie beim Umbenennen bestehender Elemente prüft das UI (`sidebar.py`) nun sofort im Session State, ob der gewünschte Name bereits vergeben ist. Falls ja, wird eine Fehlermeldung (`st.error`) angezeigt, anstatt fehlerhafte Duplikate anzulegen. Dies verhindert logische Verwirrungen und fehlerhafte Zuordnungen.
- **Import-Validierung & Bereinigungsschleife:** Beim Laden von JSON-Profilen (in `persistence.py`) haben wir eine hochrobuste Validierungsschleife integriert, die das gesamte geladene Haushaltsbuch bereinigt:
  - *ID-Kollisionen auflösen:* Jede ID wird auf Eindeutigkeit geprüft; Duplikate werden automatisch mit eindeutigen Zeitstempeln überschrieben.
  - *Zirkelbezüge eliminieren:* Falls ein Element sich selbst als Parent referenziert (`parent_id == id`), wird dieses automatisch auf `None` zurückgesetzt.
  - *Gruppenbereinigung:* Gruppen dürfen selbst kein `parent_id` besitzen; dies wird hart erzwungen.
  - *Referenzprüfung:* Referenziert eine Kategorie ein `parent_id`, das gelöscht wurde oder keine Gruppe ist, wird das `parent_id` sicher auf `None` zurückgesetzt.
  - *Session-State-Konsistenz:* Nach dem Validieren stellt die Schleife sicher, dass alle Berechnungs-Schlüssel (`c_` und `a_`) typkonform als Float/Int im Session State vorliegen.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00A9"` angehoben.

## 12. Behebung von Kategorie-Name/ID-Mismatches & Fallback-Bugs (Build 00AA)
- **Fehleranalyse:** Wir haben einen kritischen Schwachpunkt beim Umgang mit namentlich geänderten Standard-Kategorien (z.B. ID `"Wohnen"`, aber Name im UI `"Miete"`) aufgedeckt.
  1. *UI-Kategorieverlust:* Beim Importieren von Profilen, in denen befristete/einmalige Ausgaben noch über den namentlichen String (z.B. `"Wohnen"`) referenziert waren, schlug das Matching im UI fehl, da die Kategorie `"Wohnen"` nun `"Miete"` hieß. Die Ausgaben fielen fälschlicherweise auf `"Neue Kategorie"` zurück, was im UI zu Duplikaten und Datenchaos führte.
  2. *Engine-Mismatch:* Die Engine (`logic/engine.py`) verwendete bei befristeten Ausgaben fälschlicherweise `EXP_Miete`, während das Sankey-Diagramm in `app.py` nach `EXP_Wohnen` (der ID!) suchte. Dadurch wurden befristete Ausgaben im Sankey-Diagramm gar nicht oder falsch dargestellt.
  3. *Fallback-Bug:* In `logic/engine.py` Zeile 351 griff `ba.get('kategorie', ba['name'])` fehl, da ein leerer String `""` (Hauptebene) existierte und vom `get`-Standardwert nicht überschrieben wurde. Dadurch wurden diese Ausgaben fälschlicherweise als `EXP_` gelistet.
- **Import-Harmonisierung (`persistence.py`):** Ich habe eine automatische Harmonisierungsschleife beim Importieren implementiert. Sie prüft alle Kategorie-Referenzen in befristeten und einmaligen Ausgaben: Falls diese den namentlichen String (z.B. `"Wohnen"`) referenzieren, werden sie sofort und case-insensitive in die korrekte, eindeutige ID (z.B. `"Wohnen"` oder `"kat_..."`) übersetzt.
- **Engine-Korrekturen (`logic/engine.py`):**
  - In Zeile 351 wurde der fehlerhafte `.get()`-Schlüsselzugriff durch einen sicheren logischen Operator `or` ersetzt (`kat = ba.get('kategorie') or ba['name']`). Dies garantiert, dass der leere String `""` korrekt als Falsy bewertet wird und sauber auf den Ausgabennamen zurückfällt.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AA"` angehoben.

## 13. Behebung des Kategorie-Parent-Verlusts beim Profil-Import (Build 00AB)
- **Fehleranalyse:** Beim Importieren von Profilen aus `t.json` wurden bestimmte Standardkategorien (wie `"Wohnen"`, ID `"Wohnen"`, Name `"Miete"`) fälschlicherweise auf die Hauptebene zurückgesetzt, anstatt in ihrer zugeordneten Sammelkategorie (`"Wohnen"`, ID `"group_1779455571047"`) angezeigt zu werden. Dies lag an Streamlits Widget-Zustands-Verhalten:
  1. Vor dem Import existierte die Standardkategorie `"Wohnen"` auf der Hauptebene (`parent_id = None`), wodurch die Auswahlliste zur Gruppenwahl (`p_sel_Wohnen`) im Session State den Index `0` ("— Hauptebene —") hielt.
  2. Nach dem Import lag `"Wohnen"` mit `"parent_id": "group_1779455571047"` vor.
  3. Beim Wiederrendern griff Streamlit jedoch auf den alten Session-State-Wert `p_sel_Wohnen = 0` zurück und überschrieb den importierten Wert fälschlicherweise wieder auf `parent_id = None`.
- **Bereinigung der alten Widget-Zustände (`persistence.py`):** Ich habe vor dem Einlesen der neuen Profildaten eine Bereinigungsschleife in `import_settings` implementiert. Diese löscht alle alten Kategorie-bezogenen Widget-Zustände (wie `p_sel_`, `ren_`, `c_`, `a_`, `tg_` und `collapsed_`) vollständig aus `st.session_state`.
- **Automatische Neuinitialisierung:** Dadurch initialisiert Streamlit die Widgets (insbesondere die Gruppen-Auswahllisten) nach dem Import sauber und fehlerfrei mit den neu importierten, korrekten Werten, wodurch die hierarchische Struktur absolut stabil bestehen bleibt.
- **Automatisierte Testabdeckung:** Eine neue Testdatei `tests/test_persistence.py` wurde hinzugefügt, um das Löschen der alten Widget-Zustände und das korrekte Laden der Elternbeziehung vollautomatisch abzusichern (alle 22 Tests laufen zu 100% grün durch).
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AB"` angehoben.

## 14. Geburtsmonat-Erfassung & monatsgenaue Abschlagskalkulation (Build 00AC)
- **Problemstellung:** Da bisher nur das Geburtsjahr abgefragt wurde, ging das Modell implizit immer vom Geburtsmonat Januar aus. Bei Rentenbeginn im Februar und Geburtsjahr 1966 rechnete das Modell daher mit 23 Monaten vorzeitigen Rentenbezugs (Abschlag 6,9 %) statt mit echten 24 Monaten (Abschlag 7,2 %, wenn der Geburtstag ebenfalls im Februar oder später liegt).
- **Geburtsmonat-Erfassung im Profil:** In der Sidebar (`ui/sidebar.py`) wird nun neben dem Geburtsjahr komfortabel per `st.selectbox` der Geburtsmonat erfasst. Beide Felder sind ansprechend in Spalten nebeneinander angeordnet.
- **RAG-Berechnung & Monatsgenauigkeit:**
  - `berechne_monate_frueher` in `logic/rentenrecht.py` wurde um einen optionalen Parameter `geburtsmonat` (default 1) erweitert.
  - Das Modell errechnet die Regelaltersgrenze nun absolut monatsgenau unter Einbeziehung des Geburtsmonats.
  - In `logic/engine.py` wird die genaue Regelaltersgrenze in `calculate_break_even_data` ebenfalls monatsgenau auf Basis des Geburtsmonats bestimmt.
- **Persistenz (Import/Export):**
  - Der Geburtsmonat wird über `export_params` in `ui/sidebar.py` exportiert.
  - Der Geburtsmonat wird über `import_settings` in `data/persistence.py` wieder eingelesen. Die Variable `prev_geburtsmonat` verhindert automatische Resets beim Neuladen.
- **Automatisierte Absicherung:**
  - Die Testsuite in `tests/test_rentenrecht.py` wurde um genaue Grenzprüfungen erweitert (z. B. 24 Monate Abschlag bei Februar-Geburtstag/Februar-Eintritt vs. 23 Monate bei Januar-Geburtstag/Februar-Eintritt).
  - Alle 22 Unit-Tests laufen zu 100% grün durch.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AC"` angehoben.

## 15. Einstellungs-Widgets im Haushaltsbuch stabilisiert (Build 00AD)
- **Fehleranalyse:** Streamlits Frontend speichert den Zustand von Widgets (wie Textfeldern oder Dropdowns) lokal im Browser und sendet diesen bei einem Rerun basierend auf dem `key` zurück an den Server. Wenn nach einem Profil-Import eine Kategorie mit derselben ID wie zuvor (z. B. ID `"Wohnen"`, jetzt aber Name `"Miete"` statt `"Wohnen"`) gerendert wurde, hat das Frontend die alten Widget-Werte restauriert:
  1. Der Name im Einstellungs-Popover der Unterkategorie zeigte fälschlicherweise den alten Gruppennamen `"Wohnen"` statt `"Miete"`.
  2. Die Gruppenwahl zeigte fälschlicherweise `"— Hauptebene —"` (alter Zustand) statt `"Wohnen"` (neuer Zustand).
- **Lösung über uploader_id Suffix:** Alle Einstellungs- und Steuerungs-Widget-Schlüssel des Haushaltsbuchs (`opt_`, `ren_`, `p_sel_`, `del_` und `tg_`) wurden in `ui/sidebar.py` mit dem Suffix `_{st.session_state.uploader_id}` versehen. Da `uploader_id` bei jedem erfolgreichen Import hochgezählt wird, werden diese Widget-Schlüssel nach einem Import komplett neu erzeugt.
- **Resultat:** Das Streamlit-Frontend findet keinen alten Zustand für diese Schlüssel vor, verwirft alle veralteten Browser-Widget-Zustände vollständig und zeichnet das gesamte Optionen-Menü (Name bearbeiten und Gruppenwahl) absolut korrekt mit den frisch geladenen Profildaten neu.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AD"` angehoben.



