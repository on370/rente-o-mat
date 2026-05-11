# 🔍 Audit-Report: Rente-O-Mat PRO (Build 0038)

**Auditor:** Antigravity AI Revisor  
**Datum:** 2026-05-07  
**Scope:** Vollständige Code-Review, Berechnungsprüfung, Live-UI-Test  
**Ergebnis:** 7 kritische Fehler, 9 wesentliche Mängel, 12 Verbesserungspunkte

---

## 🔴 KRITISCHE FEHLER (Führen zu falschen Lebensentscheidungen)

### K1: Einkommensteuer wird auf Brutto statt auf zvE berechnet
**Datei:** `logic/engine.py`, Zeile 124  
**Problem:** `berechne_einkommensteuer(brutto * 12, jahr)` — Die EkSt wird auf das **volle Bruttogehalt** berechnet. In Wirklichkeit ist das zu versteuernde Einkommen (zvE) deutlich niedriger, weil Vorsorgeaufwendungen (RV-Beiträge, KV/PV-Beiträge) als Sonderausgaben abgezogen werden. Außerdem fehlt der Werbungskostenpauschbetrag (1.230 € seit 2023).  
**Auswirkung:** Die Steuerlast wird um ca. **15-25% zu hoch** ausgewiesen. Bei 6.000 € Brutto: EkSt auf 72.000 € statt auf ~58.000 € zvE. Das verfälscht alle Netto-Berechnungen und damit die gesamte Lebensplanung.  
**Betrifft auch:** ATZ-Phase (Zeile 137), Rentenphase (Zeile 199)  
**Fix:** Vor der EkSt-Berechnung müssen abziehbare Vorsorgeaufwendungen und der Werbungskostenpauschbetrag vom Brutto subtrahiert werden:
```python
# Vereinfachte Annäherung (korrekt wäre eine volle Sonderausgaben-Berechnung)
rv_abzug = min(brutto, bbg_rv) * rate_rv_an * 2  # AG+AN Anteil, voll abziehbar seit 2023
werbungskosten = 1230 / 12  # Monatlicher Pauschbetrag
zve = brutto - rv_abzug - werbungskosten  # Stark vereinfacht
steuer_ekst = berechne_einkommensteuer(zve * 12, jahr) / 12
```

---

### K2: EP-Modus unterschätzt Rente massiv (fehlende Rentenwert-Projektion)
**Datei:** `logic/engine.py`, Zeile 61  
**Problem:** `val_base = ep_bei_beginn * RENTENWERT_AKTUELL` — Im EP-Modus wird die Rente mit dem **heutigen** Rentenwert (39,32 €) berechnet, obwohl der Rentenwert bis zum Renteneintritt steigt. Bei 2% Rentenanpassung p.a. und Rentenbeginn 2032 wäre der Rentenwert ~44,27 €.  
**Auswirkung:** Die GRV-Rente wird im EP-Modus um **~13%** (6 Jahre × 2%) unterschätzt. Nutzer, die den EP-Modus verwenden, sehen eine deutlich zu niedrige Rente.  
**Fix:** Rentenwert auf das Startjahr projizieren:
```python
jahre_bis_start = max(0, e.get("start", jahr) - aktuelles_jahr)
rentenwert_projiziert = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_start
val_base = ep_bei_beginn * rentenwert_projiziert
```

---

### K3: Regelaltersgrenze — Monate werden systematisch ignoriert
**Datei:** `logic/engine.py`, Zeile 262–263; `ui/sidebar.py`, Zeile 84  
**Problem:** 
```python
regel_jahre, _ = berechne_regelaltersgrenze(geburtsjahr)
rag = geburtsjahr + regel_jahre  # Monate werden verworfen!
```
Für alle Geburtsjahrgänge 1947–1963 wird die Regelaltersgrenze um bis zu 11 Monate falsch berechnet. Beispiel Jahrgang 1960: RAG = 66 Jahre **+ 4 Monate**, aber Code setzt RAG = 2026 statt korrekt Mitte 2026.  
**Auswirkung:** Break-Even-Berechnungen, Abschlagsberechnungen und die Infobox zeigen falsche Werte für alle Übergangsjahrgänge.  
**Fix:** Monate als Bruchteil berücksichtigen:
```python
regel_jahre, regel_monate = berechne_regelaltersgrenze(geburtsjahr)
rag = geburtsjahr + regel_jahre + regel_monate / 12
```

