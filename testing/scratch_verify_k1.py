from logic.taxes import berechne_einkommensteuer, ermittle_zve_naherung
from logic.sozialversicherung import berechne_vorsorgeaufwendungen_steuerlich

print("--- Verifikation K1: zvE-Berechnung (Basis 2025) ---")

# Testcase: 60.000 EUR Brutto (5.000 EUR mtl.)
brutto_mtl = 5000.0
jahr = 2025

# 1. Altes System (Brutto-Basis)
# Wir simulieren den alten Zustand, indem wir die Pauschbeträge auf 0 setzen (virtuell)
steuer_alt = berechne_einkommensteuer(brutto_mtl * 12, jahr)

# 2. Neues System (zvE-Basis)
va_jahr = berechne_vorsorgeaufwendungen_steuerlich(brutto_mtl, jahr, phase="Aktiv")
zve_jahr = ermittle_zve_naherung(brutto_mtl * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va_jahr)
steuer_neu = berechne_einkommensteuer(zve_jahr, jahr)

print(f"Brutto/Jahr: {brutto_mtl*12:,.2f} EUR")
print(f"Vorsorgeaufwendungen (Abzug): {va_jahr:,.2f} EUR")
print(f"zvE (Näherung): {zve_jahr:,.2f} EUR")
print(f"Steuer (ALT - Brutto-Basis): {steuer_alt:,.2f} EUR")
print(f"Steuer (NEU - zvE-Basis):    {steuer_neu:,.2f} EUR")
print(f"Differenz (Entlastung):      {steuer_alt - steuer_neu:,.2f} EUR")

# Vergleich mit BMF (Single, 60k, 2025): ca. 9.800 EUR Lohnsteuer
print(f"\nReferenzwert BMF (Single, 60k, 2025): ca. 9.800 EUR")
abweichung = steuer_neu - 9800
print(f"Abweichung zu BMF: {abweichung:,.2f} EUR ({(abweichung/9800)*100:.1f}%)")
