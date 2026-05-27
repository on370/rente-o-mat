"""
Umfassendes Audit-Skript für Rente-O-Mat v1.0 rc1
Prüft alle Berechnungsmodule gegen bekannte Referenzwerte.
"""
import sys
sys.path.insert(0, '.')

from logic.taxes import (
    berechne_einkommensteuer, berechne_rentensteuer_anteil, 
    berechne_soli, berechne_abgeltungsteuer, ermittle_zve_naherung,
    berechne_progressionsvorbehalt, berechne_kirchensteuer,
    berechne_ertragsanteil, berechne_fuenftelregelung
)
from logic.sozialversicherung import (
    berechne_sv_aktiv, berechne_sv_rentner, 
    berechne_vorsorgeaufwendungen_steuerlich, berechne_pv_satz, _get_sv_params
)
from logic.rentenrecht import (
    berechne_regelaltersgrenze, berechne_monate_frueher, 
    berechne_ep_pro_jahr, berechne_beitragsverlust_logic
)
from config import RENTENWERT_AKTUELL, DURCHSCHNITTSENTGELT_AKTUELL

errors = []
ok_count = 0

def check(name, expected, actual, tolerance=0.5):
    global ok_count
    diff = abs(actual - expected)
    if diff <= tolerance:
        print(f'  ✅ {name}: Erwartet={expected}, Engine={actual:.2f}')
        ok_count += 1
    else:
        msg = f'  ❌ {name}: Erwartet={expected}, Engine={actual:.2f}, Diff={diff:.2f}'
        print(msg)
        errors.append(msg)

print('=== AUDIT PRÜFUNGEN Rente-O-Mat v1.0 rc1 ===')
print()

# 1. EkSt Tarif 2025 - BMF Steuerrechner Referenzwerte
print('--- 1. EkSt Tarif 2025 (§32a EStG) ---')
# Referenz: BMF-Steuerrechner (Grundtabelle, Single)
# Hinweis: BMF-Steuerrechner gibt Lohnsteuer, die = EkSt für Single
ekst_tests = [
    ('Grundfreibetrag', 12096, 0.0),
    ('1 EUR über GFB', 12097, 0.0),
    ('Zone 2: 15k zvE', 15000, 485.0),
    ('Zone 2: 17443', 17443, 1015.0),
    ('Zone 3: 20k zvE', 20000, 1639.0),
    ('Zone 3: 30k zvE', 30000, 4303.0),
    ('Zone 3: 40k zvE', 40000, 7320.0),
    ('Zone 3: 50k zvE', 50000, 10691.0),
    ('Zone 3: 60k zvE', 60000, 14415.0),
    ('Zone 4: 80k zvE', 80000, 22688.0),
    ('Zone 4: 100k zvE', 100000, 31088.0),
    ('Zone 4: 200k zvE', 200000, 73088.0),
    ('Zone 4: 277825', 277825, 105774.0),
    ('Zone 5: 300k zvE', 300000, 115753.0),
]
for desc, zve, expected in ekst_tests:
    actual = berechne_einkommensteuer(zve, 2025)
    check(desc, expected, actual, 0.01)

# EkSt 2024
print()
print('--- 1b. EkSt Tarif 2024 (§32a EStG) ---')
ekst_2024_tests = [
    ('2024: GFB 11784', 11784, 0.0),
    ('2024: 30k zvE', 30000, 4412.0),
    ('2024: 50k zvE', 50000, 10872.0),
]
for desc, zve, expected in ekst_2024_tests:
    actual = berechne_einkommensteuer(zve, 2024)
    check(desc, expected, actual, 0.01)

print()