---

### K4: Doppelzählung des Beitragsverlusts im Sankey
**Datei:** `logic/engine.py`, Zeilen 157–182; `app.py`, Zeilen 96–100  
**Problem:** Der Beitragsverlust wird **zweimal** abgezogen:
1. In `_calculate_grv_components`: `val_base = val_at_rag - bv_jahr` (Zeile 71) → die GRV-Einnahme ist bereits reduziert
2. Im Sankey: `add_r("Brutto", "Beitragsverlust", res['Beitragsverlust'])` (app.py:100) → wird nochmals als Abfluss gezeigt

Das Brutto-Node im Sankey hat weniger Zufluss als Abfluss. Die Summe der Abzüge übersteigt das Brutto.  
**Auswirkung:** Sankey-Diagramm ist mathematisch **unbalanciert** und zeigt falsche Proportionen.  
**Fix:** Entweder (a) die GRV-Einnahme im Sankey auf den vollen RAG-Wert setzen (vor Beitragsverlust), oder (b) den Beitragsverlust nicht als separaten Abfluss zeigen, sondern nur als Info.

---

### K5: Netto-GRV-Berechnung verwendet falschen Steuersatz
**Datei:** `logic/engine.py`, Zeilen 216–230  
**Problem:** Die isolierte Netto-GRV für den Strategie-Check wird berechnet als:
```python
grv_netto = payout_brutto - kv - pv - (payout_brutto * (tax_rate / 100))
```
Dabei ist `tax_rate` der Steuersatz des **Gesamteinkommens** (alle Rentenquellen). Für den Break-Even-Vergleich wird aber die GRV isoliert betrachtet. Der Steuersatz auf die GRV allein wäre niedriger (wegen Grundfreibetrag).  
**Auswirkung:** Die Netto-GRV wird zu niedrig berechnet, der Break-Even-Punkt verschiebt sich.  
**Fix:** Die GRV-Steuer separat berechnen (nur steuerpflichtiger Anteil der GRV als zvE).

---

### K6: Gehaltsdynamisierung fehlt komplett
**Datei:** `logic/engine.py`, Zeile 120  
**Problem:** `brutto = params.get('aktuelles_brutto', 0.0)` — Das Gehalt bleibt über die gesamte Aktivphase konstant. Bei einem Berufseinsteiger mit 3.500 € Brutto im Jahr 2026 wird auch 2040 noch 3.500 € angenommen.  
**Auswirkung:** Für junge Nutzer (das erklärte Ziel!) sind alle Projektionen massiv verzerrt. Überschüsse in der Aktivphase werden unterschätzt, EP-Zuwachs wird unterschätzt.  
**Fix:** Gehaltssteigerungsrate als Parameter in "Annahmen" hinzufügen und in der Engine anwenden.

---

### K7: ATZ-Rentenaufstockung fehlt
**Datei:** `logic/engine.py`, Zeilen 129–140  
**Problem:** In der ATZ zahlt der Arbeitgeber gesetzlich verpflichtend zusätzliche RV-Beiträge auf mindestens 80% der Differenz zum vollen Gehalt (§ 3 Abs. 1 Nr. 1b AltTZG). Dies wird nicht berücksichtigt.  
**Auswirkung:** ATZ-Nutzer sammeln in Wirklichkeit **deutlich mehr Rentenpunkte** als die Engine berechnet. Die projizierte GRV-Rente nach ATZ ist zu niedrig.

---

## 🟠 WESENTLICHE MÄNGEL (Funktionale Fehler oder fehlende Features)

### W1: Kirchensteuer-Import funktioniert nicht
**Datei:** `data/persistence.py`, Zeile 39; `ui/sidebar.py`, Zeile 38  
**Problem:** Export speichert `kirchensteuer_satz` als Float (0.08). Import schreibt nach `kist_key`. Aber die Sidebar-Selectbox liest von `kist_display_key`, nicht von `kist_key`. Nach Import steht Kirchensteuer immer auf "Keine".

