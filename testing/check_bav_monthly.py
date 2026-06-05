#!/usr/bin/env python3
"""
Kritische Prüfung bAV-Einmalzahlung: 
Wird der Bruttobetrag korrekt als MONATLICHER Wert in b_g addiert?
"""
from logic.engine import calculate_financials_for_year

# Minimales Szenario: NUR bAV-EZ, keine GRV
params = {
    "geburtsjahr": 1966, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2031.0,
    "aktuelles_brutto": 8000.0, "kinderzahl": 0,
    "kirchensteuer_satz": 0.0, "inflation_rate": 0.0,
    "rentenanpassung_rate": 0.0, "bav_anpassung_rate": 0.0,
    "gehalts_dynamik": 0.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "bAV Kapital", "betrag": 60000.0, "typ": "bAV (Einmalzahlung)",
         "start": 2031.0, "reinvest_target": "global"},
    ],
    "ausgaben_kategorien": [],
    "ausgaben_input": {},
    "anpassungsfaktor_input": {},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
}

print("=== Test: bAV-EZ 60.000€ bei Rentenbeginn 2031.0 ===")
res = calculate_financials_for_year(2031.5, params)
print(f"Phase: {res['Phase']}")
print(f"Brutto: {res['Brutto']:,.2f}")
print(f"EkSt: {res['EkSt']:,.2f}")
print(f"Netto: {res['Netto-Einkommen']:,.2f}")
print(f"Kapitalzuwachs_Sonder: {res.get('Kapitalzuwachs_Sonder', 0):,.2f}")
print()

# PROBLEM: b_g ist hier offenbar 60.000 + 0 (keine anderen Einnahmen)
# Das ist der VOLLE Jahresbetrag in der monatlichen Variable b_g!
# Zeile 335: b_g += ez  -- aber b_g ist MONATLICH, ez ist JÄHRLICH/EINMALIG
# Das bedeutet: Überschuss/Defizit = netto - ausgaben, wobei netto die 60k enthält
# -> Die 60k werden als "monatlich" interpretiert -> Bug!

print("ANALYSE:")
print(f"  b_g = {res['Brutto']:,.2f}")
print(f"  -> Das ist der EZ-Betrag ({60000}) + normale Rente (0)")
print(f"  -> b_g ist eine MONATLICHE Variable!")
print(f"  -> 60.000€ werden als monatliches Einkommen behandelt")
print()
print(f"  Überschuss/Defizit: {res['Überschuss/Defizit']:,.2f}")
print(f"  -> Das ist 'Netto-Einkommen' - 'Bedarf'")
print()

# Vergleich mit OHNE bAV-EZ
params_no_ez = params.copy()
params_no_ez["einnahmen"] = []
res_no = calculate_financials_for_year(2031.5, params_no_ez)
print(f"  Ohne bAV-EZ: Netto={res_no['Netto-Einkommen']:,.2f}")
print()

# Die Frage ist: Wird das in generate_trend_data korrekt behandelt?
# Zeile 733: netto_einmalzahlung_jahr = res.get("Kapitalzuwachs_Sonder", 0.0)
# Das wird vom Überschuss abgezogen, damit nur der "laufende" Saldo reinvestiert wird
# Die 56.880 netto fließen dann separat über _debug_Sonderzuwachs_Details ins Asset
# -> Die Logik ist KORREKT, aber die DARSTELLUNG im Sankey/Tabelle zeigt das EZ
#    als monatliches Brutto, was verwirrend ist
print("FAZIT: Die Reinvestitions-LOGIK ist korrekt (separater Kanal).")
print("       Die DARSTELLUNG (Brutto-Wert) ist irreführend, da die EZ")
print("       als monatlicher Brutto-Wert angezeigt wird.")
