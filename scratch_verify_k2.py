from logic.engine import _calculate_grv_components
from config import RENTENWERT_AKTUELL

print(f"--- Verifikation K2: Rentenwert-Projektion ---")
print(f"Aktueller Rentenwert: {RENTENWERT_AKTUELL} EUR")

# Testcase: 40 EP, Rentenbeginn in 10 Jahren, 2% Anpassung
e = {"name": "Gesetzlich", "typ": "Gesetzlich", "eingabe_modus": "punkte", "punkte": 40.0, "start": 2036, "ende": 2060}
params = {
    "geburtsjahr": 1969,
    "aktuelles_jahr": 2026,
    "rentenanpassung_rate": 2.0,
    "rentenbeginn": 2036,
    "aktuelles_brutto": 0 # Kein Zuwachs für diesen Test
}

# Wir testen das Jahr des Rentenbeginns
val_base, bv_jahr, monate_frueher = _calculate_grv_components(e, 2036, params)

# Manuelle Rechnung
# 1. Projektion Rentenwert: 39.32 * (1.02^10)
jahre = 10
rw_proj = RENTENWERT_AKTUELL * (1.02 ** jahre)
# 2. Rente: 40 * rw_proj
rente_erwartet = 40.0 * rw_proj

print(f"Jahre bis Beginn: {jahre}")
print(f"Projizierter Rentenwert (manuell): {rw_proj:.4f} EUR")
print(f"Erwartete Rente (manuell): {rente_erwartet:.2f} EUR")
print(f"Berechneter Basiswert (Engine): {val_base:.2f} EUR")

diff = abs(rente_erwartet - val_base)
if diff < 0.01:
    print("✅ Erfolg: Die Engine projiziert den Rentenwert korrekt!")
else:
    print(f"❌ Fehler: Abweichung von {diff:.2f} EUR")
