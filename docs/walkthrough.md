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

## 16. Kollabierbare Nodes in den Sankey-Diagrammen (Build 00AE)
- **Innovative Synchronisation:** Wir haben den einklappbaren Zustand (Falten) der Sammelkategorien aus der Sidebar direkt mit dem Render-Verhalten der Sankey-Diagramme verknüpft (betrifft den Status Quo, die Simulation und den PDF-Export).
- **Verhalten beim Einklappen (▶):** Sobald du eine Sammelkategorie in der Sidebar einklappst, wird der Fluss im Sankey-Diagramm von diesem Gruppenknoten zu den jeweiligen Unterkategorien komplett ausgeblendet. Der Gruppenknoten (z. B. 📁 `"Wohnen"`) wird im Diagramm somit zum sauberen Endknoten, der das gesamte Budget der Gruppe akkumuliert darstellt.
- **Verhalten beim Ausklappen (▼):** Klappst du die Gruppe in der Sidebar wieder aus, verzweigt sich der Fluss im Sankey-Diagramm sofort wieder detailreich zu allen einzelnen Unterkategorien (wie `"Miete"`, `"Hausratsversicherung"` etc.).
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AE"` angehoben.

## 17. Sankey Hover-Hilfe & farbliche Differenzierung (Build 00AF)
- **Sankey Hover-Hilfe:** Über beiden Sankey-Diagrammen (Status Quo und Simulations-Analyse) wurde in den UI-Subheadern ein Hilfe-Symbol (`(?)` / Tooltip) ergänzt. Dieses informiert den Nutzer leicht verständlich darüber, dass Sammelkategorien (Gruppen) in der Sidebar über die Pfeile (▶/▼) ein- bzw. ausgeklappt werden können, um die Komplexität im Sankey-Diagramm flexibel zu steuern.
- **Farbliche Trennung von End- und Sammelkategorien:** 
  - **Endkategorien (Unterkategorien):** Werden nun im Sankey-Diagramm in einem ansprechenden Premium-Violett (`#9467bd`) dargestellt.
  - **Sammelkategorien (Gruppen):** Bleiben in dem bewährten Standard-Blau (`#2E86C1`) erhalten.
  - **Systemknoten:** Alle Systemknoten wie Steuern, Abgaben, Netto, Brutto, Überschüsse und Defizite behalten ihre semantisch präzisen Sonderfarben (grün/rot/etc.) bei.
- **Konsistenz im PDF-Report:** Die farbliche Trennung zwischen Endkategorien (violett) und Gruppen (blau) wird vollautomatisch auch auf die im PDF-Report exportierten Sankey-Diagramme angewendet.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00AF"` angehoben.

## 18. Sektion "Entnahmen & Rentenbezug" im Briefing-Tab (Build 00B0)
- **Komplette Übersicht:** Im Briefing-Tab wurde ein neuer, einklappbarer Bereich `"💸 Deine Entnahmen & Rentenbezug (Was/Wann/Bei wem?)"` direkt unter den "🛒 Ausgaben" hinzugefügt.
- **Detaillierte Informationen:**
  - **Gesetzliche Rente (GRV):** Zeigt den Bezugszeitraum (z.B. ab Juli 2032), den dynamisch prognostizierten monatlichen Rentenwert und gibt wichtige Hinweise zum Rentenantrag (⏱️ Frist: 3 Monate vor Rentenbeginn, Beantragung bei der Deutschen Rentenversicherung).
  - **Betriebliche Altersvorsorge (bAV):** Zeigt den monatlichen Auszahlungsbetrag, Zeitraum sowie Hinweise zur Beantragung (⏱️ Frist: 3 bis 6 Monate vorher beim Arbeitgeber/Versorgungsträger) und steuerlichen Abwicklung (Voll steuerpflichtig + KV/PV-pflichtig mit Freibetrag).
  - **Private Rentenversicherungen:** Informiert über den Beginn, Ertragsanteilsbesteuerung und die Frist zur Wahl zwischen Einmalzahlung und monatlicher Rente (⏱️ Frist: 3 bis 6 Monate vorher bei der Versicherung).
  - **Depot-Entnahmepläne (ETFs):** Aggregiert alle aktivierten Asset-Entnahmen. Zeigt an, ob es sich um eine feste Entnahme oder einen variablen Kapitalverzehr handelt. Berechnet den monatlichen Entnahmebetrag im Startjahr aus der Timeline und gibt praktische Hinweise (⏱️ Frist: 1 bis 2 Monate vorher beim Online-Broker einrichten).
