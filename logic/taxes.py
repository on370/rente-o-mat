"""
Steuer- und Abgabenlogik für das deutsche Rentensystem.
Unterstützt EkSt-Tarife 2024 und 2025+ (§ 32a EStG),
Solidaritätszuschlag, Kirchensteuer, Ertragsanteil und Abgeltungsteuer.
"""

# --- EkSt-Tarifparameter nach Jahr ---
# Quelle: BMF / Bundesgesetzblatt
# Für unbekannte Zukunftsjahre wird der letzte bekannte Tarif verwendet.
TARIF_PARAMETER = {
    2024: {
        "grundfreibetrag": 11784,
        "zone2_ende": 17005,
        "zone3_ende": 66760,
        "zone4_ende": 277825,
        "zone2_a": 954.80,
        "zone2_b": 1400,
        "zone3_a": 181.19,
        "zone3_b": 2397,
        "zone3_c": 991.21,
        "zone4_faktor": 0.42,
        "zone4_abzug": 10636.31,
        "zone5_faktor": 0.45,
        "zone5_abzug": 18971.06,
    },
    2025: {
        "grundfreibetrag": 12096,
        "zone2_ende": 17443,
        "zone3_ende": 68480,
        "zone4_ende": 277825,
        "zone2_a": 932.30,
        "zone2_b": 1400,
        "zone3_a": 176.64,
        "zone3_b": 2397,
        "zone3_c": 1015.13,
        "zone4_faktor": 0.42,
        "zone4_abzug": 10911.92,
        "zone5_faktor": 0.45,
        "zone5_abzug": 19246.67,
    },
    2026: {
        "grundfreibetrag": 12348,
        "zone2_ende": 17799,
        "zone3_ende": 69878,
        "zone4_ende": 277825,
        "zone2_a": 914.51,
        "zone2_b": 1400,
        "zone3_a": 173.10,
        "zone3_b": 2397,
        "zone3_c": 1034.87,
        "zone4_faktor": 0.42,
        "zone4_abzug": 11135.63,
        "zone5_faktor": 0.45,
        "zone5_abzug": 19470.38,
    },
}

# --- Steuerliche Pauschbeträge ---
WERBUNGSKOSTEN_PAUSCHBETRAG_AKTIV = 1230.0  # § 9a Satz 1 Nr. 1 Buchst. a EStG
WERBUNGSKOSTEN_PAUSCHBETRAG_RENTE = 102.0   # § 9a Satz 1 Nr. 1 Buchst. b EStG
SONDERAUSGABEN_PAUSCHBETRAG = 36.0          # § 10c EStG


def ermittle_zve_naherung(brutto_jahr, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=0.0):
    """
    Ermittelt eine Näherung des zu versteuernden Einkommens (zvE).
    Zieht Werbungskosten, Sonderausgaben und Vorsorgeaufwendungen vom Brutto ab.
    """
    if phase == "Aktiv":
        wk = WERBUNGSKOSTEN_PAUSCHBETRAG_AKTIV
    else:
        wk = WERBUNGSKOSTEN_PAUSCHBETRAG_RENTE
        
    zve = brutto_jahr - wk - SONDERAUSGABEN_PAUSCHBETRAG - vorsorgeaufwendungen_jahr
    return max(0, zve)


def _get_tarif(jahr):
    """Gibt die Tarifparameter für ein Jahr zurück. Für unbekannte Jahre wird der letzte bekannte Tarif verwendet."""
    if jahr in TARIF_PARAMETER:
        return TARIF_PARAMETER[jahr]
    # Letzten bekannten Tarif nehmen
    letzte_jahr = max(k for k in TARIF_PARAMETER.keys() if k <= jahr) if any(k <= jahr for k in TARIF_PARAMETER) else max(TARIF_PARAMETER.keys())
    return TARIF_PARAMETER[letzte_jahr]


