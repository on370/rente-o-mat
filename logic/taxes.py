"""
Steuer- und Abgabenlogik für das deutsche Rentensystem.
"""

def berechne_einkommensteuer(zu_versteuerndes_einkommen):
    """
    Berechnung der deutschen Einkommensteuer (Tarif 2024) gemäß § 32a EStG.
    """
    X = zu_versteuerndes_einkommen
    if X <= 11604:
        return 0
    elif X <= 17009:
        y = (X - 11604) / 10000
        return (117.74 * y + 1500) * y
    elif X <= 66760:
        y = (X - 17009) / 10000
        return (192.59 * y + 2397) * y + 969.12
    elif X <= 277825:
        return 0.42 * X - 10602.13
    else:
        return 0.45 * X - 18713.84

def berechne_progressionsvorbehalt(zu_versteuerndes_einkommen, steuerfreier_betrag):
    """
    Berechnet die Einkommensteuer unter Berücksichtigung des Progressionsvorbehalts.
    """
    fiktives_gesamteinkommen = zu_versteuerndes_einkommen + steuerfreier_betrag
    fiktive_steuer = berechne_einkommensteuer(fiktives_gesamteinkommen)
    if fiktives_gesamteinkommen > 0:
        effektiver_steuersatz = fiktive_steuer / fiktives_gesamteinkommen
    else:
        effektiver_steuersatz = 0
    return effektiver_steuersatz * zu_versteuerndes_einkommen

def berechne_rentensteuer_anteil(rentenbeginn_jahr):
    """
    Ermittelt den steuerpflichtigen Anteil der Rente basierend auf dem Kohortenprinzip.
    """
    basis_jahr = 2022
    basis_anteil = 82.0
    if rentenbeginn_jahr <= basis_jahr:
        return min(100.0, basis_anteil + (rentenbeginn_jahr - 2000))
    else:
        jahre_nach_2022 = rentenbeginn_jahr - 2022
        return min(100.0, basis_anteil + jahre_nach_2022 * 0.5)
