# 🔍 Audit Report — Rente-O-Mat v1.5.0 (Build 00BA)

**Auditor:** Antigravity (Opus 4.6 Thinking)  
**Datum:** 31. Mai 2026  
**Scope:** Delta-Audit seit Build 00A1. Fokus: Automatische Entnahmen, Sammel-Kategorien, Finanzmathematik, Persistenz.  
**Testlauf:** 24/24 Unit-Tests bestanden.

---

## Status der vorherigen Findings

| Altes Finding | Status | Kommentar |
|---|---|---|
| C1: EkSt-Tarif 2025 | ✅ Gefixt | Alle Parameter korrekt (geprüft gegen BMF) |
| C2: Soli-Freigrenze | ✅ Gefixt | Jahresabhängig in `berechne_soli(jahr=)` |
| C3: EkSt-Tarif 2024 | ✅ Korrekt | War nie falsch — die Werte stimmen exakt mit §32a 2024 überein |
| H2: EkSt-Rundung | ✅ Gefixt | `math.floor()` in `berechne_einkommensteuer` |
| H4: Durchschnittsentgelt | ✅ Gefixt | 50.493 € (2025) |
| H5: Rentenwert | ✅ Gefixt | 40,79 € (Juli 2025) |
| H1: Vorsorgeaufwend. Rente | ✅ Gefixt | `berechne_vorsorgeaufwendungen_steuerlich(phase="Rente")` funktioniert |
| M6: Sparerpauschbetrag | ✅ Gefixt | Konsistenter Abzug über Kapital + Assets |
| L2: gehalts_dynamik | ✅ Gefixt | Nutzt jetzt `_dynamisiere_betrag()` |

---

## Neue Findings

### 🔴 CRITICAL

#### C1: Substanzerhalt-Strategie entnimmt zu viel und zerstört Kapital

