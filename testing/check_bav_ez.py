#!/usr/bin/env python3
"""Test bAV Einmalzahlung: Steuer, SV, Reinvestition."""
from logic.engine import calculate_financials_for_year, generate_trend_data
import pandas as pd

print("=" * 70)
print("TEST: bAV Einmalzahlung")
print("=" * 70)

# Szenario: 80.000€ bAV-Einmalzahlung bei Rentenbeginn 2031
params = {
    "geburtsjahr": 1966, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2031.0 + 1/12,
    "aktuelles_brutto": 8000.0, "kinderzahl": 1,
    "kirchensteuer_satz": 0.0, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 0.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2400.0, "typ": "Gesetzlich",
         "start": 2031.0 + 1/12, "ende": 2070, "eingabe_modus": "euro"},
        {"name": "bAV Kapital", "betrag": 80000.0, "typ": "bAV (Einmalzahlung)",
         "start": 2031.0 + 1/12, "reinvest_target": "global"},
    ],
    "ausgaben_kategorien": ["Wohnen"],
    "ausgaben_input": {"Wohnen": 1500},
    "anpassungsfaktor_input": {"Wohnen": 100},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
    "assets": [
        {"name": "ETF-Depot", "startwert": 100000, "rendite_pa": 5.0,
         "steuertyp": "teilfreistellung", "teilfreistellung_pct": 30.0,
         "entnahme_aktiv": False},
    ],
    "entnahme_strategie": "Manuell (Keine Automatik)",
    "reinvest_target": "ETF-Depot",
    "liquidity_reserve": 10000.0,
    "liquidity_yield": 2.0,
}

# Test 1: Engine-Berechnung im Auszahlungsjahr
print("\n--- Test 1: Engine im Auszahlungsjahr (2031) ---")
# Statt jahr_float = 2031 + 0.5, müssen wir den Zeitpunkt so wählen,
# dass er im richtigen Segment liegt (nach Rentenbeginn)
res = calculate_financials_for_year(2031 + 0.5, params)
print(f"Phase: {res['Phase']}")
print(f"Brutto: {res['Brutto']:,.2f}")
print(f"Kapitalzuwachs_Sonder: {res.get('Kapitalzuwachs_Sonder', 0):,.2f}")
print(f"Sonderzuwachs Details: {res.get('_debug_Sonderzuwachs_Details', [])}")
print(f"Netto: {res['Netto-Einkommen']:,.2f}")

# Test 2: generate_trend_data - prüfen ob das Kapital korrekt reinvestiert wird
print("\n--- Test 2: Trendanalyse (Reinvestition der EZ) ---")
jahre = list(range(2026, 2045))
df = generate_trend_data(jahre, params)

# Zeige relevante Jahre
for j in [2030, 2031, 2032, 2033]:
    rows = df[df["Jahr"] == j]
    for _, row in rows.iterrows():
        print(f"Jahr {j} ({row.get('Label', '?')}): "
              f"Phase={row['Phase']}, "
              f"Brutto={row['Brutto']:,.0f}, "
              f"Sonder={row.get('Kapitalzuwachs_Sonder', 0):,.0f}, "
              f"ETF={row.get('ASSET_VAL_ETF-Depot', 0):,.0f}, "
              f"Cash={row.get('ASSET_VAL_Cash-Reserven (kum.)', 0):,.0f}")

# Test 3: SV-Behandlung der Einmalzahlung
# bAV-Einmalzahlungen werden über 10 Jahre (120 Monate) auf die SV verteilt
print("\n--- Test 3: SV auf Einmalzahlung ---")
# Betrag pro Monat für SV: 80.000 / 120 = 666,67€
sv_betrag_mtl = 80000 / 120
print(f"SV-Basis/mtl für bAV-EZ: {sv_betrag_mtl:.2f} (über 10 Jahre)")

# Prüfe: Wird die SV-Verteilung korrekt in sv_einnahmen_bav_ez aufgenommen?
# Im Jahr 2035 (4 Jahre nach Start) sollte die SV noch laufen
# Im Jahr 2042 (11 Jahre nach Start) sollte sie NICHT mehr laufen
for test_j in [2031, 2035, 2041, 2042]:
    res_test = calculate_financials_for_year(test_j + 0.5, params)
    print(f"  Jahr {test_j}: SV={res_test['Sozialabgaben']:,.2f}, Phase={res_test['Phase']}")

# Test 4: Fünftelregelung auf die Einmalzahlung
print("\n--- Test 4: Fünftelregelung ---")
from logic.taxes import berechne_fuenftelregelung, berechne_einkommensteuer, ermittle_zve_naherung
# Normales Renteneinkommen: GRV 2400€ -> steuerpflichtig: ~86,5% (RB 2031) = 2076€/mtl = 24912€/J
# zvE ≈ 24912 - Werbungskosten - Sonderausgaben - Vorsorge
# Fünftelregelung auf 80.000€
steuer_normal = berechne_einkommensteuer(24912, 2031)
steuer_5tel = berechne_fuenftelregelung(24912, 80000, 2031)
print(f"Steuer auf laufende Einkünfte (zvE ~24912): {steuer_normal:,.0f}")
print(f"Zusatzsteuer Fünftelregelung auf 80.000€: {steuer_5tel:,.0f}")
print(f"Effektiver Steuersatz EZ: {steuer_5tel / 80000 * 100:.1f}%")
print(f"Netto nach Steuer: {80000 - steuer_5tel:,.0f}")