### W2: Entnahmeplan ist "Geld aus dem Nichts"
**Datei:** `logic/engine.py`, Zeilen 172–175  
**Problem:** Einnahmen vom Typ "Entnahmeplan (Vermögen)" werden dem Budget zugeschlagen, ohne ein Asset zu reduzieren. Es gibt keine Verbindung zum Vermögens-Tab.  
**Status:** Bereits als Konzept dokumentiert (docs/konzept_vermoegenswerte_closed_loop.md), aber nicht implementiert.

### W3: Befristete Ausgaben fehlen
**Problem:** Es gibt keine Möglichkeit, zeitlich begrenzte Ausgaben (Kredit, Unterhalt) zu erfassen. Diese enden aber real und ändern den Cashflow massiv.  
**Status:** In TODO.md vermerkt, nicht implementiert.

### W4: Zusammenveranlagung (Ehepartner) nicht berücksichtigt
**Problem:** Die gesamte Steuerberechnung geht von Einzelveranlagung aus. Verheiratete Paare profitieren vom Splittingtarif (§ 32a Abs. 5 EStG), was die Steuerlast um Tausende Euro pro Jahr senken kann.

### W5: Soli-Berechnung für Rentenphase evtl. zu hoch
**Datei:** `logic/taxes.py`, Zeile 125  
**Problem:** Die Soli-Freigrenze (18.130 €) ist für Einzelveranlagung. Bei Zusammenveranlagung wäre sie doppelt so hoch. Außerdem wird der Soli auf die **Jahressteuer** geprüft, aber die Engine arbeitet monatlich und rechnet hoch. Rundungsfehler möglich.

### W6: Keine Validierung der Eingaben
**Problem:** Kein Input-Validation: Brutto von 100.000 €/Monat, negative Beträge, Rentenbeginn vor Geburt — alles wird akzeptiert.

### W7: Performance — Break-Even in Sidebar
**Datei:** `ui/sidebar.py`, Zeilen 134–154  
**Problem:** `calculate_break_even_data()` berechnet 2 × 75 Jahre Finanzdaten bei **jedem** Streamlit-Rerun (jeder Widget-Klick). Keine Caching-Strategie.  
**Fix:** `@st.cache_data` oder Berechnung in den Tab 4 verschieben.

### W8: Bare `except` in Sidebar
**Datei:** `ui/sidebar.py`, Zeile 153  
**Problem:** `except:` fängt alles ab, auch SystemExit und KeyboardInterrupt. Muss `except Exception:` sein.

### W9: Einnahmen-Initialisierung hardcoded auf Jahrgang 1965
**Datei:** `ui/sidebar.py`, Zeilen 14–15  
**Problem:** Bei Erststart werden die Default-Einnahmen mit `berechne_regelaltersgrenze(1965)` initialisiert, unabhängig vom tatsächlich eingegebenen Geburtsjahr.

---

## 🟡 VERBESSERUNGSPUNKTE (UI/UX, Code-Qualität, Konzeptionelles)

### U1: Tab-Name "Strategie-Check" wird abgeschnitten
**Beobachtung (Live-Test):** Der vierte Tab zeigt nur "Strategie-C..." — der Name ist zu lang für die Viewport-Breite.  
**Fix:** Kürzerer Name, z.B. "⚖️ Strategie" oder "⚖️ Break-Even".

### U2: Slider-Label "Betrachtungsjahr ausblenden" ist irreführend
**Datei:** `ui/sidebar.py`, Zeile 347  
**Problem:** Label sagt "ausblenden" statt "auswählen". Verwirrend.

### U3: Sankey-Werte nicht in deutschem Format
**Beobachtung (Live-Test):** Die Labels im Sankey zeigen z.B. "1634€" statt "1.634 €". Das `separators`-Setting wirkt nur auf Hover-Tooltips, nicht auf Node-Labels.  
**Fix:** Labels in `create_sankey` manuell formatieren:
```python
display_labels.append(f"{label} ({v:,.0f}€)".replace(",", "."))
```

### U4: Info-Box in Meilensteinen ist sehr dicht
**Beobachtung:** Die blaue Box enthält 6 Kennzahlen ohne visuelle Trennung. Schwer lesbar.  
**Fix:** Aufteilung in zwei Boxen (Rentenanalyse | Steuer & Strategie).