def berechne_einkommensteuer(zu_versteuerndes_einkommen, jahr=2025):
    """
    Berechnung der deutschen Einkommensteuer gemäß § 32a EStG.
    Tarif wird anhand des Jahres automatisch gewählt.
    Gemäß § 32a Abs. 1 EStG wird das zvE auf den nächsten vollen Euro abgerundet
    und die berechnete Steuer ebenfalls auf den nächsten vollen Euro abgerundet.
    """
    import math
    X = math.floor(max(0, zu_versteuerndes_einkommen))
    t = _get_tarif(jahr)

    if X <= t["grundfreibetrag"]:
        steuer = 0.0
    elif X <= t["zone2_ende"]:
        y = (X - t["grundfreibetrag"]) / 10000
        steuer = (t["zone2_a"] * y + t["zone2_b"]) * y
    elif X <= t["zone3_ende"]:
        y = (X - t["zone2_ende"]) / 10000
        steuer = (t["zone3_a"] * y + t["zone3_b"]) * y + t["zone3_c"]
    elif X <= t["zone4_ende"]:
        steuer = t["zone4_faktor"] * X - t["zone4_abzug"]
    else:
        steuer = t["zone5_faktor"] * X - t["zone5_abzug"]
        
    return float(math.floor(steuer))


def berechne_progressionsvorbehalt(zu_versteuerndes_einkommen, steuerfreier_betrag, jahr=2025):
    """
    Berechnet die Einkommensteuer unter Berücksichtigung des Progressionsvorbehalts (§ 32b EStG).
    """
    if zu_versteuerndes_einkommen <= 0:
        return 0.0

    fiktives_gesamteinkommen = max(0, zu_versteuerndes_einkommen + steuerfreier_betrag)
    fiktive_steuer = berechne_einkommensteuer(fiktives_gesamteinkommen, jahr)

    effektiver_steuersatz = fiktive_steuer / fiktives_gesamteinkommen if fiktives_gesamteinkommen > 0 else 0
    return effektiver_steuersatz * zu_versteuerndes_einkommen


def berechne_fuenftelregelung(normales_zve, einmalzahlung, jahr=2025):
    """
    Berechnet die Einkommensteuer nach der Fünftelregelung (§ 34 EStG) für außerordentliche Einkünfte (z.B. bAV Kapital).
    Gibt die ZUSÄTZLICHE Steuer für die Einmalzahlung zurück.
    """
    if einmalzahlung <= 0:
        return 0.0

    steuer_normal = berechne_einkommensteuer(normales_zve, jahr)
    # Steuer auf normales Einkommen + 1/5 der Einmalzahlung
    steuer_mit_fuenftel = berechne_einkommensteuer(normales_zve + (einmalzahlung / 5), jahr)
    
    mehrsteuer_fuenftel = (steuer_mit_fuenftel - steuer_normal) * 5
    return mehrsteuer_fuenftel


def berechne_rentensteuer_anteil(rentenbeginn_jahr):
    """
    Ermittelt den steuerpflichtigen Anteil der gesetzlichen Rente basierend auf dem Kohortenprinzip.
    Ref: Wachstumschancengesetz (0,5% Steigerung ab 2023).
    GILT NUR FÜR GRV (§ 22 Nr. 1 Satz 3 Buchst. a Doppelbuchst. aa EStG).
    bAV ist zu 100% steuerpflichtig (§ 22 Nr. 5 EStG)!
    """
    if rentenbeginn_jahr <= 2005:
        return 50.0
    elif rentenbeginn_jahr <= 2020:
        return 50.0 + (rentenbeginn_jahr - 2005) * 2.0
    elif rentenbeginn_jahr <= 2022:
        return 80.0 + (rentenbeginn_jahr - 2020) * 1.0
    else:
        # Ab 2023 Steigerung um 0,5% pro Jahr (Wachstumschancengesetz)
        jahre_nach_2022 = rentenbeginn_jahr - 2022
        return min(100.0, 82.0 + jahre_nach_2022 * 0.5)


# --- Solidaritätszuschlag (§ 3, 4 SolZG) ---
# Freigrenze: Seit 2021 stark angehoben (partielle Abschaffung)
SOLI_SATZ = 0.055  # 5,5%
# Milderungszone: 11,9% des Überschreitungsbetrags (bis max 5,5%)

