VERSION = "1.0.1"
STAGE = "[rel]"
BUILD_ID = "00AD"  # Phase 4 audit: Reset widget keys on import via uploader suffix

# Aktueller Rentenwert ab 1. Juli 2025 (einheitlich West/Ost)
RENTENWERT_AKTUELL = 40.79

# Vorläufiges Durchschnittsentgelt 2025 (zur Berechnung von Entgeltpunkten)
DURCHSCHNITTSENTGELT_AKTUELL = 50493.0

FULL_VERSION = f"{VERSION} {STAGE} (build {BUILD_ID})"
DATENSCHUTZ_INFO = """
**Deine Daten gehören Dir:** Rente-O-Mat speichert Deine Daten und Berechnungen nur während der laufenden Sitzung, danach nicht mehr.
Wenn Du später die Berechnung ansehen oder ändern willst, speichere Dein Profil mit dem Button "Exportieren".
Die Datei mit Deinen Daten wird als **ROM_Vorname_Nachname.json** im Download-Ordner Deines Browsers abgelegt.
Um die Daten in einer späteren Sitzung wieder zu laden, öffne mit dem "Upload" Button die Datei und klicke anschließend auf "Import".
"""
