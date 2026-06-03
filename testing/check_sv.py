#!/usr/bin/env python3
"""Verify SV Rentner calculations."""
from logic.sozialversicherung import berechne_sv_rentner, _get_sv_params, berechne_pv_satz
from logic.engine import calculate_financials_for_year

# 1. Isolierte SV-Berechnung
einnahmen = [
    {"name": "GRV", "betrag": 2200.0, "typ": "Gesetzlich"},
    {"name": "bAV", "betrag": 600.0, "typ": "bAV"},
]
sv = berechne_sv_rentner(einnahmen, 2033, kinderzahl=0)
p = _get_sv_params(2033)
pv = berechne_pv_satz(0, p)
print("=== SV Rentner (GRV=2200, bAV=600, 0 Kinder, 2033) ===")
print(f"SV Gesamt (monatlich): {sv['Gesamt']:.2f} EUR")
print(f"Details: {sv['Details']}")
print(f"KVdR-Satz: {(p['rate_kv_rentner']+p['rate_kv_rentner_zusatz'])*100:.2f}%")
print(f"PV-Satz (0K): {pv*100:.2f}%")
print(f"bAV-Freibetrag: {p['bav_freibetrag_kv']:.2f} EUR")
print(f"Anteil am Brutto: {sv['Gesamt']/2800*100:.1f}%")

# 2. Engine-Integration: Was zeigt die Engine für ein Rentenjahr?
params = {
    "geburtsjahr": 1965,
    "geburtsmonat": 1,
    "aktuelles_jahr": 2026,
    "rentenbeginn": 2032.0,
    "aktuelles_brutto": 6000.0,
    "kinderzahl": 0,
    "kirchensteuer_satz": 0.0,
    "inflation_rate": 0.0,
    "rentenanpassung_rate": 0.0,
    "bav_anpassung_rate": 0.0,
    "gehalts_dynamik": 0.0,
    "atz_simulieren": False,
    "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": 2032.0, "ende": 2060, "eingabe_modus": "euro"},
        {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": 2032.0, "ende": 2060},
    ],
    "ausgaben_kategorien": [],
    "ausgaben_input": {},
    "anpassungsfaktor_input": {},
    "befristete_ausgaben": [],
    "einmalige_ausgaben": [],
}

res = calculate_financials_for_year(2033, params)
print()
print("=== Engine-Ergebnis Jahr 2033 ===")
print(f"Brutto: {res['Brutto']:.2f}")
print(f"Sozialabgaben: {res['Sozialabgaben']:.2f}")
print(f"EkSt: {res['EkSt']:.2f}")
print(f"Soli: {res['Soli']:.2f}")
print(f"Netto: {res['Netto-Einkommen']:.2f}")
print(f"SV-Anteil: {res['Sozialabgaben']/res['Brutto']*100:.1f}%")
print()
# Erwartete Werte
# GRV: KVdR = 2200 * 8.15% = 179.30, PV = 2200 * 2.4% = 52.80 -> 232.10
# bAV: (600 - 187.25) * (14.6%+1.7%) = 412.75 * 16.3% = 67.28
# bAV PV: 412.75 * 4.8% = 19.81
# Total: 232.10 + 87.09 = ~319
# Für 2033 mit fortgeschriebenen Freibeträgen wird es leicht anders sein
print("=== Erwartung (2025er Sätze, ohne BBG-Fortschreibung) ===")
grv_kv = 2200 * 0.0815
grv_pv = 2200 * 0.024
bav_pflichtig = max(0, 600 - 187.25)
bav_kv = bav_pflichtig * 0.163
bav_pv = bav_pflichtig * 0.048
total = grv_kv + grv_pv + bav_kv + bav_pv
print(f"GRV SV: {grv_kv + grv_pv:.2f}")
print(f"bAV SV: {bav_kv + bav_pv:.2f}")
print(f"Total: {total:.2f}")
print(f"SV-Anteil: {total/2800*100:.1f}%")
