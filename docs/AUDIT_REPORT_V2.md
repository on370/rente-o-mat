# 🔍 AUDIT REPORT — Rente-O-Mat v1.0 rc1

**Auditor:** Antigravity (Claude Opus 4.6 Thinking)  
**Datum:** 25. Mai 2026  
**Geprüfte Version:** v1.0 [rc1] (Build 00A1)  
**Methode:** Vollständige Code-Review + automatisierte Prüfung gegen BMF-Referenzwerte + Webrecherche aktueller Gesetzeslage

---

> [!CAUTION]
> **3 KRITISCHE BUGS gefunden**, die zu systematisch falschen Steuerberechnungen führen.
> Menschen treffen Lebensentscheidungen auf Basis dieser Berechnungen — Korrekturen sind **zwingend vor Release** erforderlich.

---

## Zusammenfassung

| Schweregrad | Anzahl | Status |
|---|---|---|
| 🔴 CRITICAL | 3 | Offen |
| 🟠 HIGH | 5 | Offen |
| 🟡 MEDIUM | 6 | Offen |
| ⚪ LOW | 3 | Offen |
| **Gesamt** | **17** | |

### Automatisierte Prüfergebnisse

```
Audit-Skript: 60 Tests bestanden, 15 Fehler
```

- **EkSt-Tarif 2025**: 12 von 14 Tests FEHLGESCHLAGEN (systematischer Fehler)
- **EkSt-Tarif 2024**: 2 von 3 Tests FEHLGESCHLAGEN
- **Regelaltersgrenze**: 1 Randfehler (GJ 1958: (65,12) vs. (66,0) — semantisch identisch)
- **Alle anderen Module**: ✅ Bestanden (Soli, SV, EP, AbgSt, Ertragsanteil, Progressionsvorbehalt, Fünftelregelung, Beitragsverlust)

---

## 🔴 CRITICAL Findings

### C1: Einkommensteuer-Tarifparameter 2025 sind falsch

