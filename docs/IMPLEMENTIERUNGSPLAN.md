# Rente-O-Mat: Implementierungsplan – Vom Prototyp zum Präzisions-Tool

## Ziel

Alle in `ANALYSE.md` identifizierten Probleme beheben: kritische Bugs fixen, fachlich falsche Berechnungen korrigieren, fehlende Features für eine glaubwürdige Finanzplanung ergänzen.

---

## Offene Fragen an den User (vor Umsetzung klären)

1. **Kirchensteuer** einbauen (Checkbox + Bundesland 8%/9%)? Oder erstmal weglassen?
2. **Ehegattensplitting** mit Partner-Einkommen? (Fachlich korrekt, aber erhöht UI-Komplexität)
3. **GKV vs. PKV** als Option? (Fixer PKV-Beitrag statt prozentualer KVdR)
4. **Inflationsmodell:** Ein globaler Regler oder getrennte Raten (Ausgaben / GRV / bAV / Kapital)?
5. **Scope:** Nur Phase 1+2 (Bugs + Korrektheit) oder auch Phase 3 (Rentenabschläge, Entgeltpunkte)?
6. **JSON Breaking Change:** Versionskennung ins Export-Format aufnehmen?

---

## Phase 1: Quick Wins (< 1 Stunde)

### `app.py`
- **K3-Fix:** `elif res['Phase'] == "ATZ":` → `elif res['Phase'] in ["ATZ(A)", "ATZ(P)"]:`

### `ui/sidebar.py`
- **M4:** `aktuelles_jahr = 2026` → `aktuelles_jahr = datetime.now().year`
- **M5:** Default-Rentenbeginn: `geburtsjahr + 67` statt hardcoded `2031`

### Neue Dateien
- `logic/__init__.py` (leer)
- `ui/__init__.py` (leer)
- `data/__init__.py` (leer)
- `requirements.txt` mit `streamlit>=1.30`, `pandas>=2.0`, `plotly>=5.18`

---

## Phase 2: Fachliche Korrektheit (Steuer, SV, Rente)

### `logic/taxes.py` – Kompletter Umbau

1. **K1:** EkSt-Tarif als Funktion mit Tarifjahr-Parameter:
   - 2024: Grundfreibetrag 11.604 €
   - 2025+: Grundfreibetrag 12.096 €
   - Zukunft: letzten bekannten Tarif fortschreiben

2. **H3:** `berechne_soli(steuer, splitting=False)` – 5,5% ab 18.130 € (Single) / 36.260 € (Splitting)

3. **H4:** `berechne_kirchensteuer(steuer, satz)` – 0 / 8% / 9% als Option

4. **H5:** `berechne_einkommensteuer_splitting(einkommen_gesamt)` – Splittingtarif § 32a Abs. 5 EStG

5. **H7:** `berechne_ertragsanteil(alter_bei_rentenbeginn)` – Lookup-Tabelle statt pauschal 18%

6. **H8:** `berechne_abgeltungssteuer(kapitalertraege, sparerpauschbetrag, soli, kist_satz)` – 25% + Soli + KiSt

### Neues Modul: `logic/sozialversicherung.py`

1. **K2:** BBG und Beitragssätze als Tabelle nach Jahr (2024–2026, Fortschreibung mit ~3%/Jahr):

```python
SV_TABELLE = {
    2024: {"bbg_kv": 5175.0, "bbg_rv": 7550.0, "rate_kv": 0.0815, ...},
    2025: {"bbg_kv": 5512.5, "bbg_rv": 8050.0, ...},
    2026: {...},
}
```

2. **H6:** Differenzierte SV-Funktionen:
   - `berechne_sv_aktiv(brutto, jahr)` – AN-Anteile KV/PV/RV/ALV
   - `berechne_sv_rentner(einnahmen_dict, jahr, kinderzahl)`:
     - GRV → KVdR-Beitrag (~16,3% auf GRV-Betrag)
     - bAV → voller KV+PV-Satz (AN+AG) oberhalb Freibetrag (176,75 €/2024)
     - Privat → kein KVdR-Beitrag (nur bei freiwillig GKV-Versicherten)
   - `berechne_sv_atz(halbes_brutto, jahr)` – SV nur auf hälftiges Brutto
   - `berechne_pv_satz(kinderzahl)` – gestaffelt: 0 Kinder: 4,0%, 1: 3,4%, 2: 3,15% usw.

### `logic/engine.py` – Kernänderungen

1. **K4:** bAV → `st_b += val * 1.0` (100% steuerpflichtig)
2. **H7:** Ertragsanteil-Lookup statt `0.18`
3. **H8:** Kapitalerträge → Abgeltungssteuer-Logik
4. SV-Berechnung auf `sozialversicherung.py` umstellen
5. **H1/H2:** Dynamisierungslogik einbauen:
   - Ausgaben × `(1 + inflation_rate) ** (jahr - aktuelles_jahr)`
   - GRV × `(1 + rentenanpassung_rate) ** (jahr - rentenbeginn)`
   - bAV × `(1 + bav_anpassung_rate) ** (jahr - rentenbeginn)`
