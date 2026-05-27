"""
Sozialversicherungslogik für den Rente-O-Mat.
Differenzierte Berechnung nach Lebensphase und Einkommensquelle.
BBG und Beitragssätze sind nach Jahr parametrisiert.
"""

# --- SV-Parameter nach Jahr ---
# Quellen: Deutsche Rentenversicherung, GKV-Spitzenverband
# Für unbekannte Zukunftsjahre: letztes bekanntes Jahr + 3% Fortschreibung auf BBG
SV_PARAMETER = {
    2024: {
        "bbg_kv": 5175.00,    # Beitragsbemessungsgrenze KV/PV (monatlich)
        "bbg_rv": 7550.00,    # Beitragsbemessungsgrenze RV/ALV (monatlich, West)
        "rate_kv_an": 0.073,  # KV Arbeitnehmeranteil (ohne Zusatzbeitrag)
        "rate_kv_zusatz": 0.0085,  # Durchschnittlicher Zusatzbeitrag (halber Anteil)
        "rate_pv_basis": 0.018,    # PV Basissatz (AN-Anteil)
        "rate_pv_kinderlos_zuschlag": 0.006,  # Zuschlag Kinderlose (ab 23 Jahre)
        "rate_pv_abschlag_je_kind": 0.0025,   # Abschlag je Kind (ab 2. Kind, max 5)
        "rate_rv_an": 0.093,  # RV Arbeitnehmeranteil (18,6% / 2)
        "rate_alv_an": 0.013, # ALV Arbeitnehmeranteil (2,6% / 2)
        "bav_freibetrag_kv": 176.75,  # Freibetrag bAV für KV-Beitrag (monatlich)
        "rate_kv_rentner": 0.073,     # KVdR: halber allgemeiner Beitragssatz
        "rate_kv_rentner_zusatz": 0.0085,  # KVdR: halber Zusatzbeitrag
    },
    2025: {
        "bbg_kv": 5512.50,
        "bbg_rv": 8050.00,
        "rate_kv_an": 0.073,
        "rate_kv_zusatz": 0.0085,
        "rate_pv_basis": 0.018,
        "rate_pv_kinderlos_zuschlag": 0.006,
        "rate_pv_abschlag_je_kind": 0.0025,
        "rate_rv_an": 0.093,
        "rate_alv_an": 0.013,
        "bav_freibetrag_kv": 187.25,
        "rate_kv_rentner": 0.073,
        "rate_kv_rentner_zusatz": 0.0085,
    },
}

def _get_sv_params(jahr):
    """Gibt SV-Parameter für ein Jahr zurück. Für Zukunft: Fortschreibung der BBG mit ~3%/Jahr."""
    if jahr in SV_PARAMETER:
        return SV_PARAMETER[jahr]

    # Letztes bekanntes Jahr finden
    bekannte_jahre = sorted(SV_PARAMETER.keys())
    letztes_jahr = max(k for k in bekannte_jahre if k <= jahr) if any(k <= jahr for k in bekannte_jahre) else bekannte_jahre[-1]
    basis = SV_PARAMETER[letztes_jahr].copy()

    # BBG fortschreiben mit ~3% pro Jahr
    diff = jahr - letztes_jahr
    faktor = 1.03 ** diff
    basis["bbg_kv"] = round(basis["bbg_kv"] * faktor, 2)
    basis["bbg_rv"] = round(basis["bbg_rv"] * faktor, 2)
    basis["bav_freibetrag_kv"] = round(basis["bav_freibetrag_kv"] * faktor, 2)
    return basis


