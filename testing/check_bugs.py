#!/usr/bin/env python3
"""Reproduce Abschlag bug and Netto discrepancy."""
from logic.rentenrecht import berechne_monate_frueher, berechne_regelaltersgrenze
from logic.engine import calculate_financials_for_year

# === BUG 1: Rentenabschlag ===
print("=" * 60)
print("BUG 1: Rentenabschlag GJ Jan 1966, RB Feb 2031")
print("=" * 60)

gj = 1966
gm = 1  # Januar
rb = 2031 + 1/12  # Februar 2031

rag_j, rag_m = berechne_regelaltersgrenze(gj)
print(f"RAG: {rag_j} Jahre, {rag_m} Monate")
# RAG = Jan 1966 + 67J + 0M = Jan 2033
# Rente beginnt am 1. des Folgemonats = Feb 2033
# Rentenbeginn: Feb 2031
# Differenz: Feb 2031 → Feb 2033 = 24 Monate = 7.2%
print(f"RAG-Punkt: Jan {gj + rag_j}")
print(f"Rente regulär ab: Feb {gj + rag_j}")
print(f"Rentenbeginn gewählt: Feb 2031")
print(f"Erwartete Differenz: 24 Monate = 7.2%")

mfr = berechne_monate_frueher(gj, rb, geburtsmonat=gm)
abschlag = min(14.4, mfr * 0.3)
print(f"\nErgebnis berechne_monate_frueher: {mfr} Monate")
print(f"Abschlag: {abschlag:.1f}%")
print(f"BUG? {mfr != 24}")

# Jetzt schauen wir uns die Funktion genau an
print(f"\nDebug: rb = {rb}")
print(f"Debug: gj + rag_j = {gj + rag_j}")
print(f"Debug: gm + rag_m = {gm + rag_m}")

# === BUG 2: Netto-Diskrepanz ===
print("\n" + "=" * 60)
print("BUG 2: Netto-Diskrepanz Brutto 8014.96 -> Netto 4996.70")
print("=" * 60)

params = {
    "geburtsjahr": 1966, "geburtsmonat": 1,
    "aktuelles_jahr": 2026, "rentenbeginn": 2031 + 1/12,
    "aktuelles_brutto": 8014.96, "kinderzahl": 1,
    "kirchensteuer_satz": 0.0, "inflation_rate": 2.0,
    "rentenanpassung_rate": 2.0, "bav_anpassung_rate": 1.0,
    "gehalts_dynamik": 0.0,
    "atz_simulieren": False, "atz_start": 9999,
    "einnahmen": [],
    "ausgaben_kategorien": [], "ausgaben_input": {},
    "anpassungsfaktor_input": {},
    "befristete_ausgaben": [], "einmalige_ausgaben": [],
}

res = calculate_financials_for_year(2026, params)
print(f"Engine-Ergebnis (ohne Gehaltsdynamik):")
print(f"  Brutto:   {res['Brutto']:>10.2f}")
print(f"  SV:       {res['Sozialabgaben']:>10.2f}")
print(f"  EkSt:     {res['EkSt']:>10.2f}")
print(f"  Soli:     {res['Soli']:>10.2f}")
print(f"  KiSt:     {res['KiSt']:>10.2f}")
print(f"  Netto:    {res['Netto-Einkommen']:>10.2f}")
print(f"  Echtes Netto (Lohnbescheinigung): 4129.00")
print(f"  Differenz: {res['Netto-Einkommen'] - 4129:.2f}")
print()

# Was fehlt für 867€ Differenz?
diff = res['Netto-Einkommen'] - 4129
print("Mögliche Erklärungen für die Differenz:")
print(f"  bAV-Entgeltumwandlung (SV+Steuer-frei): typisch 200-400€")
print(f"  VWL: typisch 40€")
print(f"  Private Zusatzversicherungen: variabel")
print(f"  Firmenwagen-Versteuerung: 1%-Regel")
print(f"  Kirchensteuer (wenn 9%): {res['EkSt'] * 0.09 * 12 / 12:.0f}€/mtl")
print(f"  Summe typischer Abzüge: 300-600€")
print(f"  Tatsächliche Differenz: {diff:.0f}€")