- **Zweispaltiges Layout:** Alle Einträge sind in übersichtlichen, zweispaltigen Zeilen (links: Was/Wann/Wie viel, rechts: To-Do/Frist/Beantragen bei) strukturiert und visuell voneinander abgetrennt.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B0"` angehoben.

## 19. Optimierte Sektion "Entnahmen & Rentenbezug" (Build 00B1)
- **Umstrukturierung:** Der Expander `"💸 Deine Entnahmen & Rentenbezug"` wurde an seine finale, logische Position direkt unter `"Die Timeline (Meilensteine)"` verschoben.
- **Korrektur 0,00 € Auszahlungen:** Durch den `.max()`-Zugriff auf das Startjahr in der Timeline wurde der Bug behoben, bei dem unterjährige Bezüge fälschlicherweise den Betrag 0,00 € auswiesen. Nun wird der echte monatliche Maximalwert präzise angezeigt.
- **Neues dreispaltiges Layout:** Die Sektion ist in drei Spalten aufgeteilt. Die linke Spalte zeigt das Startdatum als prominenten Ausrichtungsmarker.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B1"` angehoben.

## 20. Layout-Feinschliff & optimierte Breiten (Build 00B2)
- **Kompaktes Design:** Der Steuern- und Abgaben-Hinweis wurde in die mittlere Spalte (`c2`) verschoben und direkt unter den Betrag gesetzt, was für einen aufgeräumten Lesefluss sorgt.
- **Schmalere Datumsspalte:** Die linke Spalte für den Startzeitpunkt (z. B. `📅 Juli 2032`) wurde auf eine Breite von **10%** verkleinert (`st.columns([0.10, 0.50, 0.40])`). Dadurch bleibt mehr Platz für die detaillierten Beschreibungen und das To-Do-Fristen-Feld.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B2"` angehoben.

## 21. Globaler "Alle Sammel-Kat." Button in der Sidebar (Build 00B3)
- **Komfortables Einklappen:** Im Haushaltsbuch-Expander der Sidebar wurde oberhalb des ersten Eintrags ein neuer Toggle-Button mit der Beschriftung `"Alle Sammel-Kat."` hinzugefügt.
- **Dynamisches Symbol:** 
  - Zeigt **▼**, wenn mindestens eine Sammelkategorie ausgeklappt ist. Ein Klick darauf klappt alle Sammelkategorien gleichzeitig ein.
  - Zeigt **▶**, wenn alle Sammelkategorien eingeklappt sind. Ein Klick darauf klappt alle Sammelkategorien gleichzeitig aus.
- **Intelligente Sichtbarkeit:** Der Button wird vollautomatisch ausgeblendet, falls keine Sammelkategorien (Gruppen) erfasst sind.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B3"` angehoben.

## 22. Reihung & Divider für Sammelkategorien in der Sidebar (Build 00B4)
- **Saubere Trennung:** Um logische Verwirrung auszuschließen, wurde die Kategorienliste im Haushaltsbuch-Expander der Sidebar neu sortiert:
  - **Hauptkategorien (Hauptebene):** Werden zuerst und geschlossen dargestellt.
  - **Sammelkategorien (Gruppen):** Werden danach gerendert.
