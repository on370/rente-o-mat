"""Analyse der EkSt-Tarifparameter"""
import sys
sys.path.insert(0, '.')

from logic.taxes import _get_tarif, berechne_einkommensteuer

t = _get_tarif(2025)
print("2025 Tarifparameter:")
for k, v in t.items():
    print(f"  {k}: {v}")

# Teste Zone 2 manuell bei X=17443 (Ende Zone 2):
X = 17443
y = (X - t["grundfreibetrag"]) / 10000
ekst_z2_ende = (t["zone2_a"] * y + t["zone2_b"]) * y
print(f"\nZone 2 Ende (X={X}):")
print(f"  y = ({X} - {t['grundfreibetrag']}) / 10000 = {y}")
print(f"  EkSt = ({t['zone2_a']} * {y} + {t['zone2_b']}) * {y} = {ekst_z2_ende:.2f}")
print(f"  zone3_c (sollte = EkSt Zone2 Ende) = {t['zone3_c']}")

# BMF offizielles Ergebnis für 17443 zvE (2025): 
# Prüfen wir mit dem offiziellen Tarif
# Laut Steueränderungsgesetz 2024 (Inflation compensation):
# Grundfreibetrag 2025: 12.096 EUR (bestätigt)
# Zone 2 (12.096 - 17.443):
#   y = (zvE - 12.096) / 10.000
#   ESt = (932,30 · y + 1.400) · y
# Zone 3 (17.443 - 66.760):
#   z = (zvE - 17.443) / 10.000
#   ESt = (181,19 · z + 2.397) · z + 991,21

# ABER: Die Gesetz-Fassung sagt 991,21 als zone3_c.
# Engine hat zone3_c = 991.21 - das stimmt!
# BMF-Rechner gibt aber ~1182 für 17.443 zvE.
# Das kann nicht sein, wenn zone3_c = EkSt(zone2_ende) = 991,21

# ODER: BMF-Rechner rechnet GERUNDET.
# Nochmal: BMF Grundtabelle 2025, zvE = 17.443:
# y = (17443 - 12096) / 10000 = 0.5347
# EkSt = (932.30 * 0.5347 + 1400) * 0.5347
#       = (498.50 + 1400) * 0.5347
#       = 1898.50 * 0.5347
#       = 1015.13
# -> Engine ergibt 1015.13, was korrekt nach Formel ist.

# Wenn BMF 1182 EUR sagt, dann muss der BMF andere Parameter verwenden.
# WAIT: Ich muss meine Erwartungswerte überprüfen! Die BMF-Steuerrechner-Referenzwerte
# im Audit könnten falsch sein. Lass mich die offiziellen §32a Werte 2025 nochmal genau prüfen.

# §32a Abs. 1 EStG i.d.F. Steuerfortentwicklungsgesetz (2025):
# Grundfreibetrag: 12.084 EUR (NICHT 12.096!)
# KORREKTUR: Es gibt ZWEI Änderungen für 2025:
# 1. Inflationsausgleichsgesetz 2025: GFB = 12.084 
# 2. Steuerfortentwicklungsgesetz 2025: GFB = 12.096 (rückwirkend zum 1.1.2025)

# Die hier verwendeten Parameter (GFB=12096) entsprechen dem SteF:
# https://www.buzer.de/32a_EStG.htm
# §32a (1) S. 2 Nr. 1: bis 12.096 EUR -> Zone 1 (steuerfrei)
# Nr. 2: 12.097 bis 17.443: y=(X-12096)/10000, (922,98·y + 1.400)·y
#   MOMENT: 922,98 ist der 2024er Koeffizient!
# Nr. 3: 17.444 bis 66.760: z=(X-17443)/10000, (181,19·z + 2.397)·z + 1.015,13
# Nr. 4: 66.761 bis 277.825: 0,42·X - 10.636,31
# Nr. 5: ab 277.826: 0,45·X - 18.971,06

# Hm, lass mich prüfen welche Parameter TATSÄCHLICH gelten:
# Die Engine hat zone2_a = 932.30, der §32a Nr. 2 sagt 922,98
# UND zone3_c = 991.21, der §32a Nr. 3 sagt 1.015,13

# Also: Die Engine-Parameter für 2025 sind INKORREKT!
# zone2_a sollte 922.98 sein (nicht 932.30)
# zone3_c sollte 1015.13 sein (nicht 991.21)