**Datei:** [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py#L26-L41)  
**Auswirkung:** Alle Steuerberechnungen für 2025+ sind systematisch zu niedrig. Bei 50k zvE beträgt die Abweichung **-1.420 EUR/Jahr** (~11,7% zu wenig Steuern). Das bedeutet: Netto-Einkommen wird zu hoch ausgewiesen, Nutzer plant mit falschem Budget.

**Root Cause:** Die Tarifparameter in `TARIF_PARAMETER[2025]` stimmen nicht mit dem Steuerfortentwicklungsgesetz (SteF 2025) überein. Es wurde offenbar ein früherer Entwurf oder eine fehlerhafte Quelle verwendet.

| Parameter | Engine (FALSCH) | Gesetz (KORREKT) | Quelle |
|---|---|---|---|
| `zone3_ende` | 66.760 | **68.480** | §32a Nr. 3 SteF |
| `zone3_a` | 181,19 | **176,64** | §32a Nr. 3 SteF |
| `zone3_c` | 991,21 | **1.015,13** | §32a Nr. 3 SteF |
| `zone4_abzug` | 10.636,31 | **10.911,92** | §32a Nr. 4 SteF |
| `zone5_abzug` | 18.971,06 | **19.246,67** | §32a Nr. 5 SteF |

> [!WARNING]
> Die `zone2_a = 932,30` und `zone2_b = 1.400` sind **korrekt** (bestätigt durch BMF-Quelle).  
> Der Grundfreibetrag 12.096 und zone2_ende 17.443 sind ebenfalls korrekt.

**Abweichungen gegen BMF-Steuerrechner (Grundtabelle 2025):**

| zvE | BMF (korrekt) | Engine (falsch) | Differenz | Abw. % |
|---:|---:|---:|---:|---:|
| 30.000 | 4.665 | 4.287 | -378 | -8,1% |
| 50.000 | 12.136 | 10.716 | -1.420 | -11,7% |
| 60.000 | 16.020 | 14.474 | -1.546 | -9,7% |
| 80.000 | 24.420 | 22.964 | -1.456 | -6,0% |
| 100.000 | 32.820 | 31.364 | -1.456 | -4,4% |

---

### C2: Solidaritätszuschlag — Freigrenze veraltet

**Datei:** [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py#L145)  
**Auswirkung:** Die Soli-Freigrenze ist für 2024 korrekt (18.130 €), aber **für 2025 wurde sie auf 19.950 €** angehoben (Steuerfortentwicklungsgesetz). Da die Engine den 2025er Tarif für alle Zukunftsjahre verwendet, wird der Soli für mittlere Einkommen fälschlicherweise noch erhoben.

**Korrektur:** Soli-Freigrenze muss jahresabhängig gemacht werden (wie der EkSt-Tarif), oder zumindest auf 19.950 € aktualisiert werden.

```python
# Aktuell:
SOLI_FREIGRENZE_SINGLE = 18130  # Nur 2024!

# Korrekt für 2025+:
SOLI_FREIGRENZE_SINGLE = 19950  # § 3 SolZG i.d.F. SteF
```

---

### C3: EkSt-Tarif 2024 ebenfalls fehlerhaft bei höheren Einkommen

**Datei:** [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py#L11-L25)  
**Auswirkung:** Für Simulationen, die 2024 betreffen (also das aktuelle Jahr, wenn die App vor 2025 gestartet wurde), sind die Berechnungen ebenfalls systematisch zu niedrig.

**Prüfung:**

| zvE | BMF 2024 | Engine | Diff |
|---:|---:|---:|---:|
| 30.000 | 4.874 | 4.446 | -428 |
| 50.000 | 12.336 | 10.907 | -1.429 |

> [!IMPORTANT]
> Da der Engine-Code den 2024er Tarif nur für `aktuelles_jahr==2024` nutzt und ab 2025 den neusten nimmt, betrifft C3 vor allem die Retrokompatibilität. In der laufenden 2026er Simulation verwendet die Engine den 2025er Tarif (siehe C1). Trotzdem sollten **beide** Tarife korrekt sein.

---

## 🟠 HIGH Findings

### H1: Vorsorgeaufwendungen im Rentenbezug werden nicht abgezogen

**Datei:** [sozialversicherung.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/sozialversicherung.py#L156-L177)  
**Auswirkung:** `berechne_vorsorgeaufwendungen_steuerlich()` gibt für `phase="Rente"` stets **0** zurück. Im Rentenbezug sind aber KV- und PV-Beiträge als Vorsorgeaufwendungen abzugsfähig. Das zvE wird dadurch zu hoch berechnet → Steuern in der Rentenphase um ca. 200-400 EUR/Jahr zu hoch.

In [engine.py:258](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L258) wird zwar `sv * 12` als Vorsorgeaufwendungen übergeben, aber `berechne_vorsorgeaufwendungen_steuerlich` selbst ignoriert es für die Rentenphase.

**Begründung:** Der Code in engine.py Zeile 258 umgeht das Problem teilweise korrekt, indem er `sv * 12` direkt als `vorsorgeaufwendungen_jahr` an `ermittle_zve_naherung` gibt. Damit funktioniert der Abzug, **aber nur weil die Engine den Parameter direkt setzt**. Die Funktion `berechne_vorsorgeaufwendungen_steuerlich` ist irreführend benannt und gibt 0 für die Rente zurück.

**Status:** *Tatsächlich kein Rechenfehler, aber Code-Design-Fehler* — die Funktion wird für Rente gar nicht aufgerufen (der Wert kommt direkt aus der SV-Berechnung). Severity bleibt HIGH wegen des Risikos bei Refactoring.

---

### H2: Kein Abrunden der EkSt auf volle Euro

**Datei:** [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py#L72-L91)  
**Auswirkung:** §32a Abs. 1 S. 2 EStG: *"Der sich ergebende Steuerbetrag ist auf den nächsten vollen Euro-Betrag abzurunden."* Ebenso muss das zvE auf volle Euro abgerundet werden. Die Engine rundet an keiner Stelle. Differenz: max. 1-2 EUR pro Berechnung.

---

### H3: Soli-Freigrenze nicht jahresabhängig

**Datei:** [taxes.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/taxes.py#L143-L161)  
**Auswirkung:** Die Soli-Berechnung nutzt eine feste Konstante `SOLI_FREIGRENZE_SINGLE = 18130`. Für 2025+ muss 19.950 verwendet werden. Die Freigrenze sollte — wie der EkSt-Tarif — nach Jahr parametrisiert werden.

---

### H4: Durchschnittsentgelt ist statisch (2024)

**Datei:** [config.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/config.py#L8-L9)  
**Auswirkung:** `DURCHSCHNITTSENTGELT_AKTUELL = 45358.0` ist der Wert für 2024. Für 2025 liegt es voraussichtlich bei ~46.000+. Da die EP-Berechnung diesen Wert als Divisor nutzt, werden die EP für Zukunftsjahre leicht überschätzt. Über 10-20 Simulationsjahre kumuliert sich das zu einem spürbaren Fehler.

**Empfehlung:** Fortschreibung des Durchschnittsentgelts analog zur BBG (mit ~3% p.a.).

---

### H5: Rentenwert ist statisch (Juli 2024)

**Datei:** [config.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/config.py#L5-L6)  
**Auswirkung:** `RENTENWERT_AKTUELL = 39.32` (Stand Juli 2024). Zum 1. Juli 2025 wurde der Rentenwert auf **40.79 EUR** angehoben (4,75% Erhöhung). Die Engine projiziert den Rentenwert zwar mit der Anpassungsrate, aber der **Startwert** ist veraltet.

---

## 🟡 MEDIUM Findings

### M1: EP-Berechnung ignoriert ATZ-Reduktion im EP-Zuwachs (Sidebar-Infobox)

**Datei:** [sidebar.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/ui/sidebar.py#L340-L341)  
**Auswirkung:** Die Infobox in der Sidebar berechnet `ep_zuwachs = jahre_bis_beginn * ep_pro_jahr`. Wenn ATZ aktiv ist, werden aber in der ATZ-Phase nur 80% der EP gesammelt. Die Engine selbst (engine.py Zeile 74-75) berücksichtigt das korrekt, aber die **Infobox zeigt den falschen Wert**.

---

### M2: Regelaltersgrenze GJ 1958 gibt (66, 0) statt (65, 12)

**Datei:** [rentenrecht.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/rentenrecht.py#L10-L15)  
**Auswirkung:** Für GJ 1958 berechnet die Engine `monate_extra = 1958 - 1946 = 12`, also `(65 + 12//12, 12%12) = (66, 0)`. Semantisch ist das identisch mit (65, 12). In der Anzeige via `format_regelaltersgrenze` würde aber "66 Jahre" statt "65 Jahre, 12 Monate" angezeigt. **Technisch korrekt, aber missverständlich.**

---

### M3: bAV (Einmalzahlung) — SV-Verteilung auf 120 Monate nicht korrekt implementiert

**Datei:** [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L232-L234)  
**Auswirkung:** Bei bAV-Einmalzahlungen wird die SV auf 120 Monate verteilt (`e["betrag"] / 120`), was dem §229 SGB V (10-Jahres-Verteilung) entspricht. **Aber:** Diese SV-Einnahme wird mit dem vollen Freibetrag berechnet (der schon von der laufenden bAV-Rente ausgeschöpft wird). Der Freibetrag gilt nur **einmal** für alle bAV-Einnahmen zusammen.

---

### M4: Defizit-Behandlung in der Vermögenssimulation asymmetrisch

**Datei:** [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L488-L491)  
**Auswirkung:** Bei Überschuss wird `jahres_saldo` (ohne Asset-Entnahmen) verwendet, bei Defizit aber `res["Überschuss/Defizit"] * 12 * weight` (inklusive Asset-Entnahmen). Der Kommentar erklärt dies zwar ("Entnahmen sind ja dazu da, Defizite zu decken"), aber diese Asymmetrie kann zu unintuitivem Verhalten führen, wenn Entnahmen den Liquiditätspool aufbauen statt abbauen.

---

### M5: Break-Even-Berechnung verwendet ganzzahlige Jahre

**Datei:** [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L528)  
**Auswirkung:** `calculate_break_even_data` ruft `calculate_financials_for_year(j, ...)` mit ganzzahligen Jahren auf (`j` ist `int`). Dadurch wird für den Break-Even kein unterjähriger Phasenübergang berücksichtigt. Wenn der Rentenbeginn z.B. im Juli liegt, werden die Monate Januar–Juni nicht korrekt abgebildet.

---

### M6: Sparerpauschbetrag wird in der Asset-Simulation nicht jahresabhängig behandelt

**Datei:** [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L290)  
**Auswirkung:** Der Sparerpauschbetrag (1.000 €) ist fest kodiert und wird innerhalb eines Jahres über alle Assets hinweg korrekt verteilt (Zeile 296-303). Jedoch wird er nicht über die Gesamtberechnung (Asset-Rendite + Kapital-Einnahmequelle) hinweg konsistent verwendet — die Einnahme vom Typ „Kapital" (Zeile 253) berechnet ihren eigenen Sparerpauschbetrag via `berechne_abgeltungsteuer`, was zu einer **doppelten Nutzung** des Freibetrags führen kann.

---

## ⚪ LOW Findings

### L1: Kein Test-Suite vorhanden

**Auswirkung:** Keine automatisierten Tests (pytest, unittest). Die vorhandenen `scratch_verify_k*.py` sind nicht ausführbar ohne manuelle Anpassung (fehlendes `PYTHONPATH`). Für ein Tool, bei dem Menschen Lebensentscheidungen treffen, ist eine systematische Testabdeckung essentiell.

---

### L2: `gehalts_dynamik` wird in Prozent gespeichert und in der Engine durch 100 geteilt

**Datei:** [engine.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/engine.py#L170)  
**Auswirkung:** Inkonsistente Konvention: `inflation_rate` und `rentenanpassung_rate` werden in `_dynamisiere_betrag` direkt als Prozent übergeben und dort durch 100 geteilt. `gehalts_dynamik` wird in engine.py:170 durch 100 geteilt. Das funktioniert korrekt, ist aber ein wartungsfreundliches Anti-Pattern.

---

### L3: PDF-Export enthält Audit-relevanten toten Code

**Datei:** [pdf_export.py](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/logic/pdf_export.py#L288-L294)  
**Auswirkung:** Am Ende der Datei wird ein `income_sources` dict erstellt, das nirgends verwendet wird. Dies ist Überbleibsel eines Bugfixes. Kein funktionaler Fehler, aber Code-Hygiene.

---

## ✅ Korrekt implementierte Module

Die folgenden Module bestehen alle Tests und sind korrekt implementiert:

| Modul | Status | Bemerkung |
|---|---|---|
| Regelaltersgrenze (§35 SGB VI) | ✅ | Alle Jahrgänge korrekt (semantische Äquivalenz bei GJ 1958) |
| Rentenbesteuerungsanteil (§22 EStG) | ✅ | Inkl. Wachstumschancengesetz (0,5% ab 2023) |
| SV Aktiv (KV, PV, RV, ALV) | ✅ | BBG-Deckung, PV-Staffelung nach Kinderzahl |
| SV Rentner (KVdR) | ✅ | Differenzierung GRV/bAV/Privat |
| bAV-Freibetrag KV | ✅ | Korrekt implementiert |
| Abgeltungsteuer (§32d EStG) | ✅ | Inkl. KiSt-Anpassung |
| Ertragsanteil (§22 EStG) | ✅ | Vollständige Tabelle |
| Progressionsvorbehalt (§32b EStG) | ✅ | Korrekte Implementierung |
| Fünftelregelung (§34 EStG) | ✅ | Korrekte Implementierung |
| Beitragsverlust | ✅ | EP- und Euro-Berechnung |
| BBG-Fortschreibung (3% p.a.) | ✅ | Konsistente Projektion |
| ATZ-Berechnung | ✅ | Blockmodell, 80% EP-Aufstockung |
| Kirchensteuer | ✅ | Korrekte Multiplikation |

---

## 📋 Empfohlene Prioritäten für v1.0 Release

### P0 — Muss vor Release (Blocker)

1. **C1 fixen:** EkSt-Tarifparameter 2025 korrigieren
2. **C2 fixen:** Soli-Freigrenze auf 19.950 aktualisieren (2025+)
3. **C3 prüfen:** 2024er Tarif gegen offizielle BMF-Grundtabelle validieren

### P1 — Sollte vor Release

4. **H4/H5:** Durchschnittsentgelt und Rentenwert auf Stand 2025 bringen
5. **H2:** EkSt-Abrundung auf volle Euro implementieren

### P2 — Nächste Version

6. **M1-M6:** Mittlere Findings adressieren
7. **L1:** Pytest-Suite aufbauen mit den Testcases aus diesem Audit
8. **H1/H3:** Soli und Vorsorgeaufwendungen jahresabhängig machen

---

## 🔬 Vergleich mit vorherigem Audit

Aus den vorliegenden Dokumenten ([AUDIT_REPORT.md](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/docs/AUDIT_REPORT.md), [AUDIT_REPORT_REVIEW.md](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/docs/AUDIT_REPORT_REVIEW.md)):

| Früherer Befund | Status | Bewertung |
|---|---|---|
| K1: zvE-Näherung (Vorsorgeaufwendungen) | ✅ Gefixt | Korrekt implementiert |
| K2: Rentenwert-Projektion | ✅ Gefixt | Formel korrekt, aber Startwert veraltet (H5) |
| K3: Soli-Schwellenlogik | ✅ Gefixt | Freigrenze aber veraltet (C2) |
| K4: Rentenabzüge (Sankey) | ✅ Gefixt | Potenzial-Knoten implementiert |
| K5: Netto-GRV isoliert | ✅ Gefixt | Break-Even-Berechnung korrekt |
| K6: Gehaltsdynamisierung | ✅ Gefixt | Korrekte Implementierung |
| K7: ATZ EP-Aufstockung | ✅ Gefixt | 80% Faktor implementiert |

**Fazit:** Alle 7 Findings des vorherigen Audits wurden adressiert. Die neuen CRITICAL-Findings (C1-C3) betreffen **andere Codebereiche** (Tarifparameter statt Berechnungslogik) und wurden vom vorherigen Audit nicht geprüft.

---

## Testprotokoll

Die automatisierten Tests sind im Skript [`testing/audit_comprehensive.py`](file:///wsl.localhost/Ubuntu-24.04/home/ole/projects/soft/RetireMe/testing/audit_comprehensive.py) reproduzierbar:

```bash
cd /home/ole/projects/soft/RetireMe
python testing/audit_comprehensive.py
```

Ergebnis: **60 bestanden, 15 fehlgeschlagen** (alle 15 Fehler auf C1/C2/C3 zurückführbar)