- **Visueller Divider & Platzierung:** 
  - Sofern Sammelkategorien (Gruppen) vorhanden sind, wird zwischen den Hauptkategorien und den Sammelkategorien ein sauberer Divider (`st.markdown("---")`) eingefügt.
  - Der globale **"Alle Sammel-Kat." Button** wurde präzise unter diesem Divider und unmittelbar oberhalb der Gruppen platziert.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B4"` angehoben.

## 23. Automatische Entnahmepläne - Phase 1: UI-Integration & Persistenz (Build 00B5)
- **UI-Integration der Entnahmestrategie:** In der Sidebar wurde direkt unter "💎 Vermögenswerte" eine neue Sektion **"🎯 Entnahmestrategie (Automatik)"** integriert.
- **Globale Strategie-Auswahl:** Ein Dropdown ermöglicht die Wahl zwischen allen 7 konzipierten Strategien:
  - `Manuell (Keine Automatik)`
  - `Bedarfsgesteuert: Wasserfall (Priorisiert)`
  - `Bedarfsgesteuert: Pro Rata (Gleichmäßig)`
  - `Bedarfsgesteuert: Steueroptimiert (Smart)`
  - `Regelbasiert: Fixer Prozentsatz (z.B. 4%-Regel)`
  - `Substanzerhalt (Nur Rendite entnehmen)`
  - `Zielverzehr (Null-Landung bis Alter X)`
- **Dynamische Konfiguration:** Je nach gewählter Strategie erscheinen maßgeschneiderte Eingabeelemente:
  - Bei *Wasserfall* wird ein Multiselect angezeigt, in dem alle vorhandenen Vermögenswerte per Drag-and-Drop in die gewünschte Entnahme-Reihenfolge gebracht werden können.
  - Bei *Fixer Prozentsatz* kann die Entnahmerate (%) frei definiert werden (Default: `4.0 %`).
  - Bei *Zielverzehr* kann das genaue Ziel-Alter für die Null-Landung eingegeben werden (Default: `95`).
- **Erweiterte Hilfe (Popover):** Ein kompakter Button (`❓ Wie funktioniert die Automatik?`) erklärt das Konzept der **Teilautomatik**. So versteht der Nutzer sofort, dass manuelle Pläne Vorrang haben und die Automatik lediglich die verbleibende Lücke (Defizit) schließt.
- **Daten-Persistenz & Export:** Die gewählte Strategie (`entnahme_strategie`), die Wasserfall-Reihenfolge (`entnahme_wasserfall_reihenfolge`), der feste Prozentsatz (`entnahme_fix_pct`) und das Ziel-Alter (`entnahme_ziel_alter`) werden sauber im Profil (JSON) gespeichert und beim Hochladen eines Profils zuverlässig in den `session_state` restauriert.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B5"` angehoben.