# 2. Regelaltersgrenze
print('--- 2. Regelaltersgrenze (§35 SGB VI) ---')
rag_tests = [
    (1946, (65, 0)),
    (1947, (65, 1)),
    (1952, (65, 6)),
    (1958, (66, 0)),
    (1959, (66, 2)),
    (1963, (66, 10)),
    (1964, (67, 0)),
    (1965, (67, 0)),
    (1980, (67, 0)),
]
for gj, expected in rag_tests:
    actual = berechne_regelaltersgrenze(gj)
    ok = actual == expected
    if ok:
        print(f'  ✅ GJ={gj}: {actual}')
        ok_count += 1
    else:
        msg = f'  ❌ GJ={gj}: Erwartet={expected}, Engine={actual}'
        print(msg)
        errors.append(msg)

print()

# 3. Rentenbesteuerungsanteil (Kohortenprinzip)
print('--- 3. Rentenbesteuerungsanteil (§22 EStG) ---')
rb_tests = [
    (2005, 50.0),
    (2010, 60.0),
    (2015, 70.0),
    (2020, 80.0),
    (2021, 81.0),
    (2022, 82.0),
    (2023, 82.5),   # Wachstumschancengesetz
    (2025, 83.5),
    (2030, 86.0),
    (2040, 91.0),
    (2058, 100.0),
    (2060, 100.0),
]
for rj, expected in rb_tests:
    actual = berechne_rentensteuer_anteil(rj)
    check(f'RJ={rj}', expected, actual, 0.01)

print()

# 4. Solidaritätszuschlag
print('--- 4. Solidaritätszuschlag (§3,4 SolZG) ---')
# Freigrenze 18.130 EUR (seit 2024)
soli_tests = [
    ('Unterhalb Freigrenze', 18130, 0.0),
    ('Knapp drüber', 18200, 8.33),  # (18200-18130)*0.119 = 8.33
    ('Voller Soli 50k EkSt', 50000, 2750.0),
]
for desc, ekst, expected in soli_tests:
    actual = berechne_soli(ekst, jahr=2024)
    check(desc, expected, actual, 0.5)

print()

# 5. Monate früher
print('--- 5. Monate vor RAG ---')
# GJ 1965: RAG = 67+0 → (1965+67)*12 + 0 = 24384 Monate ab Jahr 0
mf_tests = [
    (1965, 2032.0, 0),       # Genau RAG
    (1965, 2030.0, 24),      # 2 Jahre früher
    (1965, 2028.5, 42),      # 3.5 Jahre früher
]
for gj, rb, expected in mf_tests:
    actual = berechne_monate_frueher(gj, rb)
    ok = actual == expected
    if ok:
        print(f'  ✅ GJ={gj}, RB={rb}: {actual} Monate')
        ok_count += 1
    else:
        msg = f'  ❌ GJ={gj}, RB={rb}: Erwartet={expected}, Engine={actual}'
        print(msg)
        errors.append(msg)

print()

# 6. SV-Beiträge Aktiv (2025)
print('--- 6. SV Aktiv (2025) ---')
sv = berechne_sv_aktiv(6000, 2025, 0)
# BBG KV=5512.50, BBG RV=8050
kv_exp = 5512.50 * (0.073 + 0.0085)
pv_exp = 5512.50 * (0.018 + 0.006)  # kinderlos
rv_exp = 6000 * 0.093
alv_exp = 6000 * 0.013
check('KV', kv_exp, sv["KV"], 0.01)
check('PV (kinderlos)', pv_exp, sv["PV"], 0.01)
check('RV', rv_exp, sv["RV"], 0.01)
check('ALV', alv_exp, sv["ALV"], 0.01)

# SV mit 2 Kindern
sv2 = berechne_sv_aktiv(6000, 2025, 2)
pv_2k = 5512.50 * (0.018 - 0.0025)  # 1 Kind Abschlag (ab 2. Kind)
check('PV (2 Kinder)', pv_2k, sv2["PV"], 0.01)

print()

# 7. EP pro Jahr
print('--- 7. Entgeltpunkte ---')
# 6000 mtl → 72000/Jahr, unter BBG RV 8050*12=96600
ep_exp = (6000 * 12) / DURCHSCHNITTSENTGELT_AKTUELL
ep_act = berechne_ep_pro_jahr(6000, 2025)
check('EP (6000 mtl)', ep_exp, ep_act, 0.001)

