#!/usr/bin/env python3
"""
QA-Referenzwerte für die drei Testpersonen.
Berechnet SV, EkSt, Netto für Aktiv- und Rentenphase.
"""
from logic.engine import calculate_financials_for_year
from logic.sozialversicherung import berechne_sv_aktiv, berechne_sv_rentner, _get_sv_params, berechne_pv_satz
from logic.taxes import berechne_einkommensteuer, ermittle_zve_naherung, berechne_soli, berechne_kirchensteuer
from logic.rentenrecht import berechne_regelaltersgrenze, berechne_monate_frueher, berechne_ep_pro_jahr
from config import RENTENWERT_AKTUELL, DURCHSCHNITTSENTGELT_AKTUELL

print("=" * 70)
print("REFERENZWERTE FÜR RENTE-O-MAT QA")
print("=" * 70)

# --- Persona A: Friseurin ---
print("\n### Szenario A: Anna Müller (Friseurin, 2.800€ Brutto)")
p = _get_sv_params(2026)
sv_a = berechne_sv_aktiv(2800, 2026, kinderzahl=2)
print(f"SV Aktiv 2026: KV={sv_a['KV']:.2f}, PV={sv_a['PV']:.2f}, RV={sv_a['RV']:.2f}, ALV={sv_a['ALV']:.2f}")
print(f"SV Gesamt: {sv_a['Gesamt']:.2f}")
pv_satz = berechne_pv_satz(2, p)
print(f"PV-Satz (2 Kinder): {pv_satz*100:.3f}%")

# EP/Jahr für Friseurin
ep_a = berechne_ep_pro_jahr(2800, 2026)
print(f"EP/Jahr: {ep_a:.4f}")
print(f"RAG: {berechne_regelaltersgrenze(1975)}")

# Engine-Berechnung
params_a = {
    "geburtsjahr": 1975, "geburtsmonat": 3,
    "aktuelles_jahr": 2026, "rentenbeginn": 2042.0,
    "aktuelles_brutto": 2800.0, "kinderzahl": 2,
    "kirchensteuer_satz": 0.0, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 1.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 1100.0, "typ": "Gesetzlich", "start": 2042.0, "ende": 2080, "eingabe_modus": "euro"},
    ],
    "ausgaben_kategorien": ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"],
    "ausgaben_input": {"Wohnen": 750, "Mobilität": 200, "Lebensmittel": 350, "Versicherungen": 100, "Gesundheit": 50, "Freizeit": 100, "Sonstiges": 100},
    "anpassungsfaktor_input": {"Wohnen": 100, "Mobilität": 100, "Lebensmittel": 100, "Versicherungen": 100, "Gesundheit": 100, "Freizeit": 100, "Sonstiges": 100},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
}

res_a_aktiv = calculate_financials_for_year(2026, params_a)
res_a_rente = calculate_financials_for_year(2043, params_a)
print(f"\nAktiv 2026: Brutto={res_a_aktiv['Brutto']:.0f}, SV={res_a_aktiv['Sozialabgaben']:.0f}, EkSt={res_a_aktiv['EkSt']:.0f}, Soli={res_a_aktiv['Soli']:.0f}, Netto={res_a_aktiv['Netto-Einkommen']:.0f}")
print(f"Rente 2043: Brutto={res_a_rente['Brutto']:.0f}, SV={res_a_rente['Sozialabgaben']:.0f}, EkSt={res_a_rente['EkSt']:.0f}, Netto={res_a_rente['Netto-Einkommen']:.0f}")