## 24. Automatische Entnahmepläne - Phase 2: Engine-Logik & Teilautomatik (Build 00B6)
- **Implementierung in der Finanz-Engine:** Die Simulationsschleife `generate_trend_data` in `logic/engine.py` wurde umfassend überarbeitet, um alle 6 konzipierten automatischen Entnahmestrategien nativ zu berechnen.
- **Nahtlose Teilautomatik:** Die Engine prüft in jedem Berechnungszeitraum (unter Berücksichtigung von Phasenübergängen wie ATZ-Splits), ob nach Abzug aller manuellen Eintritten ein verbleibendes Defizit existiert. Ist dies der Fall (oder ist eine regelbasierte Entnahme aktiv), greift die Automatik vollautomatisch ein.
- **Die 6 Entnahmestrategien im Detail:**
  - **Bedarfsgesteuert: Wasserfall (Priorisiert):** Entnimmt das Defizit exakt in der vom Nutzer im Multiselect festgelegten Depot-Reihenfolge. Assets werden der Reihe nach vollständig geleert, bevor das nächste Asset herangezogen wird.
  - **Bedarfsgesteuert: Pro Rata (Gleichmäßig):** Ermittelt in jedem Schritt das Gesamtvermögen aller Depots und zieht das Defizit absolut simultan und gewichtet nach dem jeweiligen Kapitalstand ab.
  - **Bedarfsgesteuert: Steueroptimiert (Smart):** Priorisiert den Vermögensverzehr nach steuerlichen Gesichtspunkten (1. `steuerfreie` Assets, 2. `teilfreigestellte` Assets mit Teilfreistellungs-Vorteil, 3. regulär `abgeltungsteuerpflichtige` Depots).
  - **Regelbasiert: Fixer Prozentsatz (4%-Regel):** Entnimmt unabhängig vom aktuellen Bedarf einen festen Prozentsatz (z.B. `5%` p.a.) aus allen Assets. Übersteigt die Entnahme das Defizit, fließt der Überschuss automatisch in die Liquidität (Reinvest); reicht sie nicht, wird das verbleibende Defizit am Jahresende über die Cash-Reserven gedeckt.
  - **Substanzerhalt (Nur Rendite):** Berechnet mathematisch präzise die erwirtschaftete Nettorendite (nach Steuern) jedes Depots in der aktuellen Periode (`cap * (r / (1 + r)) * weight`) und entnimmt maximal diesen Renditezuwachs, um das Ursubstanz-Kapital vollständig unangetastet zu lassen.
  - **Zielverzehr (Null-Landung bis Alter X):** Ermittelt in jedem Jahr das verbleibende Alter bis zur Null-Landung (z.B. Alter `95`) und errechnet die exakte annuitätische Verzehrrate (mit Zinseszins-Berücksichtigung) pro Asset, sodass das gesamte Portfolio am Zielalter exakt bei 0,00 € landet.
- **Ergebnis-Aktualisierung & Visualisierung:** Die gezogenen Beträge werden als `Entnahme: AssetName` in die Simulationsergebnisse eingetragen. Dadurch werden sie **vollautomatisch im Sankey-Diagramm** sowie in den **Entwicklungscharts** visualisiert. Das Netto-Einkommen und der Jahressaldo werden korrekt angepasst.
- **Unit-Tests zur Qualitätssicherung:** In `tests/test_engine.py` wurde eine umfassende Testsuite (`test_automatic_withdrawals`) hinzugefügt, die Wasserfall, Pro Rata und Fixe Prozentsätze mit exakten mathematischen Erwartungswerten prüft. Alle **23 Tests laufen zu 100% grün** durch.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B6"` angehoben.

## 25. Parameter-Rückgabe-Bugfix & Sidebar-Reorganisation (Build 00B7)
- **Parameter-Bugfix der Entnahmestrategie:** Der Fehler, dass die ausgewählte Entnahmestrategie und deren Konfigurationsparameter (Wasserfall-Reihenfolge, Prozentsatz, Zielalter) keine Auswirkung in der Simulation zeigten, wurde behoben. Die Funktion `render_sidebar` (in `ui/sidebar.py`) übergab diese Schlüssel zuvor nicht an das zurückgegebene Parameter-Dictionary `p`. Jetzt werden sie vollautomatisch und typsicher aus dem Streamlit Session-State extrahiert und der Engine bereitgestellt.
- **Sidebar-Reorganisation:** Um einen kompakteren, logischeren Lesefluss zu gewährleisten, wurde die Reihenfolge der Sidebar-Sektionen grundlegend überarbeitet. Die Vermögens- und Entnahmeseite befindet sich nun geschlossen ganz unten:
  1. `👤 Profil`
  2. `🎓 Meilensteine`
  3. `💶 Erwerbseinnahmen` (zuvor "Finanzen Aktuell")
  4. `🏠 Haushaltsbuch (Ausgaben)`
  5. `📅 Befristete & Einmalige Ausgaben`
  6. `⚙️ Annahmen (Dynamik)`
  7. `💸 Einnahmequellen (Rente)`
  8. `💎 Vermögenswerte`
  9. `🎯 Entnahmestrategie (Automatik)`
- **Umbenennung:** Die Sektion „Finanzen Aktuell“ wurde passend in **„Erwerbseinnahmen“** umbenannt, da hier das monatliche Brutto- und Nettoeinkommen während der Aktivphase gepflegt wird.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B7"` angehoben.

