#!/usr/bin/env python3
"""Detailprüfung: SV auf bAV-EZ läuft sie nach 10J aus?"""
from logic.engine import calculate_financials_for_year

params = {
    "geburtsjahr": 1966, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2031.0 + 1/12,
    "aktuelles_brutto": 8000.0, "kinderzahl": 1,
    "kirchensteuer_satz": 0.0, "inflation_rate": 0.0,  # keine Inflation für klare Zahlen
    "rentenanpassung_rate": 0.0, "bav_anpassung_rate": 0.0,
    "gehalts_dynamik": 0.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2400.0, "typ": "Gesetzlich",
         "start": 2031.0 + 1/12, "ende": 2070, "eingabe_modus": "euro"},
        {"name": "bAV Kapital", "betrag": 80000.0, "typ": "bAV (Einmalzahlung)",
         "start": 2031.0 + 1/12, "reinvest_target": "global"},
    ],
    "ausgaben_kategorien": [],
    "ausgaben_input": {},
    "anpassungsfaktor_input": {},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
}

# SV ohne bAV-EZ (nur GRV)
params_only_grv = params.copy()
params_only_grv["einnahmen"] = [params["einnahmen"][0]]

print(f"{'Jahr':>5} {'SV m/EZ':>10} {'SV o/EZ':>10} {'Diff':>8}  Kommentar")
print("-" * 55)
for j in range(2031, 2045):
    res_with = calculate_financials_for_year(j + 0.5, params)
    res_without = calculate_financials_for_year(j + 0.5, params_only_grv)
    diff = res_with["Sozialabgaben"] - res_without["Sozialabgaben"]
    
    # bAV-EZ SV-Zeitraum: start bis start+10
    start_ez = 2031.0 + 1/12
    in_sv_window = j + 0.5 >= start_ez and j + 0.5 < start_ez + 10
    
    comment = "SV auf bAV-EZ aktiv" if diff > 1 else "KEINE bAV-SV"
    expected = "✅" if (diff > 1) == in_sv_window else "⚠️ FALSCH"
    print(f"{j:>5} {res_with['Sozialabgaben']:>10.2f} {res_without['Sozialabgaben']:>10.2f} {diff:>+8.2f}  {comment} {expected}")
