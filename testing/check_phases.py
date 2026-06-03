#!/usr/bin/env python3
"""Compare SV across phases."""
from logic.engine import calculate_financials_for_year

params = {
    "geburtsjahr": 1965, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2032.0,
    "aktuelles_brutto": 6000.0, "kinderzahl": 0,
    "kirchensteuer_satz": 0.0, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 1.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": 2032.0, "ende": 2060, "eingabe_modus": "euro"},
        {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": 2032.0, "ende": 2060},
    ],
    "ausgaben_kategorien": ["Wohnen", "Sonstiges"],
    "ausgaben_input": {"Wohnen": 1200.0, "Sonstiges": 200.0},
    "anpassungsfaktor_input": {"Wohnen": 100, "Sonstiges": 100},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
}

print(f"{'Jahr':>5} {'Phase':>6} {'Brutto':>7} {'SV':>7} {'SV%':>5} {'EkSt':>7} {'Netto':>7}")
print("-" * 55)
for j in [2026, 2031, 2033, 2040, 2050]:
    res = calculate_financials_for_year(j + 0.5, params)
    brutto = res["Brutto"]
    sv = res["Sozialabgaben"]
    sv_pct = sv / max(1, brutto) * 100
    print(f"{j:>5} {res['Phase']:>6} {brutto:>7.0f} {sv:>7.0f} {sv_pct:>4.1f}% {res['EkSt']:>7.0f} {res['Netto-Einkommen']:>7.0f}")