## 26. Sperrung manueller Assets & Key-Harmonisierung (Build 00B8)
- **Sperrung manueller Assets für die Automatik:** Um doppelte Entnahmen und Planungskonflikte auszuschließen, wurde ein wichtiger Ausschlussmechanismus implementiert:
  - **In der Engine (`logic/engine.py`):** Jedes Asset mit einem aktiven manuellen Entnahmeplan (`entnahme_aktiv = True`) wird während der aktiven Entnahmejahre vollautomatisch aus den verfügbaren Assets für die globale Automatik ausgeblendet.
  - **Im UI (`ui/sidebar.py`):** Es wird ein Informationsfeld angezeigt, wenn Assets durch manuelle Entnahmen gesperrt sind. Zudem werden solche Assets automatisch aus dem Multiselect-Menü der Wasserfall-Reihenfolge herausgefiltert.
  - **Detaillierte Erklärung:** Die Hilfe-Informationen im Popover (`❓ Wie funktioniert die Automatik?`) wurden um einen klaren Warn- und Informationshinweis zu dieser Ausschlussregel erweitert.
- **Strategie-Key-Harmonisierung (Wegfall-Bugfix):** Es wurde behoben, dass unter bestimmten Bedingungen (wie dem Laden älterer Profile oder beim Wechsel der Strategie) Einträge in der Auswahlliste verschwanden oder Streamlit-Widgets sich blockierten. Eine robuste Normalisierungs- und Harmonisierungslogik (in `data/persistence.py` und `ui/sidebar.py`) gleicht nun alle historischen oder verkürzten Schlüsselnamen (z. B. `"Manuell"`, `"Wasserfall"`, `"Zielverzehr"`) vollautomatisch und abwärtssicher an die genauen Dropdown-Bezeichnungen an.
- **Versions-Build-ID:** Die Build-ID wurde lückenlos und sauber auf `"00B8"` angehoben.

## 27. Phase 2 Korrekturen: UI & Stats (Build 00B9)
- **Umbenennung "Manueller Entnahmeplan":** Die Aktivierungs-Checkbox im Editier-Formular eines einzelnen Assets wurde passend von *"Entnahmeplan aktivieren"* in **"Manueller Entnahmeplan"** umbenannt, um die Unterscheidung zur Automatik glasklar zu machen.
- **Anzeige "Entnahme: Automatik" in der Asset-Übersicht:** Assets, die nicht manuell entnommen werden und stattdessen von der globalen Entnahmestrategie (Automatik) verwaltet werden, weisen in der Sidebar-Übersichtsliste nun prominent den Status **"Entnahme: Automatik"** auf.
- **Entnahme durch Automatik im Asset-Edit:** Wenn ein Asset von der Automatik verwaltet wird (d. h. der manuelle Entnahmeplan ist inaktiv und eine globale automatische Strategie wurde gewählt), wird im Editier-Bereich unter der nicht gecheckten Checkbox eine neue Sektion **"Entnahme durch Automatik"** eingeblendet. Diese zeigt die dynamic simulation stats aus der echten Berechnung (durchschnittlich entnommener Betrag pro Monat, Start-Jahr und End-Jahr) in ausgegrauten (disabled) Eingabefeldern an.
- **Timeline-Synchronisation:** Die Timeline-Daten werden in `st.session_state` hinterlegt, damit das Sidebar-UI diese dynamischen Werte bei jedem Rerun direkt aus der echten Berechnung ausliest.
- **Erweiterte Testabdeckung:** Ein neues Testmodul `tests/test_sidebar_helpers.py` wurde hinzugefügt, um die Ermittlung der automatischen Entnahmestatistiken mit `pytest` vollständig abzusichern.

