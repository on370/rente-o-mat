import pandas as pd
from logic.taxes import berechne_einkommensteuer, berechne_progressionsvorbehalt, berechne_rentensteuer_anteil

def get_phase(jahr, atz_simulieren, atz_start, rentenbeginn):
    """Ermittelt die Lebensphase für ein gegebenes Jahr inkl. ATZ-Split."""
    if jahr < rentenbeginn:
        if atz_simulieren and jahr >= atz_start:
            # ATZ-Split: Hälftige Aufteilung der Gesamtdauer
            dauer = rentenbeginn - atz_start
            mitte = atz_start + (dauer / 2)
            if jahr < mitte:
                return "ATZ(A)" # Aktivphase
            else:
                return "ATZ(P)" # Passivphase
        else:
            return "Aktiv"
    else:
        return "Rente"

# --- Konstanten für Sozialabgaben 2024 ---
BBG_KV_MONATLICH = 5175.0
BBG_RV_MONATLICH = 7550.0

# Prozentsätze (Arbeitnehmeranteile inkl. Zusatzbeiträge)
RATE_KV_AN = 0.0815  # 7,3% + 0,85% (halber Zusatzbeitrag)
RATE_PV_AN = 0.023   # Durchschnittswert
RATE_RV_AN = 0.093   # 18,6% / 2
RATE_ALV_AN = 0.013  # 2,6% / 2

def calculate_financials_for_year(jahr, params):
    """
    Berechnet alle finanziellen Werte für ein spezifisches Jahr.
    params: Dictionary mit allen Nutzereingaben.
    """
    p = get_phase(jahr, params['atz_simulieren'], params['atz_start'], params['rentenbeginn'])
    
    # Einkommens-Details für das Diagramm
    income_details = {}
    brutto, steuer, sv, netto = 0.0, 0.0, 0.0, 0.0
    
    if p == "Aktiv":
        brutto = params['aktuelles_brutto']
        income_details["Gehalt"] = brutto
        # Sozialabgaben (AN-Anteil)
        sv_kv_pv = min(brutto, BBG_KV_MONATLICH) * (RATE_KV_AN + RATE_PV_AN)
        sv_rv_alv = min(brutto, BBG_RV_MONATLICH) * (RATE_RV_AN + RATE_ALV_AN)
        sv = sv_kv_pv + sv_rv_alv
        # Steuer (Vorsorgeaufwendungen vereinfacht berücksichtigt)
        steuer = berechne_einkommensteuer(brutto * 12) / 12
        netto = brutto - steuer - sv

    elif p in ["ATZ(A)", "ATZ(P)"]:
        h_br = params['aktuelles_brutto'] / 2
        auf = h_br * (params['atz_aufstockung_pct'] / 100)
        brutto = h_br + auf
        income_details["Gehalt (ATZ)"] = h_br
        income_details["Aufstockung"] = auf
        # Sozialabgaben nur auf das hälftige Brutto (Aufstockung ist beitragsfrei)
        sv_kv_pv = min(h_br, BBG_KV_MONATLICH) * (RATE_KV_AN + RATE_PV_AN)
        sv_rv_alv = min(h_br, BBG_RV_MONATLICH) * (RATE_RV_AN + RATE_ALV_AN)
        sv = sv_kv_pv + sv_rv_alv
        # Steuer mit Progressionsvorbehalt auf die Aufstockung
        steuer = berechne_progressionsvorbehalt(h_br * 12, auf * 12) / 12
        netto = (h_br + auf) - steuer - sv

    else: # Rente
        b_g, st_b = 0, 0
        r_ant = berechne_rentensteuer_anteil(params['rentenbeginn'])
        for e in params['einnahmen']:
            if jahr >= e["start"] and jahr <= e["ende"]:
                val = e["betrag"]
                income_details[e["name"]] = val
                b_g += val
                # Steuerpflichtiger Anteil je nach Typ
                if e["typ"] in ["Gesetzlich", "bAV"]:
                    st_b += val * (r_ant / 100)
                elif e["typ"] == "Privat":
                    st_b += val * 0.18 # Ertragsanteil (pauschalisiert)
                else:
                    st_b += val
        
        brutto = b_g
        # SV für Rentner (KVdR): KV-Beitrag (ca. 8.15%) + PV-Beitrag (ca. 3.4%)
        # Vereinfachung: Gilt primär für gesetzliche Renten/bAV
        sv = min(brutto, BBG_KV_MONATLICH) * (RATE_KV_AN + 0.034)
        steuer = berechne_einkommensteuer(st_b * 12) / 12
        netto = brutto - steuer - sv
        
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