**Datei:** [engine.py#L589-L592](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L589-L592)

```python
max_withdrawable_yield = cap * (r / (1.0 + r)) * weight
```

**Problem:** Diese Formel berechnet die vorschüssige Annuität für 1 Periode. Sie ergibt bei r=5% nur 4.761,90 € statt der 5.000 € Jahresgewinn. Das ist zunächst konservativ — **aber:** Die Engine besteuert in Schritt 1 (Z.296-309) den Gewinn und zieht die Steuer ab, bevor die Substanzerhalt-Entnahme in Schritt 2 (Z.589) berechnet wird.

Konkretes Beispiel (K=100.000€, r=5%, AbgSt):
1. Gewinn: 5.000 €, Steuer: 1.318,75 €, Kapital danach: 103.681,25 €
2. Substanzerhalt-Entnahme: `103.681,25 * 0.05/1.05 = 4.937,20 €`
3. Kapital nach Entnahme: **98.744,05 €** → **-1.255,95 € unter Startkapital!**

**Auswirkung:** Nutzer, die "Substanzerhalt" wählen, verlieren jährlich ~1,3% ihres Kapitals statt es zu erhalten. Über 20 Jahre sind das >20% Verlust.

**Fix:** Die Entnahme muss den Netto-Gewinn (nach Steuern) nutzen, nicht eine Brutto-Annuität:
```python
# Korrekt: Entnehme nur den Netto-Gewinn (Gewinn - Steuer)
netto_gewinn = gewinn - steuer  # gewinn und steuer sind in Z.296-307 bereits berechnet
max_withdrawable_yield = min(current_deficit, netto_gewinn * weight)
```

Alternative: Die Gewinn/Steuer-Werte aus der Asset-Simulation (Z.296-307) speichern und in Z.589 wiederverwenden, statt sie aus dem Brutto-`r` neu zu berechnen.

---

#### C2: Fixe-Prozentsatz-Entnahme ("4%-Regel") erzeugt Reinvestitions-Loop

**Datei:** [engine.py#L566-L576](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L566-L576)

**Problem:** Die Strategie `Regelbasiert: Fixer Prozentsatz` entnimmt **bedingungslos** (auch bei Überschuss), anders als die bedarfsgesteuerten Strategien (Z.491: `if current_deficit > 0`). Die entnommenen Beträge werden zum Netto-Einkommen addiert (Z.575) und erhöhen den Überschuss. In Z.628-648 wird der Überschuss dann reinvestiert — möglicherweise **in dasselbe Asset**. 

**Auswirkung:** Bei ausreichendem Einkommen entsteht ein Loop: Asset → Entnahme → Netto → Überschuss → Reinvestition → Asset. Das Ergebnis ist mathematisch korrekt (Kapital bleibt ~gleich), aber die dargestellten Entnahmen/Einkommen sind fiktiv aufgebläht und irreführend.

**Fix:** Entweder:
- (a) Die fixe Prozentsatz-Entnahme nur ausführen, wenn ein Defizit besteht, oder
- (b) Assets mit aktiver automatischer Entnahme vom Reinvestitionsziel ausschließen.

---

### 🟠 HIGH

#### H1: Annuitätenformel (Kapitalverzehr) ignoriert Steuern auf Gewinne

**Datei:** [engine.py#L312-L324](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L312-L324)

Die Annuitätenformel selbst ist mathematisch korrekt (bestätigt: 8.024,26 = Referenz). **Aber:** Sie berechnet die Rate mit dem Brutto-Zinssatz `r`, obwohl in Z.296-307 die Steuer auf den Gewinn bereits abgezogen wurde. Das Kapital `a_s["kapital"]` ist also nach Steuern kleiner als erwartet.

**Auswirkung:** Die berechnete Entnahmerate ist zu hoch für steuerbelastete Assets. Das Kapital läuft vor dem geplanten Enddatum leer. Bei langen Zeiträumen (30+ Jahre) summiert sich der Fehler erheblich.

**Fix:** Entweder den Netto-Zinssatz `r_netto = r * (1 - effektiver_steuersatz)` verwenden, oder die Annuität auf dem noch nicht besteuerten Kapital berechnen.

---

#### H2: Zielverzehr-Strategie berechnet Annuität ohne Steuer-Korrektur

**Datei:** [engine.py#L604-L622](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L604-L622)

Identisches Problem wie H1: Die Annuitätenformel in Z.613 nutzt die Brutto-Rendite `r`, obwohl die Kapitalrendite in Z.296-307 bereits besteuert wurde. Die Entnahme ist systematisch zu hoch.

---

#### H3: Steueroptimierte Strategie ist nur eine Sortierung, keine Steueroptimierung

**Datei:** [engine.py#L541-L564](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L541-L564)

**Problem:** Die "Steueroptimierte" Strategie sortiert Assets nach Steuertyp (`steuerfrei → teilfreistellung → abgeltung`) und entnimmt dann wie ein normaler Wasserfall. Das ist **keine** echte Steueroptimierung, weil:

1. Sie nutzt nicht den Sparerpauschbetrag gezielt aus (1.000 € steuerfreier Gewinn auf AbgSt-Assets)
2. Steuerfreie Entnahmen erzeugen keinen Steuervorteil — sie **verschieben** die Steuer nur
3. Die Entnahme aus dem steuerpflichtigen Asset könnte günstiger sein, wenn dadurch der Grundfreibetrag genutzt wird

**Auswirkung:** Nutzer vertrauen auf eine "smarte" Strategie, die nicht smarter als ein Wasserfall ist. Das **Label** ist irreführend.

**Fix (minimal):** Das Label in "Steuergünstig: Steuerfreie Assets zuerst" umbenennen. Oder (besser): Tatsächliche Steueroptimierung implementieren, die den Sparerpauschbetrag berücksichtigt.

---

#### H4: Entnahmen aus automatischen Strategien werden nicht besteuert

**Datei:** [engine.py#L486-L622](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L486-L622)

**Problem:** Alle automatischen Entnahmestrategien entnehmen Kapital und addieren es direkt zum `Netto-Einkommen` (Z.508, 537, 561, 575, 599, 621). Aber: Die Entnahme enthält anteilig Gewinne, die der Abgeltungsteuer unterliegen. Die Steuern auf die **Gewinne innerhalb der Entnahme** werden nicht berechnet.

Dies ist konzeptionell das gleiche Problem wie bei manuellen Entnahmeplänen (dort auch steuerfrei, weil "Kapitalrückzahlung" — vgl. Konzeptdokument). Die Annahme "Entnahmen sind steuerfrei" ist nur korrekt, wenn das Kapital ausschließlich aus bereits versteuerten Mitteln besteht. Tatsächlich fließt aber auch unversteuerte Rendite ein.

**Milderung:** Die Engine besteuert die Rendite bereits jährlich (Z.296-307), daher ist das nicht doppelt — aber bei der Entnahme wird der Gewinnanteil der Entnahme nicht separat besteuert (anders als beim echten Depot, wo FIFO-Methode gilt).

**Empfehlung:** Akzeptabel als Vereinfachung, aber im Briefing/Disclaimer explizit dokumentieren: "Steuer auf Kapitalgewinne wird jährlich pauschal auf die Rendite berechnet, nicht bei Entnahme."

---

### 🟡 MEDIUM

#### M1: Sammel-Kategorien beeinflussen die Rentenanpassung nicht korrekt

**Datei:** [sidebar.py#L544-L549](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L544-L549) + [engine.py#L341-L346](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L341-L346)

**Problem:** Sammel-Kategorien (Gruppen, `is_group=True`) haben selbst ein `rv_pct`-Feld (Default 100), aber dieses wird nie verwendet — die Engine iteriert nur über Leaf-Kategorien. Die Gruppe dient rein der UI-Organisation. **Funktional kein Bug**, aber die Tatsache, dass Gruppen ein `rv_pct`-Feld haben, ist irreführend und überflüssiger Ballast.

---

#### M2: Cash-Reserve (Liquidität) wird nicht besteuert

**Datei:** [engine.py#L398-L399](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L398-L399)

Die Cash-Reserve wird mit `liq_yield` verzinst (Z.399: `rendite_pa: liq_yield`) und als `steuerfrei` konfiguriert. In der Realität unterliegen Zinsen auf Tagesgeld der Abgeltungsteuer. Bei 3% Zins und 50.000€ Cash-Reserve sind das ~375 € Steuern p.a., die ignoriert werden.

**Fix:** `steuertyp: "abgeltung"` statt `"steuerfrei"`.

---

#### M3: Pro-Rata-Strategie hat Endlos-Schleife-Risiko

**Datei:** [engine.py#L515](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L515)

```python
while current_deficit > 0.0001:
```

Die `while`-Schleife hat zwar Break-Bedingungen (Z.517-518, Z.527-528), aber: Wenn durch Rundungsfehler `current_deficit` nie unter die Schwelle fällt und `total_cap > 0` bleibt (z.B. durch Floating-Point-Impräzision bei sehr kleinen Beträgen), entsteht eine Endlosschleife.

**Fix:** Maximal-Iterationen begrenzen (`max_iter = 10`) oder die Schleife durch eine direkte Berechnung ersetzen (eine einzelne Iteration reicht bei Pro-Rata, da jedes Asset proportional entleert wird).

---

#### M4: `gehalts_dynamik` wird im Sidebar-Return als Prozent übergeben, in der Engine als Prozent interpretiert

**Datei:** [sidebar.py#L1717](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L1717) + [engine.py#L176](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L176)

In `sidebar.py` Z.1717 steht `"gehalts_dynamik": gehalts_dyn` (Wert vom Slider, z.B. `1.0` für 1%). In `engine.py` Z.176 wird `_dynamisiere_betrag(brutto_base, ..., params.get('gehalts_dynamik', 1.0))` aufgerufen. `_dynamisiere_betrag` teilt intern durch 100 (Z.43). Das ist **korrekt**, aber die Konvention ist inkonsistent: `inflation_rate` wird auch als Prozent übergeben und auch in `_dynamisiere_betrag` durch 100 geteilt. Kein Bug, aber fragile Konvention.

---

#### M5: Befristete Ausgaben werden bei Kategorien-Löschung nicht bereinigt

**Datei:** [sidebar.py#L597-L606](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L597-L606)

Wenn eine Kategorie gelöscht wird, werden ihre Widget-Keys (`c_`, `a_`) entfernt. Aber befristete Ausgaben, die auf diese Kategorie verweisen (über `ba["kategorie"] == kat_id`), werden **nicht** aktualisiert. Die `kategorie`-Referenz verwaist. Im Engine-Code (Z.352) wird dann `kat = ba.get('kategorie') or ba['name']` verwendet, was den Fallback korrekt handhabt — aber die Ausgabe taucht dann unter einem falschen/unbekannten Key im `ausgaben_details`-Dict auf.

---

#### M6: `bare except` in der Infobox

**Datei:** [sidebar.py#L443](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L443)

```python
except:
    be_info = "Berechnung läuft..."
```

Fängt alle Exceptions ab, inklusive `SystemExit`, `KeyboardInterrupt`. Muss `except Exception:` sein.

---

### ⚪ LOW

#### L1: Persistenz exportiert `gehalts_dynamik` nicht

**Datei:** [sidebar.py#L234-L274](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L234-L274)

Der Export-Dict enthält `gehalts_dynamik` nicht. Beim Import fehlt ebenfalls der Key im Mapping (Z.40-62 in `persistence.py`). Effekt: Nach Import steht Gehaltsdynamik auf Default 1.0%, nicht auf dem gespeicherten Wert.

---

#### L2: Kein Test für automatische Entnahme-Strategien "Steueroptimiert", "Substanzerhalt", "Zielverzehr"

**Datei:** [tests/test_engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/tests/test_engine.py)

Nur Wasserfall, Pro Rata und Fixer Prozentsatz werden getestet. Die drei komplexesten Strategien haben keine Testabdeckung.

---

#### L3: `reinvest_target` und `liquidity_reserve` fehlen im Persistenz-Mapping

**Datei:** [data/persistence.py#L40-L62](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/data/persistence.py#L40-L62)

Die Keys `reinvest_target`, `liquidity_reserve`, `liquidity_yield` werden beim Export gespeichert (sidebar.py Z.264-266), aber beim Import nicht geladen — sie fehlen im `mapping`-Dict.

---

## Zusammenfassung

| Schweregrad | Anzahl | IDs |
|---|---|---|
| 🔴 CRITICAL | 2 | C1, C2 |
| 🟠 HIGH | 4 | H1, H2, H3, H4 |
| 🟡 MEDIUM | 6 | M1-M6 |
| ⚪ LOW | 3 | L1-L3 |

### Empfohlene Reihenfolge

1. **C1 + H1 + H2** zusammen fixen (gleiche Wurzel: Brutto-Rendite vs. Netto-Rendite nach Steuern)
2. **C2** fixen (4%-Regel nur bei Defizit oder Reinvest-Exclusion)
3. **L1 + L3** fixen (Persistenz-Lücken — trivial)
4. **H3** Label korrigieren
5. **M2** Cash-Reserve-Steuertyp ändern
6. **M3** Pro-Rata max_iter einführen
7. **M6** bare except → Exception
8. **L2** Fehlende Tests nachziehen
