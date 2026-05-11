# 🔍 Audit-Review: Status der K-Befunde (Build 0044)

**Reviewer:** Claude Opus (Thinking Model)  
**Datum:** 2026-05-08  
**Scope:** Code-Review aller K1–K7-Fixes aus AUDIT_REPORT.md gegen den aktuellen Quellcode  

---

## Projektstatus (Kurzüberblick)

Das Projekt **Rente-O-Mat PRO** ist eine Streamlit-basierte Finanzplanungs-App für die deutsche Altersvorsorge. Die Architektur ist sauber modularisiert:

| Modul | Verantwortung | LOC |
|-------|---------------|-----|
| `logic/engine.py` | Zentrale Simulation (Brutto→Netto pro Jahr) | 334 |
| `logic/taxes.py` | EkSt-Tarife, Soli, KiSt, Abgeltungsteuer, zvE | 226 |
| `logic/sozialversicherung.py` | SV-Beiträge (KV, PV, RV, ALV) nach Phase | 177 |
| `logic/rentenrecht.py` | Regelaltersgrenze, EP, Abschläge, Beitragsverlust | 73 |
| `ui/sidebar.py` | Eingabe-UI, Infobox, Export/Import | 365 |
| `ui/charts.py` | Sankey, Trend, Vermögen, Break-Even Charts | 256 |
| `app.py` | Tab-Layout, Sankey-Aufbau, Daten-Pipeline | 228 |

---

## K1: EkSt auf zvE statt Brutto ✅ BEHOBEN (korrekt)

**Implementierung:**
- `taxes.py` enthält `ermittle_zve_naherung()` (Zeile 49–60) mit Werbungskosten (1.230€/102€), Sonderausgaben (36€) und Vorsorgeaufwendungen.
- `sozialversicherung.py` enthält `berechne_vorsorgeaufwendungen_steuerlich()` (Zeile 156–176) mit RV (100% AN+AG seit 2023) und KV/PV (96% Basisabsicherung).
- `engine.py` ruft für alle drei Phasen (Aktiv Z.146–150, ATZ Z.164–168, Rente Z.232–236) korrekt `ermittle_zve_naherung()` vor `berechne_einkommensteuer()` auf.

**Bewertung:** Sauber implementiert. Die Näherung ist für eine Planungs-App angemessen.

---

## K2: Rentenwert-Projektion im EP-Modus ✅ BEHOBEN (korrekt)

**Implementierung:**
- `engine.py` Z.66–68 (EP-Modus): `rentenwert_projiziert` wird mit `rentenanpassung_rate` hochgerechnet.
- `engine.py` Z.79–80 (Euro-Modus): `val_at_rag` wird ebenso projiziert.
- Sidebar-Infobox (Z.148–149) nutzt dieselbe Projektion für die Anzeige.

**Bewertung:** Korrekt implementiert.

---

## K3: Monatsgenaue Regelaltersgrenze ✅ BEHOBEN (korrekt)

**Implementierung:**
- `rentenrecht.py` Z.34–48: `berechne_monate_frueher()` arbeitet mit Dezimaljahren und rechnet in Gesamtmonate um.
- `sidebar.py` Z.93–98: Rentenbeginn wird als `r_jahr + (r_monat - 1) / 12` berechnet.
- `engine.py` Z.303–304: Break-Even nutzt `rag_jahre + rag_monate / 12`.

**Bewertung:** Korrekt. Die Monatspräzision ist durchgängig implementiert.

---

## K4: Doppelzählung Beitragsverlust im Sankey ✅ BEHOBEN (mit Einschränkung)

**Implementierung:**
- `engine.py` Z.99/105: `_calculate_grv_components()` gibt `potential` (= `val_at_rag` dynamisiert) zurück.
- `engine.py` Z.136/193/284: `potential_gesamt` wird aggregiert und ins Ergebnis-Dict geschrieben.
- `app.py` Z.120–141: Sankey-Logik leitet GRV über "Gesetzliche Rente (Potenzial)" → Brutto/Abzüge.

