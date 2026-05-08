"""
Finanz-Engine für den Rente-O-Mat.
Berechnet Brutto, Steuern, Sozialabgaben und Netto für jedes Jahr und jede Lebensphase.
Unterstützt Inflation, Dynamisierung, differenzierte SV und korrekte Besteuerung.
"""
import pandas as pd
from logic.taxes import (
    berechne_einkommensteuer, berechne_progressionsvorbehalt,
    berechne_rentensteuer_anteil, berechne_soli, berechne_kirchensteuer,
    berechne_ertragsanteil, berechne_abgeltungsteuer, berechne_fuenftelregelung,
    ermittle_zve_naherung
)
from logic.sozialversicherung import (
    berechne_sv_aktiv, berechne_sv_atz, berechne_sv_rentner,
    berechne_vorsorgeaufwendungen_steuerlich
)
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


def _calculate_grv_components(jahr, e, params):
    """
    Zentrale Funktion zur Berechnung aller Komponenten einer gesetzlichen Rente.
    Berücksichtigt EP-Modus vs. Euro-Modus, Beitragsverlust und Abschläge.
    """
    from logic.rentenrecht import berechne_monate_frueher, berechne_ep_pro_jahr, berechne_beitragsverlust_logic
    from config import RENTENWERT_AKTUELL
    
    geburtsjahr = params.get('geburtsjahr', 1965)
    aktuelles_jahr = params.get('aktuelles_jahr', 2026)
    rentenanpassung_rate = params.get('rentenanpassung_rate', 0.0)
    rentenbeginn = params.get('rentenbeginn', geburtsjahr + 67)
    
    monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn)
    ep_pro_jahr = berechne_ep_pro_jahr(params.get('aktuelles_brutto', 0), jahr)
    
    if e.get("eingabe_modus") == "punkte":
        # Echte Hochrechnung: Startpunkte + (Jahre bis Beginn * EP_pro_Jahr)
        jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
        ep_bei_beginn = e.get("punkte", 0.0) + (jahre_bis_beginn * ep_pro_jahr)
        
        # K2: Rentenwert auf das Startjahr projizieren (wie DRV Renteninformation)
        rentenwert_projiziert = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        val_base = ep_bei_beginn * rentenwert_projiziert
        
        # Beitragsverlust (was man noch hätte sammeln können bis RAG)
        bv_res = berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr, rentenwert_projiziert)
        bv_jahr = bv_res["euro"]
    else:
        # Euro-Modus: Wir behandeln den Betrag als heutige Anwartschaft (wie DRV Info)
        # und projizieren ihn bis zum Startjahr.
        jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
        betrag_heute = e.get("betrag", 0.0)
        
        # K2: Auch Euro-Betrag projizieren (entspricht DRV Szenarien 1% / 2%)
        val_at_rag = betrag_heute * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        
        rentenwert_projiziert = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        bv_res = berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr, rentenwert_projiziert)
        bv_jahr = bv_res["euro"]
        
        # Basiswert reduzieren um Beitragsverlust (falls man früher geht)
        val_base = val_at_rag - bv_jahr
        
    # Dynamisierung (Rentenwert-Steigerung)
    # Wir dynamisieren ab dem Jahr des Rentenbeginns.
    start_der_rente = e.get("start", rentenbeginn)
    val_dyn = _dynamisiere_betrag(val_base, start_der_rente, jahr, rentenanpassung_rate)
    bv_dyn = _dynamisiere_betrag(bv_jahr, start_der_rente, jahr, rentenanpassung_rate)
    
    # Gesetzlicher Abschlag (0,3% pro Monat)
    abs_pct = min(14.4, monate_frueher * 0.3)
    abs_euro = val_dyn * (abs_pct / 100)
    
    return {
        "beitragsverlust": bv_dyn,
        "abschlag_betrag": abs_euro,
        "auszahlung_brutto": val_dyn - abs_euro,
        "basis_brutto": val_dyn # Brutto vor 0,3% Abschlag
    }


