#!/usr/bin/env python3
"""
Vollständiger QA-Bericht: Vergleich App-Engine vs. offizielle 2026er Parameter.
Identifiziert Abweichungen durch fehlende 2026er Parametrisierung.
"""
import math

# ===== OFFIZIELLE 2026er PARAMETER =====
# Quelle: BMF, DRV, GKV-Spitzenverband

# EkSt 2026 (§32a EStG, Steuerfortentwicklungsgesetz)
def ekst_2026_offiziell(zve):
    X = math.floor(max(0, zve))
    if X <= 12348: return 0
    elif X <= 17799:
        y = (X - 12348) / 10000
        return math.floor((914.51 * y + 1400) * y)
    elif X <= 69878:
        y = (X - 17799) / 10000
        return math.floor((173.10 * y + 2397) * y + 1034.87)
    elif X <= 277825:
        return math.floor(0.42 * X - 11135.63)
    else:
        return math.floor(0.45 * X - 19470.38)

# SV 2026
SV_2026 = {
    "bbg_kv": 5812.50,
    "bbg_rv": 8450.00,
    "rate_kv_an": 0.073,       # halber allg. Beitragssatz: 14,6% / 2
    "rate_kv_zusatz": 0.0145,  # halber Zusatzbeitrag: 2,9% / 2 (Anstieg von 0,85%!)
    "rate_pv_basis": 0.018,    # PV Basissatz: 3,6% / 2
    "rate_pv_kinderlos_zuschlag": 0.006,
    "rate_pv_abschlag_je_kind": 0.0025,
    "rate_rv_an": 0.093,       # RV: 18,6% / 2
    "rate_alv_an": 0.013,      # ALV: 2,6% / 2
}

# Rentenwert / Durchschnittsentgelt 2026
RENTENWERT_2026 = 42.52  # ab 01.07.2026
DURCHSCHNITTSENTGELT_2026 = 51944.0

def pv_satz_2026(kinder):
    basis = SV_2026["rate_pv_basis"]
    if kinder == 0:
        return basis + SV_2026["rate_pv_kinderlos_zuschlag"]
    elif kinder == 1:
        return basis
    else:
        abschlag = min(kinder - 1, 4) * SV_2026["rate_pv_abschlag_je_kind"]
        return max(0, basis - abschlag)

def sv_aktiv_2026(brutto, kinder):
    p = SV_2026
    pv = pv_satz_2026(kinder)
    kv = min(brutto, p["bbg_kv"]) * (p["rate_kv_an"] + p["rate_kv_zusatz"])
    pv_b = min(brutto, p["bbg_kv"]) * pv
    rv = min(brutto, p["bbg_rv"]) * p["rate_rv_an"]
    alv = min(brutto, p["bbg_rv"]) * p["rate_alv_an"]
    return {"KV": kv, "PV": pv_b, "RV": rv, "ALV": alv, "Gesamt": kv + pv_b + rv + alv}

# ===== APP-WERTE (Engine mit 2025er Fallback) =====
from logic.engine import calculate_financials_for_year
from logic.sozialversicherung import berechne_sv_aktiv
from logic.taxes import berechne_einkommensteuer, ermittle_zve_naherung
from logic.sozialversicherung import berechne_vorsorgeaufwendungen_steuerlich

print("=" * 80)
print("QA-REPORT: App-Engine (2025 Fallback) vs. offizielle 2026er Parameter")
print("=" * 80)

scenarios = [
    {"name": "A: Friseurin (Anna)", "brutto": 2800, "kinder": 2, "kist": 0.0},
    {"name": "B: Ingenieur (Max)", "brutto": 6500, "kinder": 1, "kist": 0.09},
    {"name": "C: Chefarzt (Dr. Weber)", "brutto": 12000, "kinder": 3, "kist": 0.08},
]

