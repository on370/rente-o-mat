"""
Steuer- und Abgabenlogik für das deutsche Rentensystem.
"""

def berechne_einkommensteuer(zu_versteuerndes_einkommen):
    """
    Berechnung der deutschen Einkommensteuer (Tarif 2024) gemäß § 32a EStG.
    Werte basierend auf den offiziellen BMF-Parametern 2024.
    """
    X = zu_versteuerndes_einkommen
    if X <= 11604:
        return 0
    elif X <= 17005:
        y = (X - 11604) / 10000
        return (922.98 * y + 1400) * y
    elif X <= 66760:
        y = (X - 17005) / 10000
        return (181.19 * y + 2397) * y + 1025.38
    elif X <= 277825:
        return 0.42 * X - 10602.13
    else:
        return 0.45 * X - 18936.88

def berechne_progressionsvorbehalt(zu_versteuerndes_einkommen, steuerfreier_betrag):
    """
    Berechnet die Einkommensteuer unter Berücksichtigung des Progressionsvorbehalts (§ 32b EStG).
    """
    if zu_versteuerndes_einkommen <= 0:
        return 0
    
    fiktives_gesamteinkommen = max(0, zu_versteuerndes_einkommen + steuerfreier_betrag)
    fiktive_steuer = berechne_einkommensteuer(fiktives_gesamteinkommen)
    
    effektiver_steuersatz = fiktive_steuer / fiktives_gesamteinkommen if fiktives_gesamteinkommen > 0 else 0
    return effektiver_steuersatz * zu_versteuerndes_einkommen

def berechne_rentensteuer_anteil(rentenbeginn_jahr):
    """
    Ermittelt den steuerpflichtigen Anteil der Rente basierend auf dem Kohortenprinzip.
    Ref: Wachstumschancengesetz (0,5% Steigerung ab 2023).
    """
    if rentenbeginn_jahr <= 2005:
        return 50.0
    elif rentenbeginn_jahr <= 2020:
        return 50.0 + (rentenbeginn_jahr - 2005) * 2.0
    elif rentenbeginn_jahr <= 2022:
        return 80.0 + (rentenbeginn_jahr - 2020) * 1.0
    else:
        # Ab 2023 Steigerung um 0,5% pro Jahr
        jahre_nach_2022 = rentenbeginn_jahr - 2022
        return min(100.0, 82.0 + jahre_nach_2022 * 0.5)
