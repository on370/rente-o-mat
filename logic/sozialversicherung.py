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

    einnahmen_liste: Liste von dicts mit {"betrag": float, "typ": str}
    Typen: "Gesetzlich", "bAV", "Privat", "Kapital", "Sonstiges"

    Regeln:
    - Gesetzliche Rente: KVdR-Beitrag (halber allg. Satz + Zusatzbeitrag) + PV
    - bAV: Voller KV+PV-Beitrag (AN+AG-Anteil!) oberhalb Freibetrag
    - Privat: In der KVdR i.d.R. kein KV-Beitrag (nur bei freiwilliger Versicherung)
    - Kapital: In der KVdR kein KV-Beitrag
    """
    p = _get_sv_params(jahr)
    pv_satz = berechne_pv_satz(kinderzahl, p)

    sv_gesamt = 0.0
    sv_details = {}

    for e in einnahmen_liste:
        betrag = e["betrag"]
        typ = e["typ"]

        if typ == "Gesetzlich":
            # KVdR: Halber allgemeiner Satz + halber Zusatzbeitrag
            kv = betrag * (p["rate_kv_rentner"] + p["rate_kv_rentner_zusatz"])
            pv_beitrag = betrag * pv_satz
            sv = kv + pv_beitrag

        elif typ == "bAV":
            # Voller Beitragssatz (AN+AG) auf bAV-Rente, aber Freibetrag abziehen
            beitragspflichtig = max(0, betrag - p["bav_freibetrag_kv"])
            # Voller KV-Satz (AN+AG) = ca. 14,6% + Zusatzbeitrag
            kv_voll = beitragspflichtig * (p["rate_kv_an"] * 2 + p["rate_kv_zusatz"] * 2)
            pv_beitrag = beitragspflichtig * pv_satz * 2  # Auch voller PV-Satz
            sv = kv_voll + pv_beitrag

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
