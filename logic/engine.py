"""
Finanz-Engine für den Rente-O-Mat.
Berechnet Brutto, Steuern, Sozialabgaben und Netto für jedes Jahr und jede Lebensphase.
Unterstützt Inflation, Dynamisierung, differenzierte SV und korrekte Besteuerung.
"""
import pandas as pd
from logic.taxes import (
    berechne_einkommensteuer, berechne_progressionsvorbehalt,
    berechne_rentensteuer_anteil, berechne_soli, berechne_kirchensteuer,
    berechne_ertragsanteil, berechne_abgeltungsteuer, berechne_fuenftelregelung
)
from logic.sozialversicherung import berechne_sv_aktiv, berechne_sv_atz, berechne_sv_rentner
from logic.rentenrecht import berechne_monate_frueher


def get_phase(jahr, atz_simulieren, atz_start, rentenbeginn):
    """Ermittelt die Lebensphase für ein gegebenes Jahr inkl. ATZ-Split."""
    if jahr < rentenbeginn:
        if atz_simulieren and jahr >= atz_start:
            # ATZ-Split: Hälftige Aufteilung der Gesamtdauer
            dauer = rentenbeginn - atz_start
            mitte = atz_start + (dauer / 2)
            if jahr < mitte:
                return "ATZ(A)"  # Aktivphase
            else:
                return "ATZ(P)"  # Passivphase
        else:
            return "Aktiv"
    else:
        return "Rente"


def _dynamisiere_betrag(basisbetrag, startjahr, aktuelles_jahr, steigerung_pct):
    """Erhöht einen Betrag jährlich um einen Prozentsatz ab dem Startjahr."""
    if aktuelles_jahr <= startjahr or steigerung_pct == 0:
        return basisbetrag
    jahre = aktuelles_jahr - startjahr
    return basisbetrag * (1 + steigerung_pct / 100) ** jahre