6. Soli + KiSt in Steuerberechnung integrieren
7. **M8:** `df.fillna(0)` nach `generate_trend_data`

### `ui/sidebar.py` – Neue Eingaben

**Profil-Erweiterung:**
- Familienstand (Single / Verheiratet) → steuert Splitting
- Kinderzahl → steuert PV-Satz
- Kirchensteuer (Keine / 8% / 9%)

**Neuer Expander „⚙️ Annahmen":**
- Inflationsrate (Slider 0–5%, Default 2%)
- GRV-Rentenanpassung p.a. (Slider 0–5%, Default 2%)
- bAV-Anpassung p.a. (Slider 0–3%, Default 1%)

**M3 – Sidebar-Reihenfolge:**
Profil → Meilensteine → Finanzen Aktuell → Einnahmequellen → Haushaltsbuch → Annahmen → Zeitstrahl

**M7 – Eingabevalidierung:**
- Rentenbeginn > aktuelles Jahr
- ATZ-Start ≥ aktuelles Jahr
- Einnahmen: Ende ≥ Start, Betrag ≥ 0
- Geburtsjahr: 1940–2010

### `ui/charts.py` – Erweiterungen

1. **M6:** Neue Funktion `create_wealth_chart(df, startvermögen, rendite)`:
   - Kumulative Linie: Startvermögen + Σ(Überschuss/Defizit × 12) × (1 + rendite)
   - Rote Linie bei 0 → zeigt „Pleite-Jahr"
2. Sankey: Soli und KiSt als eigene Knoten (wenn > 0)
3. Trend-Chart: Netto-Einkommen als zusätzliche gestrichelte Linie

### `app.py` – Erweiterungen

1. Neuer Tab „💰 Vermögensentwicklung" mit `create_wealth_chart`
2. Kennzahlen-Header: `st.metric` Cards für Brutto / Netto / Steuersatz / Überschuss
3. Sankey um Soli/KiSt-Knoten erweitern

---

## Phase 3: UX & PRD-Ergänzungen

### `logic/engine.py`
- **N4:** Rentenabschläge/-zuschläge:
  - Regelaltersgrenze Monate − tatsächlicher Rentenbeginn Monate × 0,3% (max. −14,4%)
  - Zuschlag bei Überschreitung: +0,5%/Monat
- **N5:** GRV-Betrag alternativ aus Entgeltpunkten: `EP × aktueller_rentenwert × abschlag_faktor`

### `ui/sidebar.py`
- Einnahmen-Editor: Option „Aus Entgeltpunkten berechnen" für GRV-Typ
- Neuer Einnahmen-Typ: „Einmalzahlung" mit Jahr + Betrag (für Abfindung, LV-Auszahlung etc.)
- Startvermögen + Rendite als Eingabe im Annahmen-Expander

### `data/persistence.py`
- Versions-Tag: `"version": "2.0"` im JSON
- Import: fehlende Felder mit Defaults auffüllen (Rückwärtskompatibilität)

---

## Phase 4: Premium-Features (Langfristig)

- **N3:** Szenario-Vergleich (Side-by-Side Charts für 2 Konfigurationen)
- **N6:** Hinterbliebenenabsicherung (Witwenrente 60%, Anrechnung)
- **N8:** PDF-Report-Export (Plotly → Kaleido → PDF)
- **N9:** Sensitivitätsanalyse (Best/Worst/Base-Case)
- **N10:** GKV/PKV-Unterscheidung (fixer PKV-Beitrag im Alter)

---

## Verifikationsplan

### Unit-Tests (neu: `tests/test_taxes.py`, `tests/test_sv.py`)

```
EkSt 2025, ZVE=0        → 0,00 €
EkSt 2025, ZVE=30.000   → ~4.780 € (2025-Tarif)
EkSt 2025, ZVE=100.000  → ~30.780 €
Splitting 100.000        → ~21.328 € (2 × EkSt(50.000))
Soli auf 20.000 EkSt     → 1.100 €
bAV 600 €/Monat         → 100% steuerpflichtig (7.200 €/Jahr in ZVE)
Ertragsanteil Alter 63   → 20%
BBG RV 2026             → plausibel > 8.050 €
```

### Manuelle Tests

1. App starten: `streamlit run app.py`
2. ATZ aktivieren → Sankey prüfen: ATZ-Gehalt + Aufstockung als separate Knoten
3. Inflations-Slider auf 3% → Ausgaben im Trend-Chart müssen sichtbar steigen
4. JSON Export → Import Roundtrip → alle Werte identisch
5. Ergebnisse mit BMF-Steuerrechner (www.bmf-steuerrechner.de) abgleichen