# Über BBG
ep_capped = (8050 * 12) / DURCHSCHNITTSENTGELT_AKTUELL
ep_act2 = berechne_ep_pro_jahr(10000, 2025)
check('EP (10000 mtl, >BBG)', ep_capped, ep_act2, 0.001)

print()

# 8. Abgeltungsteuer
print('--- 8. Abgeltungsteuer (§32d EStG) ---')
# 10000 Kapitalertrag, 1000 Freibetrag, 9000 steuerpflichtig
# ohne KiSt: 9000*0.25=2250 + 2250*0.055=123.75 = 2373.75
abgst = berechne_abgeltungsteuer(10000, 0.0)
check('AbgSt 10k ohne KiSt', 2373.75, abgst, 0.01)

# Innerhalb Freibetrag
abgst_frei = berechne_abgeltungsteuer(800, 0.0)
check('AbgSt 800 (unter Freibetrag)', 0.0, abgst_frei, 0.01)

# Mit Kirchensteuer 9%
# Eff. Satz = 0.25/(1+0.09) = 0.22936
# AbgSt = 9000 * 0.22936 = 2064.22
# Soli = 2064.22 * 0.055 = 113.53
# KiSt = 2064.22 * 0.09 = 185.78
# Ges = 2363.53
abgst_k = berechne_abgeltungsteuer(10000, 0.09)
check('AbgSt 10k mit KiSt 9%', 2363.53, abgst_k, 1.0)

print()

# 9. Vorsorgeaufwendungen steuerlich
print('--- 9. Vorsorgeaufwendungen (steuerlicher Abzug) ---')
va = berechne_vorsorgeaufwendungen_steuerlich(6000, 2025, 'Aktiv')
rv_an = min(6000, 8050) * 0.093
rv_abzug = rv_an * 2
kv_an = min(6000, 5512.5) * (0.073 + 0.0085)
pv_an = min(6000, 5512.5) * 0.018
kv_pv_abzug = (kv_an + pv_an) * 0.96
total_va = (rv_abzug + kv_pv_abzug) * 12
check('VA Aktiv (6000 Brutto)', total_va, va, 0.01)

# Rente: Sonderausgabenabzug für KVdR und PV
einnahmen_r = [{"name": "GRV", "betrag": 2000.0, "typ": "Gesetzlich"}]
va_rente = berechne_vorsorgeaufwendungen_steuerlich(2000, 2025, 'Rente', kinderzahl=0, einnahmen_liste=einnahmen_r)
kv_r_exp = 2000 * (0.073 + 0.0085)
pv_r_exp = 2000 * (0.018 + 0.006)
total_va_rente = (kv_r_exp * 0.96 + pv_r_exp) * 12
check('VA Rente (2000 GRV)', total_va_rente, va_rente, 0.01)

print()

# 10. SV Rentner
print('--- 10. SV Rentner ---')
# GRV 2000 EUR: KVdR = 2000*(0.073+0.0085)=163, PV = 2000*0.024 = 48, Ges = 211
sv_r = berechne_sv_rentner([{"name": "GRV", "betrag": 2000, "typ": "Gesetzlich"}], 2025, 0)
kv_r_exp = 2000 * (0.073 + 0.0085)
pv_r_exp = 2000 * (0.018 + 0.006)
check('SV Rentner GRV 2000', kv_r_exp + pv_r_exp, sv_r["Gesamt"], 0.5)

# bAV 600 EUR: Voller Satz (AN+AG), aber Freibetrag 187.25 (2025)
bav_pfl = max(0, 600 - 187.25)
kv_bav_exp = bav_pfl * (0.073*2 + 0.0085*2)
pv_bav_exp = bav_pfl * (0.018 + 0.006) * 2
sv_bav = berechne_sv_rentner([{"name": "bAV", "betrag": 600, "typ": "bAV"}], 2025, 0)
check('SV Rentner bAV 600', kv_bav_exp + pv_bav_exp, sv_bav["Gesamt"], 0.5)