def calculate_financials_for_year(jahr, params):
    """
    Berechnet alle finanziellen Werte für ein spezifisches Jahr.
    params: Dictionary mit allen Nutzereingaben inkl. Inflations-/Dynamisierungsparameter.
    """
    phase = get_phase(jahr, params.get('atz_simulieren', False), params.get('atz_start', 9999), params.get('rentenbeginn', 2030))

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
    steuer_kapital = 0.0
    rentenabschlag_gesamt = 0.0
    beitragsverlust_gesamt = 0.0
    steuerpflichtiger_anteil_grv = 0.0
    kapitalzuwachs_sonder = 0.0

    if phase == "Aktiv":
        brutto = params.get('aktuelles_brutto', 0.0)
        income_details["Gehalt"] = brutto
        sv_result = berechne_sv_aktiv(brutto, jahr, kinderzahl)
        sv = sv_result["Gesamt"]
        
        # K1: Berechnung auf Basis des zu versteuernden Einkommens (zvE)
        va_jahr = berechne_vorsorgeaufwendungen_steuerlich(brutto, jahr, phase="Aktiv")
        zve_jahr = ermittle_zve_naherung(brutto * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va_jahr)
        
        steuer_ekst = berechne_einkommensteuer(zve_jahr, jahr) / 12
        soli = berechne_soli(steuer_ekst * 12) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12
        netto = brutto - steuer_ekst - soli - kist - sv

    elif phase in ["ATZ(A)", "ATZ(P)"]:
        h_br = params.get('aktuelles_brutto', 0.0) / 2
        auf = h_br * (params.get('atz_aufstockung_pct', 20) / 100)
        brutto = h_br + auf
        income_details["Gehalt (ATZ)"] = h_br
        income_details["Aufstockung"] = auf
        sv_result = berechne_sv_atz(h_br, jahr, kinderzahl)
        sv = sv_result["Gesamt"]
        
        # K1: zvE-Basis für ATZ (Progressionsvorbehalt auf Basis des zvE)
        va_jahr = berechne_vorsorgeaufwendungen_steuerlich(h_br, jahr, phase="Aktiv")
        zve_jahr = ermittle_zve_naherung(h_br * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va_jahr)
        
        steuer_ekst = berechne_progressionsvorbehalt(zve_jahr, auf * 12, jahr) / 12
        soli = berechne_soli(steuer_ekst * 12) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12
        netto = brutto - steuer_ekst - soli - kist - sv

    else:  # Rente
        b_g = 0.0
        st_b = 0.0
        r_ant = berechne_rentensteuer_anteil(params.get('rentenbeginn', 2030))
        alter_bei_rentenbeginn = params.get('rentenbeginn', 2030) - geburtsjahr
        ertragsanteil = berechne_ertragsanteil(alter_bei_rentenbeginn)
        sv_einnahmen = []
        kapitalertraege_jahressumme = 0.0
        steuerpflichtiger_anteil_grv = r_ant
        einmalzahlungen_bav = []

        for e in params.get('einnahmen', []):
            if jahr >= e.get("start", 0) and jahr <= e.get("ende", 9999):
                if e["typ"] == "Gesetzlich":
                    grv = _calculate_grv_components(jahr, e, params)
                    val = grv["basis_brutto"]
                    abschlag_betrag = grv["abschlag_betrag"]
                    beitragsverlust_jahr = grv["beitragsverlust"]
                    rentenabschlag_gesamt += abschlag_betrag
                    beitragsverlust_gesamt += beitragsverlust_jahr
                    income_details["Beitragsverlust"] = income_details.get("Beitragsverlust", 0) + beitragsverlust_jahr
                elif e["typ"] == "bAV":
                    val = _dynamisiere_betrag(e.get("betrag", 0.0), e.get("start", jahr), jahr, bav_anpassung_rate)
                    abschlag_betrag = 0.0
                elif e["typ"] == "bAV (Einmalzahlung)":
                    if jahr >= e["start"] and jahr < e["start"] + 10:
                        sv_einnahmen.append({"name": e["name"] + " (SV)", "betrag": e["betrag"] / 120, "typ": "bAV"})
                    if jahr == e["start"]:
                        einmalzahlungen_bav.append(e["betrag"])
                    continue
                elif e["typ"] == "Entnahmeplan (Vermögen)":
                    income_details[e["name"]] = e.get("betrag", 0.0)
                    b_g += e.get("betrag", 0.0)
                    continue
                else:
                    val = e.get("betrag", 0.0)
                    abschlag_betrag = 0.0

                val_nach_abschlag = val - abschlag_betrag
                income_details[e["name"]] = val
                b_g += val
                sv_einnahmen.append({"name": e["name"], "betrag": val_nach_abschlag, "typ": e["typ"]})

                if e["typ"] == "Gesetzlich":
                    st_b += val_nach_abschlag * (r_ant / 100)
                elif e["typ"] == "bAV":
                    st_b += val_nach_abschlag
                elif e["typ"] == "Privat":
                    st_b += val_nach_abschlag * (ertragsanteil / 100)
                elif e["typ"] == "Kapital":
                    kapitalertraege_jahressumme += val_nach_abschlag * 12
                else:
                    st_b += val_nach_abschlag

        brutto = b_g
        sv_result = berechne_sv_rentner(sv_einnahmen, jahr, kinderzahl)
        sv = sv_result["Gesamt"]
        
        # K1: zvE-Basis für Rente
        va_jahr = sv * 12 # SV-Beiträge der Rentner sind voll abziehbar
        zve_jahr = ermittle_zve_naherung(st_b * 12, jahr, phase="Rente", vorsorgeaufwendungen_jahr=va_jahr)
        
        steuer_ekst = berechne_einkommensteuer(zve_jahr, jahr) / 12
        soli_ekst = berechne_soli(steuer_ekst * 12) / 12
        kist_ekst = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12
        steuer_kapital = berechne_abgeltungsteuer(kapitalertraege_jahressumme, kirchensteuer_satz) / 12
        for ez in einmalzahlungen_bav:
            mehr_ekst = berechne_fuenftelregelung(st_b * 12, ez, jahr)
            mehr_soli = berechne_soli((steuer_ekst * 12) + mehr_ekst) - berechne_soli(steuer_ekst * 12)
            mehr_kist = berechne_kirchensteuer((steuer_ekst * 12) + mehr_ekst, kirchensteuer_satz) - berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz)
            kapitalzuwachs_sonder += ez - mehr_ekst - mehr_soli - mehr_kist
        soli = soli_ekst
        kist = kist_ekst
        steuer_ekst = steuer_ekst + steuer_kapital
        netto = brutto - steuer_ekst - soli - kist - sv - rentenabschlag_gesamt

    steuer_gesamt = steuer_ekst + soli + kist
    tax_rate = (steuer_gesamt / brutto * 100) if brutto > 0 else 0

    # Netto-Rente isolieren für Strategie-Check
    grv_netto = 0.0
    if phase == "Rente":
        payout_brutto = 0.0
        for e in params.get('einnahmen', []):
            if e.get("typ") == "Gesetzlich" and jahr >= e.get("start", 0) and jahr <= e.get("ende", 9999):
                grv_comp = _calculate_grv_components(jahr, e, params)
                payout_brutto += grv_comp["auszahlung_brutto"]
        if payout_brutto > 0:
            from logic.sozialversicherung import _get_sv_params, berechne_pv_satz
            svp = _get_sv_params(jahr)
            pvs = berechne_pv_satz(kinderzahl, svp)
            kv_grv = payout_brutto * (svp["rate_kv_rentner"] + svp["rate_kv_rentner_zusatz"])
            pv_grv = payout_brutto * pvs
            grv_netto = payout_brutto - kv_grv - pv_grv - (payout_brutto * (tax_rate / 100))

    ausgaben = 0.0
    ausgaben_details = {}
    for k in params.get('ausgaben_kategorien', []):
        basis_ausgabe = params.get('ausgaben_input', {}).get(k, 0.0)
        infl_ausgabe = _dynamisiere_betrag(basis_ausgabe, aktuelles_jahr, jahr, inflation_rate)
        if phase == "Rente":
            infl_ausgabe *= (params.get('anpassungsfaktor_input', {}).get(k, 100) / 100)
        ausgaben += infl_ausgabe
        ausgaben_details[f"EXP_{k}"] = infl_ausgabe

    res = {
        "Jahr": jahr, "Phase": phase, "Brutto": brutto, "EkSt": steuer_ekst, "Soli": soli, "KiSt": kist,
        "Steuern": steuer_gesamt, "Steuersatz": tax_rate, "Sozialabgaben": sv, "Netto-Einkommen": netto,
        "Netto-GRV": grv_netto, "Bedarf": ausgaben, "Überschuss/Defizit": netto - ausgaben,
        "Rentenabschlag": rentenabschlag_gesamt, "Beitragsverlust": beitragsverlust_gesamt,
        "Steuerpflichtiger_Rentenanteil": steuerpflichtiger_anteil_grv, "Kapitalzuwachs_Sonder": kapitalzuwachs_sonder
    }
    res.update(income_details)
    res.update(ausgaben_details)
    return res


