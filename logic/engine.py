import pandas as pd
from logic.taxes import berechne_einkommensteuer, berechne_progressionsvorbehalt, berechne_rentensteuer_anteil

def get_phase(jahr, atz_simulieren, atz_start, rentenbeginn):
    """Ermittelt die Lebensphase für ein gegebenes Jahr inkl. ATZ-Split."""
    if jahr < atz_start and jahr < rentenbeginn:
        return "Aktiv"
    elif atz_simulieren and atz_start <= jahr < rentenbeginn:
        # ATZ-Split: Hälftige Aufteilung
        dauer = rentenbeginn - atz_start
        mitte = atz_start + (dauer / 2)
        if jahr < mitte:
            return "ATZ(A)" # Aktivphase
        else:
            return "ATZ(P)" # Passivphase
    else:
        return "Rente"

def calculate_financials_for_year(jahr, params):
    """
    Berechnet alle finanziellen Werte für ein spezifisches Jahr.
    params: Dictionary mit allen Nutzereingaben.
    """
    p = get_phase(jahr, params['atz_simulieren'], params['atz_start'], params['rentenbeginn'])
    
    # Einkommens-Details für das Diagramm
    income_details = {}
    
    # Einnahmen & Abzüge
    if p == "Aktiv":
        brutto = params['aktuelles_brutto']
        income_details["Gehalt"] = brutto
        steuer = berechne_einkommensteuer(brutto * 12) / 12
        sv = brutto * 0.20
        netto = brutto - steuer - sv
    elif p in ["ATZ(A)", "ATZ(P)"]:
        h_br = params['aktuelles_brutto'] / 2
        auf = h_br * (params['atz_aufstockung_pct'] / 100)
        brutto = h_br + auf
        income_details["Gehalt (ATZ)"] = h_br
        income_details["Aufstockung"] = auf
        steuer = berechne_progressionsvorbehalt(h_br * 12, auf * 12) / 12
        sv = h_br * 0.20
        netto = (h_br + auf) - steuer - sv
    else: # Rente
        b_g, st_b = 0, 0
        r_ant = berechne_rentensteuer_anteil(params['rentenbeginn'])
        for e in params['einnahmen']:
            if jahr >= e["start"] and jahr <= e["ende"]:
                val = e["betrag"]
                income_details[e["name"]] = val
                b_g += val
                if e["typ"] in ["Gesetzlich", "bAV"]:
                    st_b += val * (r_ant / 100)
                elif e["typ"] == "Privat":
                    st_b += val * 0.18
                else:
                    st_b += val
        brutto = b_g
        steuer = berechne_einkommensteuer(st_b * 12) / 12
        sv = b_g * 0.15
        netto = b_g - steuer - sv
        
    # Effektiver Steuersatz
    tax_rate = (steuer / brutto * 100) if brutto > 0 else 0
    
    # Ausgaben
    ausgaben = sum([
        params['ausgaben_input'][k] * (params['anpassungsfaktor_input'][k]/100 if p=="Rente" else 1.0) 
        for k in params['ausgaben_kategorien']
    ])
    
    res = {
        "Jahr": jahr,
        "Phase": p,
        "Brutto": brutto,
        "Steuern": steuer,
        "Steuersatz": tax_rate,
        "Sozialabgaben": sv,
        "Netto-Einkommen": netto,
        "Bedarf": ausgaben,
        "Überschuss/Defizit": netto - ausgaben
    }
    res.update(income_details) # Füge die einzelnen Quellen hinzu
    return res

def generate_trend_data(jahre, params):
    """Generiert ein DataFrame mit der zeitlichen Entwicklung."""
    data = [calculate_financials_for_year(j, params) for j in jahre]
    return pd.DataFrame(data)