# --- Persona B: Ingenieur ---
print("\n" + "=" * 70)
print("### Szenario B: Max Schmidt (Ingenieur, 6.500€ Brutto)")
sv_b = berechne_sv_aktiv(6500, 2026, kinderzahl=1)
print(f"SV Aktiv 2026: KV={sv_b['KV']:.2f}, PV={sv_b['PV']:.2f}, RV={sv_b['RV']:.2f}, ALV={sv_b['ALV']:.2f}")
print(f"SV Gesamt: {sv_b['Gesamt']:.2f}")
ep_b = berechne_ep_pro_jahr(6500, 2026)
print(f"EP/Jahr: {ep_b:.4f}")
print(f"RAG: {berechne_regelaltersgrenze(1968)}")
mfr_b = berechne_monate_frueher(1968, 2033.0, geburtsmonat=7)
print(f"Monate früher (Rentenbeginn 2033.0): {mfr_b}")
print(f"Abschlag: {min(14.4, mfr_b * 0.3):.1f}%")

params_b = {
    "geburtsjahr": 1968, "geburtsmonat": 7,
    "aktuelles_jahr": 2026, "rentenbeginn": 2033.0,
    "aktuelles_brutto": 6500.0, "kinderzahl": 1,
    "kirchensteuer_satz": 0.09, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 1.0,
    "atz_simulieren": True, "atz_start": 2029.0, "atz_dauer": 4,
    "atz_aufstockung_pct": 35,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2400.0, "typ": "Gesetzlich", "start": 2033.0, "ende": 2070, "eingabe_modus": "euro"},
        {"name": "Betriebsrente", "betrag": 800.0, "typ": "bAV", "start": 2033.0, "ende": 2070},
    ],
    "ausgaben_kategorien": ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"],
    "ausgaben_input": {"Wohnen": 1400, "Mobilität": 350, "Lebensmittel": 500, "Versicherungen": 250, "Gesundheit": 100, "Freizeit": 300, "Sonstiges": 200},
    "anpassungsfaktor_input": {"Wohnen": 100, "Mobilität": 100, "Lebensmittel": 100, "Versicherungen": 100, "Gesundheit": 100, "Freizeit": 100, "Sonstiges": 100},
    "befristete_ausgaben": [
        {"name": "Studium Kind", "betrag_mtl": 500, "start": 2030, "ende": 2035, "kategorie": "", "inflationsgebunden": True},
    ],
    "einmalige_ausgaben": [
        {"name": "Weltreise", "betrag": 15000, "jahr": 2034, "monat": 6, "kategorie": "", "inflationsgebunden": True},
    ],
}

res_b_aktiv = calculate_financials_for_year(2026, params_b)
res_b_atz = calculate_financials_for_year(2030, params_b)
res_b_rente = calculate_financials_for_year(2034, params_b)
print(f"\nAktiv 2026: Brutto={res_b_aktiv['Brutto']:.0f}, SV={res_b_aktiv['Sozialabgaben']:.0f}, EkSt={res_b_aktiv['EkSt']:.0f}, KiSt={res_b_aktiv['KiSt']:.0f}, Netto={res_b_aktiv['Netto-Einkommen']:.0f}")
print(f"ATZ   2030: Brutto={res_b_atz['Brutto']:.0f}, SV={res_b_atz['Sozialabgaben']:.0f}, EkSt={res_b_atz['EkSt']:.0f}, Netto={res_b_atz['Netto-Einkommen']:.0f}, Phase={res_b_atz['Phase']}")
print(f"Rente 2034: Brutto={res_b_rente['Brutto']:.0f}, SV={res_b_rente['Sozialabgaben']:.0f}, EkSt={res_b_rente['EkSt']:.0f}, Netto={res_b_rente['Netto-Einkommen']:.0f}")

# --- Persona C: Chefarzt ---
print("\n" + "=" * 70)
print("### Szenario C: Dr. Thomas Weber (Chefarzt, 12.000€ Brutto)")
sv_c = berechne_sv_aktiv(12000, 2026, kinderzahl=3)
print(f"SV Aktiv 2026: KV={sv_c['KV']:.2f}, PV={sv_c['PV']:.2f}, RV={sv_c['RV']:.2f}, ALV={sv_c['ALV']:.2f}")
print(f"SV Gesamt: {sv_c['Gesamt']:.2f}")
ep_c = berechne_ep_pro_jahr(12000, 2026)
print(f"EP/Jahr: {ep_c:.4f} (sollte an BBG gedeckelt sein)")
print(f"RAG: {berechne_regelaltersgrenze(1965)}")
mfr_c = berechne_monate_frueher(1965, 2030.0, geburtsmonat=1)
print(f"Monate früher (Rentenbeginn 2030.0): {mfr_c}")
print(f"Abschlag: {min(14.4, mfr_c * 0.3):.1f}%")

