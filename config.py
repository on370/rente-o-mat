VERSION = "1.5.3"
STAGE = "[rel]"
BUILD_ID = "00D3"  # Allow Hauptebene option in group selectbox for both create and edit modes.

# Aktueller Rentenwert ab 1. Juli 2026 (einheitlich West/Ost)
RENTENWERT_AKTUELL = 42.52

# Vorläufiges Durchschnittsentgelt 2026 (zur Berechnung von Entgeltpunkten)
DURCHSCHNITTSENTGELT_AKTUELL = 51944.0

FULL_VERSION = f"{VERSION} {STAGE} (build {BUILD_ID})"
DATENSCHUTZ_INFO = """
**Deine Daten gehören Dir:** Rente-O-Mat speichert Deine Daten und Berechnungen nur während der laufenden Sitzung, danach nicht mehr.
Wenn Du später die Berechnung ansehen oder ändern willst, speichere Dein Profil mit dem Button "Exportieren".
Die Datei mit Deinen Daten wird als **ROM_Vorname_Nachname.json** im Download-Ordner Deines Browsers abgelegt.
Um die Daten in einer späteren Sitzung wieder zu laden, öffne mit dem "Upload" Button die Datei und klicke anschließend auf "Import".
"""