for s in scenarios:
    print(f"\n{'─' * 80}")
    print(f"### {s['name']} — Brutto {s['brutto']:,}€/mtl., {s['kinder']} Kind(er)")
    print(f"{'─' * 80}")
    
    brutto = s["brutto"]
    kinder = s["kinder"]
    kist = s["kist"]
    
    # --- SV ---
    sv_app = berechne_sv_aktiv(brutto, 2026, kinder)
    sv_ref = sv_aktiv_2026(brutto, kinder)
    
    print(f"\n  {'Posten':<10} {'App (2025→2026)':>14} {'Referenz 2026':>14} {'Diff':>8}")
    print(f"  {'─'*48}")
    for key in ["KV", "PV", "RV", "ALV", "Gesamt"]:
        diff = sv_app[key] - sv_ref[key]
        marker = " ⚠️" if abs(diff) > 1 else " ✅"
        print(f"  {key:<10} {sv_app[key]:>14.2f} {sv_ref[key]:>14.2f} {diff:>+8.2f}{marker}")
    
    # --- EkSt ---
    va = berechne_vorsorgeaufwendungen_steuerlich(brutto, 2026, phase="Aktiv")
    zve = ermittle_zve_naherung(brutto * 12, 2026, phase="Aktiv", vorsorgeaufwendungen_jahr=va)
    ekst_app = berechne_einkommensteuer(zve, 2026)
    ekst_ref = ekst_2026_offiziell(zve)
    
    # Korrektes zvE mit 2026er VA
    # VA mit 2026er Parametern (höhere BBG → höhere abzugsfähige Beiträge)
    sv_ref_total = sv_ref["Gesamt"]
    # RV (AN+AG): Für Vorsorgeaufwendungen
    rv_abzug_2026 = min(brutto, SV_2026["bbg_rv"]) * SV_2026["rate_rv_an"] * 2
    kv_beitrag_2026 = min(brutto, SV_2026["bbg_kv"]) * (SV_2026["rate_kv_an"] + SV_2026["rate_kv_zusatz"])
    pv_beitrag_2026 = min(brutto, SV_2026["bbg_kv"]) * SV_2026["rate_pv_basis"]
    va_ref = (rv_abzug_2026 + (kv_beitrag_2026 + pv_beitrag_2026) * 0.96) * 12
    zve_ref = max(0, brutto * 12 - 1230 - 36 - va_ref)
    ekst_ref_correct = ekst_2026_offiziell(zve_ref)
    
    print(f"\n  {'EkSt':<10} {'App':>14} {'Ref (App-zvE)':>14} {'Ref (korr.zvE)':>14}")
    print(f"  {'─'*55}")
    print(f"  {'zvE':<10} {zve:>14,.0f} {zve:>14,.0f} {zve_ref:>14,.0f}")
    print(f"  {'VA (Jahr)':<10} {va:>14,.0f} {'—':>14} {va_ref:>14,.0f}")
    print(f"  {'EkSt/J':<10} {ekst_app:>14,.0f} {ekst_ref:>14,.0f} {ekst_ref_correct:>14,.0f}")
    diff_ekst = ekst_app - ekst_ref_correct
    print(f"  {'Diff (mtl)':<10} {'':>14} {'':>14} {diff_ekst/12:>+14.0f} €/mtl ⚠️")
    
    # --- EP/Jahr ---
    ep_app = (brutto * 12) / 50493.0  # App benutzt DURCHSCHNITTSENTGELT_AKTUELL = 50493
    ep_ref = min(brutto * 12, SV_2026["bbg_rv"] * 12) / DURCHSCHNITTSENTGELT_2026
    # Deckelung bei BBG RV
    ep_app_capped = min(brutto * 12, 8050 * 12) / 50493.0
    ep_ref_capped = min(brutto * 12, SV_2026["bbg_rv"] * 12) / DURCHSCHNITTSENTGELT_2026
    print(f"\n  {'EP/Jahr':<10} {'App':>14} {'Referenz':>14} {'Diff':>8}")
    print(f"  {'─'*48}")
    print(f"  {'EP/J':<10} {ep_app_capped:>14.4f} {ep_ref_capped:>14.4f} {ep_app_capped - ep_ref_capped:>+8.4f}")

print(f"\n{'=' * 80}")
print("ZUSAMMENFASSUNG DER ABWEICHUNGEN")
print("=" * 80)
print("""
FEHLENDE 2026er PARAMETER IM CODE:

1. ⚠️  EkSt-Tarif 2026 fehlt (taxes.py TARIF_PARAMETER)
   → Grundfreibetrag: 12.096€ (Code) vs. 12.348€ (korrekt) = -252€
   → Progressionszone und Koeffizienten veraltet
   → Auswirkung: +73 bis +224€ EkSt/Jahr zu viel

2. ⚠️  SV-Parameter 2026 fehlen (sozialversicherung.py SV_PARAMETER)
   → BBG KV: 5.512,50€ vs. 5.812,50€
   → BBG RV: 8.050,00€ vs. 8.450,00€  
   → KV-Zusatzbeitrag: 0,85% vs. 1,45% (AN-Hälfte) = +0,6%!
   → Auswirkung: KV-Beitrag um ~35€/mtl. zu niedrig

3. ⚠️  Rentenwert noch 40,79€ (config.py) statt 42,52€ (ab 01.07.2026)
   → EP-basierte Rentenberechnung um ~4,2% zu niedrig

4. ⚠️  Durchschnittsentgelt noch 50.493€ statt 51.944€
   → EP-Berechnung leicht verzerrt
""")