def calculate_financials_for_year(jahr, params):
    """
    Berechnet alle finanziellen Werte für ein spezifisches Jahr.
    params: Dictionary mit allen Nutzereingaben inkl. Inflations-/Dynamisierungsparameter.
    """
    phase = get_phase(jahr, params['atz_simulieren'], params['atz_start'], params['rentenbeginn'])

    # Parameter auslesen (mit Defaults für Rückwärtskompatibilität)
    kinderzahl = params.get('kinderzahl', 0)
    kirchensteuer_satz = params.get('kirchensteuer_satz', 0.0)
    inflation_rate = params.get('inflation_rate', 0.0)
    rentenanpassung_rate = params.get('rentenanpassung_rate', 0.0)
    bav_anpassung_rate = params.get('bav_anpassung_rate', 0.0)
    aktuelles_jahr = params.get('aktuelles_jahr', 2026)
    geburtsjahr = params.get('geburtsjahr', 1965)

    # Einkommens-Details für das Diagramm
    income_details = {}
    brutto = 0.0
    steuer_ekst = 0.0
    soli = 0.0
    kist = 0.0
    sv = 0.0
    netto = 0.0
    steuer_kapital = 0.0  # Separate Abgeltungsteuer
    rentenabschlag_gesamt = 0.0
    steuerpflichtiger_anteil_grv = 0.0
    kapitalzuwachs_sonder = 0.0

    if phase == "Aktiv":
        brutto = params['aktuelles_brutto']
        income_details["Gehalt"] = brutto

        # Sozialabgaben (AN-Anteil)
        sv_result = berechne_sv_aktiv(brutto, jahr, kinderzahl)
        sv = sv_result["Gesamt"]

        # Steuer (vereinfacht: Brutto * 12 als zvE)
        steuer_ekst = berechne_einkommensteuer(brutto * 12, jahr) / 12
        soli = berechne_soli(steuer_ekst * 12) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12

        netto = brutto - steuer_ekst - soli - kist - sv

    elif phase in ["ATZ(A)", "ATZ(P)"]:
        h_br = params['aktuelles_brutto'] / 2
        auf = h_br * (params['atz_aufstockung_pct'] / 100)
        brutto = h_br + auf
        income_details["Gehalt (ATZ)"] = h_br
        income_details["Aufstockung"] = auf

        # Sozialabgaben nur auf das hälftige Brutto (Aufstockung ist beitragsfrei)
        sv_result = berechne_sv_atz(h_br, jahr, kinderzahl)
        sv = sv_result["Gesamt"]

        # Steuer mit Progressionsvorbehalt auf die Aufstockung
        steuer_ekst = berechne_progressionsvorbehalt(h_br * 12, auf * 12, jahr) / 12
        soli = berechne_soli(steuer_ekst * 12) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12

        netto = brutto - steuer_ekst - soli - kist - sv

    else:  # Rente
        b_g = 0.0
        st_b = 0.0  # Steuerpflichtiger Betrag (für progressive EkSt)
        r_ant = berechne_rentensteuer_anteil(params['rentenbeginn'])
        alter_bei_rentenbeginn = params['rentenbeginn'] - geburtsjahr
        ertragsanteil = berechne_ertragsanteil(alter_bei_rentenbeginn)

        # Einnahmen mit Dynamisierung sammeln
        sv_einnahmen = []  # Für differenzierte SV-Berechnung
        kapitalertraege_jahressumme = 0.0
        steuerpflichtiger_anteil_grv = r_ant
        einmalzahlungen_bav = []

        for e in params['einnahmen']:
            if jahr >= e["start"] and jahr <= e["ende"]:
                val = e["betrag"]
                abschlag_betrag = 0.0

                # Dynamisierung je nach Typ
                if e["typ"] == "Gesetzlich":
                    if e.get("eingabe_modus") == "punkte":
                        from config import RENTENWERT_AKTUELL
                        val = e.get("punkte", 0.0) * RENTENWERT_AKTUELL
                        
                    val = _dynamisiere_betrag(val, e["start"], jahr, rentenanpassung_rate)
                    monate_frueher = berechne_monate_frueher(geburtsjahr, params['rentenbeginn'])
                    abschlag_pct = min(14.4, monate_frueher * 0.3)
                    abschlag_betrag = val * (abschlag_pct / 100)
                    rentenabschlag_gesamt += abschlag_betrag
                elif e["typ"] == "bAV":
                    val = _dynamisiere_betrag(val, e["start"], jahr, bav_anpassung_rate)
                elif e["typ"] == "bAV (Einmalzahlung)":
                    if jahr >= e["start"] and jahr < e["start"] + 10:
                        sv_einnahmen.append({"name": e["name"] + " (SV)", "betrag": e["betrag"] / 120, "typ": "bAV"})
                    if jahr == e["start"]:
                        einmalzahlungen_bav.append(e["betrag"])
                    continue # Keine laufende Einnahme im Sankey
                elif e["typ"] == "Entnahmeplan (Vermögen)":
                    income_details[e["name"]] = e["betrag"]
                    b_g += e["betrag"]
                    continue # Steuer- und abgabenfrei

                val_nach_abschlag = val - abschlag_betrag
                income_details[e["name"]] = val
                b_g += val
                sv_einnahmen.append({"name": e["name"], "betrag": val_nach_abschlag, "typ": e["typ"]})

                # Steuerpflichtiger Anteil je nach Typ
                if e["typ"] == "Gesetzlich":
                    st_b += val_nach_abschlag * (r_ant / 100)
                elif e["typ"] == "bAV":
                    # bAV: 100% nachgelagert steuerpflichtig (§ 22 Nr. 5 EStG)
                    st_b += val_nach_abschlag
                elif e["typ"] == "Privat":
                    # Ertragsanteil nach Alter bei Rentenbeginn (§ 22 EStG)
                    st_b += val_nach_abschlag * (ertragsanteil / 100)
                elif e["typ"] == "Kapital":
                    # Kapitalerträge separat über Abgeltungsteuer
                    kapitalertraege_jahressumme += val_nach_abschlag * 12
                else:  # Sonstiges
                    st_b += val_nach_abschlag

        brutto = b_g

        # SV für Rentner (differenziert nach Einkommensquelle)
        sv_result = berechne_sv_rentner(sv_einnahmen, jahr, kinderzahl)
        sv = sv_result["Gesamt"]

        # EkSt auf den steuerpflichtigen Anteil (ohne Kapitalerträge)
        steuer_ekst = berechne_einkommensteuer(st_b * 12, jahr) / 12
        soli_ekst = berechne_soli(steuer_ekst * 12) / 12
        kist_ekst = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12

        # Abgeltungsteuer auf Kapitalerträge (separat)
        steuer_kapital = berechne_abgeltungsteuer(
            kapitalertraege_jahressumme, kirchensteuer_satz
        ) / 12

        # Fünftelregelung für Einmalzahlungen
        for ez in einmalzahlungen_bav:
            mehr_ekst = berechne_fuenftelregelung(st_b * 12, ez, jahr)
            mehr_soli = berechne_soli((steuer_ekst * 12) + mehr_ekst) - berechne_soli(steuer_ekst * 12)
            mehr_kist = berechne_kirchensteuer((steuer_ekst * 12) + mehr_ekst, kirchensteuer_satz) - berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz)
            
            # Netto fließt als steuerfreier Sonderzuwachs ins Vermögen (Tab 2)
            netto_ez = ez - mehr_ekst - mehr_soli - mehr_kist
            kapitalzuwachs_sonder += netto_ez

        soli = soli_ekst  # Soli auf Kapital ist schon in berechne_abgeltungsteuer enthalten
        kist = kist_ekst
        steuer_ekst = steuer_ekst + steuer_kapital

        netto = brutto - steuer_ekst - soli - kist - sv - rentenabschlag_gesamt

    # Gesamtsteuer für Anzeige
    steuer_gesamt = steuer_ekst + soli + kist

    # Effektiver Steuersatz
    tax_rate = (steuer_gesamt / brutto * 100) if brutto > 0 else 0

    # Ausgaben mit Inflation und Anpassungsfaktor
    ausgaben = 0.0
    for k in params['ausgaben_kategorien']:
        basis_ausgabe = params['ausgaben_input'][k]
        # Inflation auf Ausgaben anwenden
        inflationierte_ausgabe = _dynamisiere_betrag(basis_ausgabe, aktuelles_jahr, jahr, inflation_rate)
        # Anpassungsfaktor für Rente (und optional ATZ(P))
        if phase == "Rente":
            inflationierte_ausgabe *= (params['anpassungsfaktor_input'][k] / 100)
        ausgaben += inflationierte_ausgabe

    res = {
        "Jahr": jahr,
        "Phase": phase,
        "Brutto": brutto,
        "EkSt": steuer_ekst,
        "Soli": soli,
        "KiSt": kist,
        "Steuern": steuer_gesamt,
        "Steuersatz": tax_rate,
        "Sozialabgaben": sv,
        "Netto-Einkommen": netto,
        "Bedarf": ausgaben,
        "Überschuss/Defizit": netto - ausgaben,
        "Rentenabschlag": rentenabschlag_gesamt,
        "Steuerpflichtiger_Rentenanteil": steuerpflichtiger_anteil_grv,
        "Kapitalzuwachs_Sonder": kapitalzuwachs_sonder
    }
    res.update(income_details)  # Füge die einzelnen Quellen hinzu
    return res


def generate_trend_data(jahre, params):
    """Generiert ein DataFrame mit der zeitlichen Entwicklung."""
    data = [calculate_financials_for_year(j, params) for j in jahre]
    df = pd.DataFrame(data)
    # NaN-Werte auffüllen (Einkommensquellen die nicht in jedem Jahr aktiv sind)
    df = df.fillna(0)
    return df