print("\n=== DIAGNOSE ===")
print("Die Engine-Parameter für 2025 weichen vom Gesetzestext ab!")
print(f"  zone2_a: Engine={t['zone2_a']}, Gesetz=922.98 (§32a Nr. 2 SteF)")
print(f"  zone3_c: Engine={t['zone3_c']}, Gesetz=1015.13 (§32a Nr. 3 SteF)")
print()

# Prüfen: Was wäre mit korrekten Parametern?
# 30k zvE, Zone 3:
z = (30000 - 17443) / 10000
ekst_korrekt = (181.19 * z + 2397) * z + 1015.13
ekst_engine = berechne_einkommensteuer(30000, 2025)
print(f"30k zvE mit korrekten §32a Params: {ekst_korrekt:.2f}")
print(f"30k zvE Engine: {ekst_engine:.2f}")

# Prüfe noch die 2024er Werte
# §32a 2024:
# Nr. 2: y=(X-11604)/10000, (922,98·y + 1.400)·y
# Nr. 3: z=(X-17005)/10000, (181,19·z + 2.397)·z + 1.025,38
# Die Engine hat: zone2_a=922.98, zone3_c=1025.38 -> das stimmt für 2024!
t24 = _get_tarif(2024)
print(f"\n2024: zone2_a={t24['zone2_a']} (soll 922.98) -> {'✅' if t24['zone2_a']==922.98 else '❌'}")
print(f"2024: zone3_c={t24['zone3_c']} (soll 1025.38) -> {'✅' if t24['zone3_c']==1025.38 else '❌'}")

# Fazit: Die 2025er Tarifparameter (zone2_a, zone3_c, möglicherweise zone2_b) sind falsch.
# Die 2024er sind korrekt.

# Nochmal Zone 2 für 2025 mit KORREKTEM zone2_a = 922.98:
y_test = (17443 - 12096) / 10000
ekst_z2_korrekt = (922.98 * y_test + 1400) * y_test
print(f"\nZone2 Ende (17443) mit zone2_a=922.98: {ekst_z2_korrekt:.2f}")
print(f"Zone2 Ende (17443) mit zone2_a=932.30: {ekst_z2_ende:.2f}")
print(f"Gesetz zone3_c = 1015.13 -> sollte identisch mit Zone2 Ende sein")
print(f"Differenz: {abs(ekst_z2_korrekt - 1015.13):.4f}")

# FAZIT:
# Die zone3_c = 1015.13 im Gesetz ist = EkSt(zone2_ende) MIT zone2_a = 922.98
# Die Engine hat FÄLSCHLICHERWEISE zone2_a auf 932.30 gesetzt, 
# was den gesamten Tarif ab Zone 2 verfälscht.
print("\n=== LÖSUNG ===")
print("Korrektur in taxes.py TARIF_PARAMETER[2025]:")
print('  zone2_a: 922.98 (nicht 932.30)')
print('  zone3_c: 1015.13 (nicht 991.21)')
print("  zone4_abzug: prüfen!")
print("  zone5_abzug: prüfen!")

# Berechne korrekte zone4_abzug und zone5_abzug
# Zone 4 beginnt bei 66760: 0.42 * X - abzug = EkSt(66760)
z_66760 = (66760 - 17443) / 10000
ekst_66760 = (181.19 * z_66760 + 2397) * z_66760 + 1015.13
zone4_abzug_korrekt = 0.42 * 66760 - ekst_66760
print(f"\nzone4: EkSt(66760) = {ekst_66760:.2f}")
print(f"zone4_abzug = 0.42 * 66760 - {ekst_66760:.2f} = {zone4_abzug_korrekt:.2f}")
print(f"Engine hat: {t['zone4_abzug']}")

# Zone 5 beginnt bei 277825: 0.45 * X - abzug = EkSt(277825)
ekst_277825 = 0.42 * 277825 - zone4_abzug_korrekt
zone5_abzug_korrekt = 0.45 * 277825 - ekst_277825
print(f"\nzone5: EkSt(277825) = {ekst_277825:.2f}")
print(f"zone5_abzug = 0.45 * 277825 - {ekst_277825:.2f} = {zone5_abzug_korrekt:.2f}")
print(f"Engine hat: {t['zone5_abzug']}")