> [!WARNING]
> **Bug in `_calculate_grv_components` Z.99:** Im EP-Modus (Z.61–72) wird `val_at_rag` **nie definiert** – nur `val_base`. Die Variable `val_at_rag` existiert nur im Euro-Modus-Zweig (Z.80). Zeile 99 (`pot_dyn = _dynamisiere_betrag(val_at_rag, ...)`) wird im EP-Modus einen **`NameError: name 'val_at_rag' is not defined`** werfen.
>
> **Fix:** Im EP-Modus muss `val_at_rag = ep_bei_beginn * rentenwert_projiziert` (= `val_base` vor Beitragsverlust-Abzug, also der Wert in Z.68) explizit gesetzt werden. Aktuell wird `val_base` dort direkt zugewiesen, ohne `val_at_rag` zu definieren.

> [!WARNING]
> **Bilanzproblem in `app.py` Z.139:** Die Berechnung des GRV-Brutto-Anteils, der vom Potenzial-Knoten ins Brutto fließt, ist extrem fragil:
> ```python
> add_r("Gesetzliche Rente (Potenzial)", "Brutto", res['Brutto'] - (res['Gehalt'] if 'Gehalt' in res else 0) - sum(...))
> ```
> Diese Zeile versucht, den GRV-Anteil am Brutto durch Subtraktion aller Nicht-GRV-Quellen zu ermitteln. Das funktioniert nur, wenn alle Nicht-GRV-Einnahmen korrekt subtrahiert werden. Bei komplexen Szenarien (mehrere Quellen, Entnahmepläne) kann dies falsche Werte liefern. Besser wäre es, den GRV-Brutto-Anteil direkt aus den Engine-Daten zu nehmen.

---

## K5: Netto-GRV Steuersatz ❌ OFFEN

**Aktueller Code** (`engine.py` Z.253–267):
```python
grv_netto = payout_brutto - kv_grv - pv_grv - (payout_brutto * (tax_rate / 100))
```
`tax_rate` ist der Steuersatz des **Gesamteinkommens** (Z.251). Bei Gesamteinkommen von z.B. 3.500€/mtl. liegt der effektive Steuersatz bei ~20%. Würde man nur die GRV (z.B. 2.000€) isoliert besteuern, läge der Satz bei ~10%. Die Break-Even-Analyse ist dadurch systematisch verzerrt zugunsten der Frührente.

---

## K6: Gehaltsdynamisierung ❌ OFFEN

**Aktueller Code** (`engine.py` Z.140–141):
```python
brutto = params.get('aktuelles_brutto', 0.0)
income_details["Gehalt"] = brutto
```
Keinerlei Steigerung über die Jahre. Das Gehalt bleibt von heute bis zum Renteneintritt konstant.

---

## K7: ATZ-RV-Aufstockung ❌ OFFEN

**Aktueller Code** (`engine.py` Z.155–161):
Die ATZ-Berechnung nutzt `berechne_sv_atz(h_br, ...)`, was identisch zu `berechne_sv_aktiv` ist (Z.96–101). Die gesetzlich vorgeschriebene zusätzliche RV-Aufstockung auf 80% des Vollzeitgehalts durch den AG fehlt. EP-Zuwachs in der ATZ wird dadurch unterschätzt.

---

## Zusammenfassung

| ID | Status | Bewertung |
|----|--------|-----------|
| K1 | ✅ | Sauber implementiert, zvE-Logik durchgängig |
| K2 | ✅ | Rentenwert-Projektion korrekt |
| K3 | ✅ | Monatspräzision durchgängig |
| K4 | ⚠️ | Konzept richtig, aber **Bug im EP-Modus** (`val_at_rag` undefiniert) und **fragile Bilanz-Logik** in app.py |
| K5 | ❌ | Offen – Break-Even nutzt falschen Steuersatz |
| K6 | ❌ | Offen – Gehalt statisch |
| K7 | ❌ | Offen – ATZ-RV-Aufstockung fehlt |

> [!IMPORTANT]
> **Sofort-Fix empfohlen:** Der `val_at_rag`-Bug in K4 (EP-Modus) wird einen Laufzeitfehler erzeugen, sobald ein Nutzer den EP-Eingabemodus wählt. Dies sollte vor dem nächsten Release gefixt werden.
