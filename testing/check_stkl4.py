#!/usr/bin/env python3
"""
Prüfung: StKl 4 mit 0.5 Kinderfreibetrag.
StKl 4 = Grundtarif (identisch zu StKl 1).
Kinderfreibetrag beeinflusst NUR Soli und KiSt, NICHT die EkSt selbst.
(Bei der EkSt gibt es die Günstigerprüfung KiFB vs. Kindergeld am Jahresende.)

Frage: Erklärt der KiFB die 514€ Differenz? -> Nein, unmöglich.
KiFB 2026: 9.312€ pro Kind -> 0.5 KiFB = 4.656€
Effekt auf Soli: maximal ~15€/mtl.
Effekt auf KiSt: maximal ~30€/mtl.
-> Zusammen max. 45€, nicht 514€.

Also: Die 1.867€ auf dem Gehaltszettel müssen noch etwas anderes enthalten.
"""
from logic.taxes import berechne_einkommensteuer, ermittle_zve_naherung, berechne_soli, berechne_kirchensteuer
from logic.sozialversicherung import berechne_vorsorgeaufwendungen_steuerlich

brutto = 8014.96
eu = 500.0
brutto_st = brutto - eu  # 7514.96

# R-O-M Berechnung (StKl 4 = Grundtarif)
va = berechne_vorsorgeaufwendungen_steuerlich(brutto_st, 2026, phase="Aktiv")
zve = ermittle_zve_naherung(brutto_st * 12, 2026, phase="Aktiv", vorsorgeaufwendungen_jahr=va)
ekst_jahr = berechne_einkommensteuer(zve, 2026)
ekst_monat = ekst_jahr / 12

# Soli (ohne KiFB)
soli_ohne = berechne_soli(ekst_jahr, jahr=2026) / 12

# Soli (mit 0.5 KiFB = 4656€ Abzug von der Soli-Bemessungsgrundlage)
# KiFB 2026: 6.612€ Freibetrag + 2.700€ BEA-Freibetrag = 9.312€ pro Kind
# 0.5 KiFB = 4.656€
kifb = 4656
zve_soli = max(0, zve - kifb)
ekst_soli = berechne_einkommensteuer(zve_soli, 2026)
soli_mit = berechne_soli(ekst_soli, jahr=2026) / 12

# KiSt
kist_ohne = berechne_kirchensteuer(ekst_jahr, 0.09) / 12
kist_mit = berechne_kirchensteuer(berechne_einkommensteuer(zve_soli, 2026), 0.09) / 12

print(f"Brutto: {brutto}€, EU: {eu}€, SV-pflichtig: {brutto_st}€")
print(f"zvE: {zve:,.0f}€")
print(f"EkSt/mtl (Grundtarif = StKl 1 = StKl 4): {ekst_monat:,.2f}€")
print()
print(f"Soli ohne KiFB: {soli_ohne:,.2f}€")
print(f"Soli mit 0.5 KiFB: {soli_mit:,.2f}€ (Diff: {soli_ohne - soli_mit:+.2f}€)")
print()
print(f"KiSt (9%) ohne KiFB: {kist_ohne:,.2f}€")
print(f"KiSt (9%) mit 0.5 KiFB: {kist_mit:,.2f}€ (Diff: {kist_ohne - kist_mit:+.2f}€)")
print()

# Was steht alles auf dem Gehaltszettel?
print(f"=== Was könnte auf dem Gehaltszettel stehen? ===")
print(f"Lohnsteuer (StKl 4): {ekst_monat:>10.2f}€")
print(f"Soli:                {soli_ohne:>10.2f}€")
print(f"KiSt (wenn 9%):      {kist_ohne:>10.2f}€")
print(f"SUMME Steuern:       {ekst_monat + soli_ohne + kist_ohne:>10.2f}€")
print()
print(f"User sagt 'EkSt' = 1.867€")
print(f"Wenn das EkSt + Soli + KiSt ist: {ekst_monat + soli_ohne + kist_ohne:,.2f}€")
print(f"Differenz zum User: {1867 - (ekst_monat + soli_ohne + kist_ohne):+,.2f}€")
print()

# Was wenn das SV-pflichtige Brutto NICHT um EU reduziert wird?
# (Weil manche Arbeitgeber das anders handhaben)
va2 = berechne_vorsorgeaufwendungen_steuerlich(brutto, 2026, phase="Aktiv")
zve2 = ermittle_zve_naherung(brutto * 12, 2026, phase="Aktiv", vorsorgeaufwendungen_jahr=va2)
ekst2 = berechne_einkommensteuer(zve2, 2026) / 12
soli2 = berechne_soli(berechne_einkommensteuer(zve2, 2026), jahr=2026) / 12
kist2 = berechne_kirchensteuer(berechne_einkommensteuer(zve2, 2026), 0.09) / 12
print(f"=== Wenn SV-Brutto = volles Brutto ({brutto}€) ===")
print(f"zvE: {zve2:,.0f}€")
print(f"EkSt/mtl: {ekst2:,.2f}€")
print(f"Soli: {soli2:,.2f}€")
print(f"KiSt (9%): {kist2:,.2f}€")
print(f"SUMME: {ekst2 + soli2 + kist2:,.2f}€")
print(f"Diff zu User (1867): {1867 - (ekst2 + soli2 + kist2):+,.2f}€")
print()

# Netto-Check mit allen Steuern
from logic.sozialversicherung import berechne_sv_aktiv
sv = berechne_sv_aktiv(brutto_st, 2026, 1)
netto_rom = brutto - eu - sv['Gesamt'] - ekst_monat - soli_ohne
print(f"=== Netto-Check (ohne KiSt, StKl 4) ===")
print(f"  Brutto:    {brutto:>10.2f}")
print(f"  - EU:      {eu:>10.2f}")
print(f"  - SV:      {sv['Gesamt']:>10.2f}")
print(f"  - EkSt:    {ekst_monat:>10.2f}")
print(f"  - Soli:    {soli_ohne:>10.2f}")
print(f"  = Netto:   {netto_rom:>10.2f}")
print(f"  User-Netto: 4129.00")
print(f"  Diff:      {netto_rom - 4129:+.2f}")