def berechne_pv_satz(kinderzahl, sv_params):
    """
    Berechnet den PV-Beitragssatz (AN-Anteil) basierend auf der Kinderzahl.
    Ab 2024: Staffelung nach Anzahl der Kinder (§ 55 SGB XI).
    """
    basis = sv_params["rate_pv_basis"]
    if kinderzahl == 0:
        return basis + sv_params["rate_pv_kinderlos_zuschlag"]
    elif kinderzahl == 1:
        return basis
    else:
        # Ab 2. Kind: Abschlag, maximal bis 5 Kinder berücksichtigt
        abschlag = min(kinderzahl - 1, 4) * sv_params["rate_pv_abschlag_je_kind"]
        return max(0, basis - abschlag)


def berechne_sv_aktiv(brutto_monatlich, jahr, kinderzahl=0):
    """
    Berechnet Sozialversicherungsbeiträge für Aktiv-Beschäftigte (AN-Anteil).
    Returns: dict mit Einzelposten und Gesamtsumme.
    """
    p = _get_sv_params(jahr)
    pv_satz = berechne_pv_satz(kinderzahl, p)

    kv = min(brutto_monatlich, p["bbg_kv"]) * (p["rate_kv_an"] + p["rate_kv_zusatz"])
    pv = min(brutto_monatlich, p["bbg_kv"]) * pv_satz
    rv = min(brutto_monatlich, p["bbg_rv"]) * p["rate_rv_an"]
    alv = min(brutto_monatlich, p["bbg_rv"]) * p["rate_alv_an"]

    gesamt = kv + pv + rv + alv
    return {
        "KV": kv, "PV": pv, "RV": rv, "ALV": alv,
        "Gesamt": gesamt
    }


def berechne_sv_atz(halbes_brutto_monatlich, jahr, kinderzahl=0):
    """
    Berechnet SV-Beiträge in der Altersteilzeit.
    SV wird nur auf das hälftige Brutto berechnet (Aufstockung ist SV-frei).
    """
    return berechne_sv_aktiv(halbes_brutto_monatlich, jahr, kinderzahl)