### U5: Kein Hinweis bei Rentenbeginn = Regelaltersgrenze
**Problem:** Wenn der Nutzer genau die RAG wählt, zeigt die Box "Rentenabschlag: 0.0%, Beitragsverlust: 0.00 EP". Es fehlt ein positiver Hinweis wie "Kein Abschlag — optimaler Zeitpunkt".

### U6: Ausgaben-Defaults unrealistisch
**Problem:** Alle Kategorien außer Wohnen starten mit 200 €. "Lebensmittel" mit 200 € für eine Person ist knapp, "Gesundheit" mit 200 € ist sehr hoch für jemanden unter 50.

### U7: Code-Duplikation Ausgaben-Inflation
**Dateien:** `logic/engine.py` (Zeilen 232–238) und `app.py` (Zeilen 123–137)  
**Problem:** Die Inflationsberechnung für Ausgaben existiert zweimal (Engine und Sankey-Aufbau in app.py). Divergenzrisiko.

### U8: Fehlende Dynamisierung für private Renten
**Problem:** Nur GRV und bAV werden dynamisiert. Private Renten und "Sonstiges" bleiben konstant, obwohl auch diese in der Realität steigen können.

### U9: Abschläge für langjährig Versicherte (35/45 Jahre) fehlen
**Problem:** Das Modell kennt nur die Standard-Regelaltersgrenze. Die "Rente für besonders langjährig Versicherte" (45 Beitragsjahre, abschlagsfrei ab 63/64) ist nicht modelliert.

### U10: `locals()` Check in app.py fragil
**Datei:** `app.py`, Zeile 173  
**Problem:** `if 'df_trend' not in locals()` — funktioniert zufällig, ist aber kein robustes Pattern.

### U11: Keine Unit-Tests
**Problem:** Kein einziger automatisierter Test. Bei der Komplexität der Steuer- und SV-Berechnungen wäre ein Testset mit Referenzwerten (z.B. BMF-Lohnsteuertabelle) essenziell.

### U12: README veraltet
**Problem:** Die README.md beschreibt Features, die sich seit den letzten Builds stark verändert haben.

---

## 📊 Zusammenfassung der Prioritäten

| Prio | ID | Aufwand | Beschreibung |
|------|----|---------|--------------|
| 🔴 1 | K1 | Mittel | EkSt auf zvE statt Brutto |
| 🔴 2 | K4 | Klein | Beitragsverlust Doppelzählung im Sankey |
| 🔴 3 | K2 | Klein | Rentenwert-Projektion im EP-Modus |
| 🔴 4 | K3 | Klein | Monate bei Regelaltersgrenze |
| 🔴 5 | K6 | Mittel | Gehaltsdynamisierung |
| 🔴 6 | K5 | Mittel | Netto-GRV Steuersatz |
| 🔴 7 | K7 | Mittel | ATZ-RV-Aufstockung |
| 🟠 1 | W1 | Klein | Kirchensteuer-Import |
| 🟠 2 | W6 | Klein | Input-Validierung |
| 🟠 3 | W7 | Klein | Performance/Caching |
| 🟠 4 | W8 | Trivial | Bare except |
| 🟠 5 | W2/W3 | Groß | Entnahmeplan/Befristete Ausgaben |

---

## 🧪 Empfohlene Verifikationsstrategie

1. **Referenzwerte BMF:** Die EkSt-Berechnung gegen die [BMF-Lohnsteuertabelle](https://www.bmf-steuerrechner.de/) prüfen (Brutto → Netto für 3-4 Testfälle).
2. **DRV-Rechner:** Die Rentenberechnung gegen den [DRV-Rentenschätzer](https://www.deutsche-rentenversicherung.de/) validieren.
3. **Sankey-Bilanz:** Für jeden Zeitpunkt prüfen: Summe(Zuflüsse) == Summe(Abflüsse) für jeden Knoten.
4. **Unit-Tests:** Mindestens für `berechne_einkommensteuer`, `berechne_sv_aktiv`, `_calculate_grv_components` und `berechne_regelaltersgrenze`.

---

*Dieser Report dient als Arbeitsgrundlage für die Weiterentwicklung. Priorität haben die kritischen Berechnungsfehler (K1–K7), da diese direkt die Qualität der Finanzprognose und damit potenzielle Lebensentscheidungen beeinflussen.*