def berechne_soli(einkommensteuer_jahr, splitting=False, jahr=2026):
    """
    Berechnet den Solidaritätszuschlag.
    Seit 2021 nur noch für höhere Einkommen relevant.
    """
    if jahr <= 2024:
        freigrenze = 36260 if splitting else 18130
    else:
        freigrenze = 39900 if splitting else 19950

    if einkommensteuer_jahr <= freigrenze:
        return 0.0

    # Milderungszone: 11,9% des Differenzbetrags, max. 5,5% der EkSt
    differenz = einkommensteuer_jahr - freigrenze
    soli_milderung = differenz * 0.119
    soli_voll = einkommensteuer_jahr * SOLI_SATZ
    return min(soli_milderung, soli_voll)


# --- Kirchensteuer ---
def berechne_kirchensteuer(einkommensteuer_jahr, kirchensteuer_satz=0.0):
    """
    Berechnet die Kirchensteuer (8% oder 9% der EkSt, je nach Bundesland).
    kirchensteuer_satz: 0.0 (keine), 0.08 (Bayern/BW), 0.09 (restliche Bundesländer)
    """
    return einkommensteuer_jahr * kirchensteuer_satz


# --- Ertragsanteil für private Renten (§ 22 Nr. 1 Satz 3 Buchst. a Doppelbuchst. bb EStG) ---
# Hängt vom Alter bei Beginn der Rente ab
ERTRAGSANTEIL_TABELLE = {
    55: 26, 56: 26, 57: 25, 58: 24, 59: 23,
    60: 22, 61: 22, 62: 21, 63: 20, 64: 19,
    65: 18, 66: 18, 67: 17, 68: 16, 69: 15,
    70: 15, 71: 14, 72: 13, 73: 13, 74: 12,
    75: 11, 76: 11, 77: 10, 78: 9, 79: 8,
    80: 7, 81: 7, 82: 6, 83: 5, 84: 5,
    85: 4, 86: 4, 87: 3, 88: 3, 89: 2,
    90: 2, 91: 1, 92: 1, 93: 1, 94: 1, 95: 1,
}

def berechne_ertragsanteil(alter_bei_rentenbeginn):
    """
    Ermittelt den Ertragsanteil für private Renten basierend auf dem
    Alter des Rentenberechtigten bei Beginn der Rente.
    """
    alter = int(alter_bei_rentenbeginn)
    if alter < 55:
        return 26  # Minimum in der Tabelle für jüngere
    if alter > 95:
        return 1
    return ERTRAGSANTEIL_TABELLE.get(alter, 18)


# --- Abgeltungsteuer für Kapitalerträge (§ 32d EStG) ---
ABGELTUNGSTEUER_SATZ = 0.25  # 25%
SPARERPAUSCHBETRAG_SINGLE = 1000  # seit 2023

def berechne_abgeltungsteuer(kapitalertraege_jahr, kirchensteuer_satz=0.0, sparerpauschbetrag=None):
    """
    Berechnet die Abgeltungsteuer auf Kapitalerträge (§ 32d EStG).
    Inkl. Soli und ggf. Kirchensteuer.
    """
    if sparerpauschbetrag is None:
        sparerpauschbetrag = SPARERPAUSCHBETRAG_SINGLE

    steuerpflichtig = max(0, kapitalertraege_jahr - sparerpauschbetrag)
    if steuerpflichtig <= 0:
        return 0.0

    # Bei Kirchensteuer wird der AbgSt-Satz angepasst (§ 32d Abs. 1 S. 3 EStG)
    if kirchensteuer_satz > 0:
        effektiver_satz = ABGELTUNGSTEUER_SATZ / (1 + kirchensteuer_satz)
    else:
        effektiver_satz = ABGELTUNGSTEUER_SATZ

    abgst = steuerpflichtig * effektiver_satz
    soli = abgst * SOLI_SATZ  # Soli auf AbgSt (keine Freigrenze bei AbgSt)
    kist = abgst * kirchensteuer_satz

    return abgst + soli + kist