# M3: SV Rentner mit zwei parallelen bAV-Quellen (laufende Rente + Einmalzahlungs-Anteil)
# bAV1 = 600 EUR, bAV2 = 200 EUR. Freibetrag 187.25 (2025) wird einmalig auf die Summe (800 EUR) angewendet.
# Summe beitragspflichtig = 800 - 187.25 = 612.75 EUR.
bav_pfl_2 = max(0, 800 - 187.25)
kv_bav_exp_2 = bav_pfl_2 * (0.073*2 + 0.0085*2)
pv_bav_exp_2 = bav_pfl_2 * (0.018 + 0.006) * 2
sv_bav_2 = berechne_sv_rentner([
    {"name": "bAV Laufend", "betrag": 600, "typ": "bAV"},
    {"name": "bAV Einmalzahlung (Anteil)", "betrag": 200, "typ": "bAV"}
], 2025, 0)
check('SV Rentner Doppel-bAV (einmaliger Freibetrag)', kv_bav_exp_2 + pv_bav_exp_2, sv_bav_2["Gesamt"], 0.5)

# Privat: 0 EUR SV
sv_priv = berechne_sv_rentner([{"name": "Priv", "betrag": 500, "typ": "Privat"}], 2025, 0)
check('SV Rentner Privat', 0.0, sv_priv["Gesamt"], 0.01)

print()

# 11. Ertragsanteil
print('--- 11. Ertragsanteil (§22 EStG) ---')
ea_tests = [
    (60, 22), (62, 21), (65, 18), (67, 17), (70, 15)
]
for alter, expected in ea_tests:
    actual = berechne_ertragsanteil(alter)
    check(f'EA Alter {alter}', expected, actual, 0)

print()

# 12. Progressionsvorbehalt
print('--- 12. Progressionsvorbehalt (§32b EStG) ---')
# 30k zvE + 10k steuerfrei
# Fiktiv: EkSt(40k) = 8252 EUR (bei 2025)
# Effektiver Satz: 8252 / 40000 = 20.63%
# Steuer: 30000 * 20.63% = 6189
pv_test = berechne_progressionsvorbehalt(30000, 10000, 2025)
ekst_fiktiv = berechne_einkommensteuer(40000, 2025)
eff_satz = ekst_fiktiv / 40000
expected_pv = eff_satz * 30000
check('ProgVorb (30k+10k)', expected_pv, pv_test, 0.01)

print()

# 13. Fünftelregelung
print('--- 13. Fünftelregelung (§34 EStG) ---')
# Normales zvE 20k, Einmalzahlung 100k
# EkSt(20k) = 1703.18
# EkSt(20k + 20k) = EkSt(40k) = 8252
# Mehrsteuer = (8252 - 1703.18) * 5 = 32744.1
fr = berechne_fuenftelregelung(20000, 100000, 2025)
ekst_20 = berechne_einkommensteuer(20000, 2025)
ekst_40 = berechne_einkommensteuer(40000, 2025)
expected_fr = (ekst_40 - ekst_20) * 5
check('Fünftel (20k+100k)', expected_fr, fr, 0.01)

print()

# 14. Beitragsverlust
print('--- 14. Beitragsverlust ---')
# 24 Monate früher, 1.5 EP/Jahr, Rentenwert 42
# Fehlende EP = 24/12 * 1.5 = 3.0
# Euro = 3.0 * 42 = 126 EUR/Monat
bv = berechne_beitragsverlust_logic(24, 1.5, 42.0)
check('BV EP', 3.0, bv["ep"], 0.01)
check('BV Euro', 126.0, bv["euro"], 0.01)

print()

# 15. Engine-Gesamttest: Rentenphase
print('--- 15. Engine Gesamttest (Rentenphase) ---')
from logic.engine import calculate_financials_for_year, _calculate_grv_components, get_phase

