#!/usr/bin/env python3
from logic.sozialversicherung import berechne_sv_aktiv, berechne_vorsorgeaufwendungen_steuerlich
from logic.taxes import ermittle_zve_naherung, berechne_einkommensteuer

brutto_st = 8014.96 - 500  # 7514.96
jahr = 2026
kinder = 1

sv = berechne_sv_aktiv(brutto_st, jahr, kinder)
print(f"SV auf {brutto_st:.2f}: {sv['Gesamt']:.2f}")

va = berechne_vorsorgeaufwendungen_steuerlich(brutto_st, jahr, phase="Aktiv")
zve = ermittle_zve_naherung(brutto_st * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va)
tax = berechne_einkommensteuer(zve, jahr) / 12
print(f"Tax auf {brutto_st:.2f}: {tax:.2f}")
print(f"Netto: {brutto_st - sv['Gesamt'] - tax:.2f}")
