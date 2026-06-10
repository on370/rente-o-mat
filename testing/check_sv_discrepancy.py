#!/usr/bin/env python3
"""
Analyse der SV-Diskrepanz: 1941€ (User) vs. 1410€ (R-O-M).
Diff: 531€. Steuerklasse spielt bei SV keine Rolle.

Hypothese: Die 1941€ des Users enthalten auch Kirchensteuer.
Oder: Das SV-pflichtige Brutto ist NICHT 7515 sondern höher.
"""

brutto = 8014.96
eu = 500.0
sv_pflichtig = brutto - eu  # 7514.96

# Was der User als "Sozialabgaben" sieht:
user_sv = 1941.0
user_ekst = 1867.0
user_netto = 4129.0

# Check: Gehen die Zahlen auf?
# Brutto - EkSt - SV - EU = Netto?
netto_check = brutto - user_ekst - user_sv - eu
print(f"Check: {brutto} - {user_ekst} - {user_sv} - {eu} = {netto_check:.2f}")
print(f"User-Netto: {user_netto}")
print(f"Differenz: {netto_check - user_netto:+.2f}")
print()

# Wenn die Summe nicht aufgeht, fehlt ein Posten.
fehlbetrag = user_netto - netto_check
print(f"Es fehlen {fehlbetrag:+.2f}€ in der Rechnung.")
print(f"Das könnte Soli ({0:.0f}€ bei diesem Einkommen) oder")
print(f"Kirchensteuer (9% von {user_ekst:.0f} = {user_ekst * 0.09:.0f}€) sein.")
print()

# Hypothese 1: User hat Kirchensteuer (9%) in die SV eingerechnet
kist_9 = user_ekst * 0.09
print(f"Hypothese 1: KiSt (9%) in 'SV' eingerechnet")
print(f"  KiSt: {kist_9:.0f}€")
print(f"  Echte SV: {user_sv - kist_9:.0f}€")
print(f"  R-O-M SV: 1410€")
print(f"  Rest-Diff: {user_sv - kist_9 - 1410:.0f}€")
print()

# Hypothese 2: KiSt 8%
kist_8 = user_ekst * 0.08
print(f"Hypothese 2: KiSt (8%) in 'SV' eingerechnet")
print(f"  KiSt: {kist_8:.0f}€")
print(f"  Echte SV: {user_sv - kist_8:.0f}€")
print(f"  R-O-M SV: 1410€")
print(f"  Rest-Diff: {user_sv - kist_8 - 1410:.0f}€")
print()

# Hypothese 3: SV wird auf VOLLES Brutto (8015) gerechnet, nicht auf EU-bereinigtes
from logic.sozialversicherung import berechne_sv_aktiv
sv_voll = berechne_sv_aktiv(brutto, 2026, 1)
print(f"Hypothese 3: SV auf volles Brutto ({brutto}€)")
print(f"  SV (volles Brutto): {sv_voll['Gesamt']:.2f}€")
print(f"  Diff zu User: {user_sv - sv_voll['Gesamt']:+.2f}€")
print()

# Tatsächlich: EU aus Entgeltumwandlung ist normalerweise SV-FREI bis 4% der BBG RV.
# 4% BBG RV 2026 = 4% * 101.400 = 4.056 € / Jahr = 338 € / Monat
# Darüber hinaus SV-PFLICHTIG!
# Die 500€ EU sind also teilweise SV-frei und teilweise SV-pflichtig!
bbg_rv_jahr = 8450.0 * 12  # = 101.400
sv_frei_eu = bbg_rv_jahr * 0.04 / 12  # = 338 € monatlich
sv_pflichtig_eu = max(0, eu - sv_frei_eu)  # = 162 € monatlich
print(f"Hypothese 4: EU nur bis 4% BBG RV SV-frei!")
print(f"  4% BBG RV: {sv_frei_eu:.0f}€/mtl. SV-frei")
print(f"  EU: {eu:.0f}€")
print(f"  Davon SV-pflichtig: {sv_pflichtig_eu:.0f}€")
print(f"  SV-pflichtiges Brutto: {brutto - sv_frei_eu:.2f}€")
sv_korrekt = berechne_sv_aktiv(brutto - sv_frei_eu, 2026, 1)
print(f"  SV auf korrektes Brutto: {sv_korrekt['Gesamt']:.2f}€")
print(f"  Diff zu User: {user_sv - sv_korrekt['Gesamt']:+.2f}€")
print()

# Die EU ist auch steuerlich begrenzt: 8% BBG RV (§ 3 Nr. 63 EStG)
steuer_frei_eu = bbg_rv_jahr * 0.08 / 12  # = 676 €/mtl
print(f"Steuerbefreiung EU: 8% BBG RV = {steuer_frei_eu:.0f}€/mtl -> 500€ voll steuerfrei ✓")

print("\n" + "=" * 70)
print("GESAMTANALYSE")
print("=" * 70)
# Wenn wir Hyp 3 (SV auf 8015) + KiSt annehmen:
sv_auf_voll = sv_voll['Gesamt']
kist = user_ekst * 0.09  # geschätzt
print(f"Wahrscheinlichstes Szenario:")
print(f"  SV auf volles Brutto {brutto}€: {sv_auf_voll:.0f}€")
print(f"  + KiSt (ca. 9%): {kist:.0f}€")  
print(f"  = Summe: {sv_auf_voll + kist:.0f}€")
print(f"  User hat: {user_sv:.0f}€")
print(f"  Verbleibende Diff: {user_sv - sv_auf_voll - kist:.0f}€")