# Einfacher Fall: GRV 2000€, keine ATZ, keine Assets
test_params = {
    'geburtsjahr': 1965,
    'aktuelles_jahr': 2026,
    'rentenbeginn': 2032.0,
    'aktuelles_brutto': 6000.0,
    'kinderzahl': 0,
    'kirchensteuer_satz': 0.0,
    'inflation_rate': 0.0,
    'rentenanpassung_rate': 0.0,
    'bav_anpassung_rate': 1.0,
    'gehalts_dynamik': 0.0,
    'atz_simulieren': False,
    'atz_start': 9999,
    'einnahmen': [
        {"name": "Gesetzliche Rente", "betrag": 2000.0, "typ": "Gesetzlich", 
         "start": 2032.0, "ende": 2060, "eingabe_modus": "euro"}
    ],
    'ausgaben_kategorien': [],
    'ausgaben_input': {},
    'anpassungsfaktor_input': {},
    'befristete_ausgaben': [],
    'einmalige_ausgaben': [],
}

# Phase-Check
phase = get_phase(2033, False, 9999, 2032)
check_ok = phase == "Rente"
if check_ok:
    print(f'  ✅ Phase 2033: {phase}')
    ok_count += 1
else:
    msg = f'  ❌ Phase 2033: Erwartet=Rente, Engine={phase}'
    print(msg)
    errors.append(msg)

# Berechne ein Rentenjahr
res = calculate_financials_for_year(2033, test_params)

# Monate früher: RAG = 2032.0, Beginn = 2032.0 -> 0 Monate -> kein Abschlag
print(f'  Rentenjahr 2033:')
print(f'    Brutto = {res["Brutto"]:.2f}')
print(f'    SV = {res["Sozialabgaben"]:.2f}')
print(f'    EkSt = {res["EkSt"]:.2f}')
print(f'    Netto = {res["Netto-Einkommen"]:.2f}')
print(f'    Abschlag = {res["Rentenabschlag"]:.2f}')

# Prüfung: Brutto sollte 2000 sein (keine Dynamisierung bei 0%)
check('Brutto GRV (0% Dyn)', 2000.0, res["Brutto"], 1.0)

# Prüfung: Kein Abschlag (genau RAG)
check('Abschlag (RAG)', 0.0, res["Rentenabschlag"], 0.01)

# Neue Prüfungen für EkSt und Netto (Build 00A4)
check('EkSt 2033 (abgerundet + Vorsorgeaufw.)', 101.50, res["EkSt"], 0.01)
check('Netto 2033 (präzise)', 1687.50, res["Netto-Einkommen"], 0.01)

print()

# 16. BBG Fortschreibung
print('--- 16. BBG Fortschreibung (Zukunftsjahre) ---')
p2030 = _get_sv_params(2030)
# 2025 BBG KV = 5512.50, Fortschreibung 3% p.a. für 5 Jahre
bbg_kv_exp = round(5512.50 * 1.03**5, 2)
bbg_rv_exp = round(8050.00 * 1.03**5, 2)
check('BBG KV 2030', bbg_kv_exp, p2030["bbg_kv"], 0.01)
check('BBG RV 2030', bbg_rv_exp, p2030["bbg_rv"], 0.01)

print()

# 17. Kirchensteuer
print('--- 17. Kirchensteuer ---')
ki = berechne_kirchensteuer(10000, 0.09)
check('KiSt 9% auf 10k', 900.0, ki, 0.01)
ki0 = berechne_kirchensteuer(10000, 0.0)
check('KiSt 0%', 0.0, ki0, 0.01)

print()

# === ZUSAMMENFASSUNG ===
print('=' * 60)
print(f'ERGEBNIS: {ok_count} Tests bestanden, {len(errors)} Fehler')
if errors:
    print('\nFEHLER:')
    for e in errors:
        print(e)
else:
    print('\n✅ Alle Tests bestanden!')
print('=' * 60)