def berechne_sv_rentner(einnahmen_liste, jahr, kinderzahl=0):
    """
    Berechnet SV-Beiträge für Rentner (KVdR + PV), differenziert nach Einkommensquelle.
    Wendet den bAV-KV-Freibetrag einmalig auf die Summe aller bAV-Bezüge an (M3).
    """
    p = _get_sv_params(jahr)
    pv_satz = berechne_pv_satz(kinderzahl, p)

    sv_gesamt = 0.0
    sv_details = {}

    # 1. Summiere bAV-Bezüge für die einmalige Freibetrags-Anwendung
    bav_gesamt = 0.0
    for e in einnahmen_liste:
        if e["typ"] == "bAV":
            bav_gesamt += e["betrag"]

    # Berechne SV auf summierte bAV (einmaliger Freibetrag)
    if bav_gesamt > 0:
        bav_beitragspflichtig = max(0, bav_gesamt - p["bav_freibetrag_kv"])
        # Voller KV-Satz (AN+AG) = ca. 14,6% + Zusatzbeitrag
        kv_voll = bav_beitragspflichtig * (p["rate_kv_an"] * 2 + p["rate_kv_zusatz"] * 2)
        pv_beitrag = bav_beitragspflichtig * pv_satz * 2  # Auch voller PV-Satz
        sv_bav = kv_voll + pv_beitrag
        
        # Aufteilen auf Details (anteilig)
        for e in einnahmen_liste:
            if e["typ"] == "bAV":
                anteil = e["betrag"] / bav_gesamt
                sv_details[e.get("name", "bAV")] = sv_bav * anteil
                
        sv_gesamt += sv_bav

    # 2. Berechne alle anderen Einnahmen
    for e in einnahmen_liste:
        betrag = e["betrag"]
        typ = e["typ"]
        
        if typ == "bAV":
            continue

        if typ == "Gesetzlich":
            # KVdR: Halber allgemeiner Satz + halber Zusatzbeitrag
            kv = betrag * (p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"])
            pv_beitrag = betrag * pv_satz
            sv = kv + pv_beitrag

        elif typ in ["Privat", "Kapital"]:
            # In der KVdR kein KV/PV-Beitrag auf private Renten und Kapitalerträge
            sv = 0.0

        else:  # Sonstiges
            # Konservativ: Wie gesetzliche Rente behandeln
            kv = betrag * (p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"])
            pv_beitrag = betrag * pv_satz
            sv = kv + pv_beitrag

        sv_details[e.get("name", typ)] = sv
        sv_gesamt += sv

    return {"Gesamt": sv_gesamt, "Details": sv_details}

def berechne_vorsorgeaufwendungen_steuerlich(brutto_monatlich, jahr, phase="Aktiv", kinderzahl=0, einnahmen_liste=None):
    """
    Berechnet die steuerlich abziehbaren Vorsorgeaufwendungen (Basis-Kranken- und Pflegeversicherung).
    Aktiv: RV (AN+AG voll) + KV/PV (AN-Anteil Basis).
    Rente: KV/PV (AN-Anteil Basis).
    """
    p = _get_sv_params(jahr)
    
    if phase == "Aktiv":
        # RV ist seit 2023 zu 100% abziehbar (AN + AG Anteil)
        rv_beitrag_an = min(brutto_monatlich, p["bbg_rv"]) * p["rate_rv_an"]
        rv_abzug = rv_beitrag_an * 2 # AN + AG Anteil
        
        # KV/PV: Nur Basisabsicherung. Vereinfachung: 96% der AN-Beiträge
        kv_beitrag_an = min(brutto_monatlich, p["bbg_kv"]) * (p["rate_kv_an"] + p["rate_kv_zusatz"])
        pv_beitrag_an = min(brutto_monatlich, p["bbg_kv"]) * p["rate_pv_basis"] # Ohne kinderlos-Zuschlag als Basis
        kv_pv_abzug = (kv_beitrag_an + pv_beitrag_an) * 0.96
        
        return (rv_abzug + kv_pv_abzug) * 12
    
    # Rente: Rentner zahlen nur KVdR und PV (keine RV).
    # Beiträge sind als Sonderausgaben abziehbar (KV zu 96% wegen fehlendem Krankengeldanspruch, PV zu 100%).
    if einnahmen_liste is None:
        # Fallback auf Basis des übergebenen brutto_monatlich (gesetzliche + bAV Rente)
        rate_kv = p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"]
        pv_satz = berechne_pv_satz(kinderzahl, p)
        # KVdR halber Satz
        kv_beitrag = min(brutto_monatlich, p["bbg_kv"]) * rate_kv
        pv_beitrag = min(brutto_monatlich, p["bbg_kv"]) * pv_satz
        return (kv_beitrag * 0.96 + pv_beitrag) * 12
    else:
        # Präzise Ermittlung anhand der tatsächlichen Rentenbezüge
        kv_gesamt = 0.0
        pv_gesamt = 0.0
        pv_satz = berechne_pv_satz(kinderzahl, p)
        
        for e in einnahmen_liste:
            betrag = e["betrag"]
            typ = e["typ"]
            if typ == "Gesetzlich":
                kv_gesamt += min(betrag, p["bbg_kv"]) * (p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"])
                pv_gesamt += min(betrag, p["bbg_kv"]) * pv_satz
            elif typ == "bAV":
                beitragspflichtig = max(0, betrag - p["bav_freibetrag_kv"])
                kv_gesamt += min(beitragspflichtig, p["bbg_kv"]) * (p["rate_kv_an"] * 2 + p["rate_kv_zusatz"] * 2)
                pv_gesamt += min(beitragspflichtig, p["bbg_kv"]) * pv_satz * 2
            elif typ not in ["Privat", "Kapital"] and typ != "":
                kv_gesamt += min(betrag, p["bbg_kv"]) * (p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"])
                pv_gesamt += min(betrag, p["bbg_kv"]) * pv_satz
                
        kv_pv_abzug = kv_gesamt * 0.96 + pv_gesamt
        return kv_pv_abzug * 12