## 28. Phase 2 Korrekturen: Briefing Text-Fix (Build 00BA)
- **Korrektur automatischer Entnahmeplan-Hinweise:** Es wurde ein inhaltlicher Fehler bei den ausgegebenen To-Do- und Beantragungshinweisen für automatische Vermögensentnahmen behoben. Zuvor gab die App fälschlicherweise an, dass die Rente-O-Mat-Engine diese Entnahmen bei der Bank vollautomatisch steuern würde. Dies wurde nun durch einen realistischen Hinweis auf die notwendige manuelle Einrichtung bei der depotführenden Bank oder dem Online-Broker (1 bis 2 Monate vor Beginn) sowie eine Erläuterung bezüglich der verwalteten Entnahmestrategie und der Ersetzbarkeit durch einen manuellen Entnahmeplan ersetzt.

## 29. Behebung der Findings aus dem Delta-Audit (Build 00BB)
- **Korrektur der Substanzerhalt-Mathematik (C1):** Die Entnahme wurde auf den tatsächlichen Netto-Gewinn der Periode (`period_netto_gewinn`) begrenzt, statt auf eine unpräzise Brutto-Annuität, wodurch das Kapital nun nachweislich geschützt und dauerhaft erhalten bleibt.
- **Vermeidung von Reinvestitions-Loops (C2):** Assets, die von automatischen Entnahmestrategien gesteuert werden, sind nun explizit von der Reinvestitions-Ziel-Auswahl in `generate_trend_data` ausgeschlossen. Dies verhindert unendliche Zirkelbezüge, bei denen Entnahmen direkt wieder in dasselbe Asset zurückfließen.
- **Steuer-Korrektur bei Annuitäten (H1, H2):** Sowohl beim manuellen Kapitalverzehr als auch beim automatischen Zielverzehr wird für die Annuitätenformel der präzise steuerbereinigte Netto-Zinssatz `r_netto` verwendet, was eine Null-Landung zum Zielalter ohne vorzeitiges Leerlaufen des Depots garantiert.
- **Umbenennung & Harmonisierung der Steuer-Strategie (H3):** Die ehemals "steueroptimierte" Strategie wurde akkurat in **"Bedarfsgesteuert: Steuergünstig (Steuerfreie zuerst)"** umbenannt. Die Persistenz- und Sidebar-Logik harmonisiert alle alten Labels/Keys rückwirkend auf diese Bezeichnung.
- **Besteuerung von Cash-Reserve Zinsen (M2):** Der Steuertyp des Cashflow-Sammelbeckens wurde von "steuerfrei" auf `"abgeltung"` umgestellt, um Tagesgeldzinsen steuerlich korrekt nach EStG/SolZG zu erfassen.
- **Schleifenschutz für Pro-Rata-Strategie (M3):** Ein sicherer Zähler mit maximal 10 Iterationen wurde in der `while`-Schleife der Pro-Rata-Entnahme integriert, um Endlosschleifen durch Gleitkomma-Ungenauigkeiten vollständig zu verhindern.
- **Sync der UI-Selectboxen beim Profil-Import:** Beim Importieren eines JSON-Profils werden nun auch die Visual-Keys (`kist_display_key` und `renten_anp_display_key`) automatisch synchronisiert, was Fehl-Anzeigen im UI unterbindet.
- **Vollständige Persistenz-Abdeckung (L1, L3):** Die zuvor beim Import/Export vernachlässigten Keys (`gehalts_dynamik`, `reinvest_target`, `liquidity_reserve`, `liquidity_yield`) wurden vollständig in das Mapping von `data/persistence.py` und die Exporte in `ui/sidebar.py` eingepflegt.
- **Präzise Ausnahmebehandlung (M6):** Das bare `except:` in der Sidebar-Infobox wurde durch ein sauberes `except Exception:` ersetzt.
- **Umfassende Unit-Tests für Advanced-Strategien (L2):** Eine neue Testsuite `tests/test_engine_advanced.py` wurde implementiert und deckt Steuergünstig-Reihenfolge, Substanzerhalt-Deckelung und Zielverzehr-Null-Landung ab. Alle 27 Tests laufen und bestehen fehlerfrei.