params_c = {
    "geburtsjahr": 1965, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2030.0,
    "aktuelles_brutto": 12000.0, "kinderzahl": 3,
    "kirchensteuer_satz": 0.08, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 1.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [
        {"name": "Gesetzliche Rente", "betrag": 2800.0, "typ": "Gesetzlich", "start": 2030.0, "ende": 2070, "eingabe_modus": "euro"},
        {"name": "Betriebsrente", "betrag": 1500.0, "typ": "bAV", "start": 2030.0, "ende": 2070},
        {"name": "Private RV", "betrag": 600.0, "typ": "Privat", "start": 2030.0, "ende": 2070},
    ],
    "ausgaben_kategorien": ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"],
    "ausgaben_input": {"Wohnen": 2200, "Mobilität": 500, "Lebensmittel": 700, "Versicherungen": 400, "Gesundheit": 200, "Freizeit": 600, "Sonstiges": 400},
    "anpassungsfaktor_input": {"Wohnen": 100, "Mobilität": 100, "Lebensmittel": 100, "Versicherungen": 100, "Gesundheit": 100, "Freizeit": 100, "Sonstiges": 100},
    "befristete_ausgaben": [
        {"name": "Studium Kinder", "betrag_mtl": 800, "start": 2026, "ende": 2032, "kategorie": "", "inflationsgebunden": True},
    ],
    "einmalige_ausgaben": [
        {"name": "Weltreise", "betrag": 30000, "jahr": 2031, "monat": 3, "kategorie": "", "inflationsgebunden": True},
    ],
}

res_c_aktiv = calculate_financials_for_year(2026, params_c)
res_c_rente = calculate_financials_for_year(2031, params_c)
print(f"\nAktiv 2026: Brutto={res_c_aktiv['Brutto']:.0f}, SV={res_c_aktiv['Sozialabgaben']:.0f}, EkSt={res_c_aktiv['EkSt']:.0f}, KiSt={res_c_aktiv['KiSt']:.0f}, Netto={res_c_aktiv['Netto-Einkommen']:.0f}")
print(f"Rente 2031: Brutto={res_c_rente['Brutto']:.0f}, SV={res_c_rente['Sozialabgaben']:.0f}, EkSt={res_c_rente['EkSt']:.0f}, Netto={res_c_rente['Netto-Einkommen']:.0f}")

# --- BMF-Referenzrechnung ---
print("\n" + "=" * 70)
print("MANUELLE REFERENZ: BMF Lohnsteuerrechner 2026")
print("=" * 70)
# Für EkSt-Plausibilisierung: zvE berechnen
for label, brutto, kinder, kist in [("A", 2800, 2, 0.0), ("B", 6500, 1, 0.09), ("C", 12000, 3, 0.08)]:
    from logic.sozialversicherung import berechne_vorsorgeaufwendungen_steuerlich
    va = berechne_vorsorgeaufwendungen_steuerlich(brutto, 2026, phase="Aktiv")
    zve = ermittle_zve_naherung(brutto * 12, 2026, phase="Aktiv", vorsorgeaufwendungen_jahr=va)
    ekst_jahr = berechne_einkommensteuer(zve, 2026)
    soli_jahr = berechne_soli(ekst_jahr, jahr=2026)
    kist_jahr = berechne_kirchensteuer(ekst_jahr, kist)
    print(f"Szenario {label}: Brutto={brutto*12:,.0f}€/J, VA={va:,.0f}€, zvE={zve:,.0f}€, EkSt={ekst_jahr:,.0f}€/J ({ekst_jahr/12:.0f}/mtl), Soli={soli_jahr:.0f}, KiSt={kist_jahr:.0f}")
