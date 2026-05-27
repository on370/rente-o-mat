"""
Modul für rentenrechtliche Berechnungen (z.B. Regelaltersgrenze, Abschläge).
"""

def berechne_regelaltersgrenze(geburtsjahr):
    """
    Berechnet die gesetzliche Regelaltersgrenze basierend auf dem Geburtsjahr.
    Gibt ein Tupel zurück: (Jahre, Monate)
    """
    if geburtsjahr < 1947:
        return (65, 0)
    elif geburtsjahr <= 1958:
        # 1947 -> 65 Jahre + 1 Monat, ..., 1958 -> 65 Jahre + 12 Monate (66 Jahre)
        monate_extra = geburtsjahr - 1946
        return (65 + monate_extra // 12, monate_extra % 12)
    elif geburtsjahr <= 1963:
        # 1959 -> 66 Jahre + 2 Monate, ..., 1963 -> 66 Jahre + 10 Monate
        monate_extra = (geburtsjahr - 1958) * 2
        return (66 + monate_extra // 12, monate_extra % 12)
    else:
        # 1964 und später
        return (67, 0)

def format_regelaltersgrenze(geburtsjahr):
    """
    Gibt die Regelaltersgrenze als formatierten String zurück.
    """
    jahre, monate = berechne_regelaltersgrenze(geburtsjahr)
    if monate == 0:
        return f"{jahre} Jahre"
    else:
        return f"{jahre} Jahre, {monate} Monate"

def berechne_monate_frueher(geburtsjahr, rentenbeginn_dezimal, geburtsmonat=1):
    """
    Berechnet, wie viele Monate vor der Regelaltersgrenze der Renteneintritt erfolgt.
    rentenbeginn_dezimal: Jahr als Float (z.B. 2030.25 für April 2030)
    """
    rag_jahre, rag_monate = berechne_regelaltersgrenze(geburtsjahr)
    
    # Umrechnung in Gesamtmonate ab Jahr 0 (vereinfacht für Differenzbildung)
    total_rag_monate = (geburtsjahr + rag_jahre) * 12 + (geburtsmonat - 1) + rag_monate
    
    # rentenbeginn_dezimal in Monate umrechnen
    total_beginn_monate = int(round(rentenbeginn_dezimal * 12))
    
    monate_frueher = max(0, total_rag_monate - total_beginn_monate)
    return monate_frueher

def berechne_ep_pro_jahr(brutto_monat, jahr):
    """
    Berechnet die pro Jahr gesammelten Entgeltpunkte basierend auf dem Brutto
    und dem Durchschnittsentgelt, unter Berücksichtigung der BBG.
    """
    from logic.sozialversicherung import _get_sv_params
    from config import DURCHSCHNITTSENTGELT_AKTUELL
    
    p = _get_sv_params(jahr)
    jahresbrutto_gedeckelt = min(brutto_monat, p["bbg_rv"]) * 12
    return jahresbrutto_gedeckelt / DURCHSCHNITTSENTGELT_AKTUELL

def berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr, rentenwert):
    """
    Berechnet den Beitragsverlust (fehlende EP) in Euro pro Monat.
    """
    jahre_frueher = monate_frueher / 12
    fehlende_ep = jahre_frueher * ep_pro_jahr
    loss_euro = fehlende_ep * rentenwert
    return {
        "euro": loss_euro,
        "ep": fehlende_ep
    }