def generate_trend_data(jahre, params):
    rate = params.get('rentenanpassung_rate', 0.0)
    print(f"\n[DEBUG] Engine: Generiere Trend-Daten...")
    print(f"[DEBUG] Rentenanpassung: {rate}%")
    
    data = [calculate_financials_for_year(j, params) for j in jahre]
    
    # Stichprobe für ein Rentenjahr (z.B. p['rentenbeginn'])
    rb = params.get('rentenbeginn', 2030)
    sample = next((d for d in data if d["Jahr"] == rb), None)
    if sample:
        print(f"[DEBUG] Jahr {rb}: Netto-Einkommen = {sample['Netto-Einkommen']:.2f}€")
    
    return pd.DataFrame(data).fillna(0)


def calculate_break_even_data(params):
    from logic.rentenrecht import berechne_regelaltersgrenze
    geburtsjahr = params.get("geburtsjahr", 1965)
    aktuelles_jahr = params.get("aktuelles_jahr", 2026)
    einnahmen = params.get("einnahmen", [])
    
    regel_jahre, _ = berechne_regelaltersgrenze(geburtsjahr)
    rag = geburtsjahr + regel_jahre
    
    params_a = params.copy()
    params_b = params.copy()
    params_b["rentenbeginn"] = rag
    
    einnahmen_b = []
    for e in einnahmen:
        e_copy = e.copy()
        if e.get("typ") == "Gesetzlich": e_copy["start"] = rag
        einnahmen_b.append(e_copy)
    params_b["einnahmen"] = einnahmen_b

    jahre = list(range(aktuelles_jahr, geburtsjahr + 101))
    kum_a, kum_b = 0.0, 0.0
    results = []
    
    for j in jahre:
        res_a = calculate_financials_for_year(j, params_a)
        res_b = calculate_financials_for_year(j, params_b)
        n_a, n_b = res_a.get("Netto-GRV", 0.0), res_b.get("Netto-GRV", 0.0)
        kum_a += n_a * 12
        kum_b += n_b * 12
        results.append({"Jahr": j, "Alter": j - geburtsjahr, "Netto_A": n_a, "Netto_B": n_b, "Kumuliert_A": kum_a, "Kumuliert_B": kum_b})
        
    df = pd.DataFrame(results)
    be_row = df[df["Kumuliert_B"] > df["Kumuliert_A"]].head(1)
    be_jahr = int(be_row["Jahr"].values[0]) if not be_row.empty else None
    be_alter = int(be_row["Alter"].values[0]) if not be_row.empty else None
    return df, be_jahr, be_alter
