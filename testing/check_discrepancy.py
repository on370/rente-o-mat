#!/usr/bin/env python3
import math
from logic.engine import calculate_financials_for_year
from logic.taxes import berechne_einkommensteuer, ermittle_zve_naherung
from logic.sozialversicherung import berechne_sv_aktiv, berechne_vorsorgeaufwendungen_steuerlich

brutto = 8014.96
jahr = 2026
kinder = 1

# SV berechnen
sv = berechne_sv_aktiv(brutto, jahr, kinder)
print(f"SV für Brutto {brutto}:")
print(f"  KV:  {sv['KV']:.2f}")
print(f"  PV:  {sv['PV']:.2f}")
print(f"  RV:  {sv['RV']:.2f}")
print(f"  ALV: {sv['ALV']:.2f}")
print(f"  Sum: {sv['Gesamt']:.2f}")

# EkSt berechnen
va = berechne_vorsorgeaufwendungen_steuerlich(brutto, jahr, phase="Aktiv")
zve = ermittle_zve_naherung(brutto * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va)
ekst_jahr = berechne_einkommensteuer(zve, jahr)
ekst_monat = ekst_jahr / 12

print(f"\nEkSt für Brutto {brutto}:")
print(f"  ZV-Einkommen: {zve:.2f}")
print(f"  Steuer/Jahr:  {ekst_jahr:.2f}")
print(f"  Steuer/Monat: {ekst_monat:.2f}")
print(f"  Netto normal: {brutto - sv['Gesamt'] - ekst_monat:.2f}")

