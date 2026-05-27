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
from config import RENTENWERT_AKTUELL


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
    """Erhöht einen Betrag jährlich um einen Prozentsatz ab dem Startjahr. (Harte Jahressprünge)"""
    jahre = int(aktuelles_jahr) - int(startjahr)
    if jahre <= 0 or steigerung_pct == 0:
        return basisbetrag
    return basisbetrag * (1 + steigerung_pct / 100) ** jahre


def _calculate_grv_components(jahr_float, e, params):
    """
    Zentrale Funktion zur Berechnung aller Komponenten einer gesetzlichen Rente.
    Berücksichtigt EP-Modus vs. Euro-Modus, Beitragsverlust und Abschläge.
    K7-Fix: Berücksichtigt 80% EP-Aufstockung während der ATZ.
    """
    from logic.rentenrecht import berechne_monate_frueher, berechne_ep_pro_jahr, berechne_beitragsverlust_logic
    from config import RENTENWERT_AKTUELL
    
    geburtsjahr = params.get('geburtsjahr', 1965)
    aktuelles_jahr = params.get('aktuelles_jahr', 2026)
    rentenanpassung_rate = params.get('rentenanpassung_rate', 0.0)
    rentenbeginn = params.get('rentenbeginn', geburtsjahr + 67)
    
    monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn)
    brutto_voll = params.get('aktuelles_brutto', 0)
    ep_pro_jahr_voll = berechne_ep_pro_jahr(brutto_voll, aktuelles_jahr)
    
    if e.get("eingabe_modus") == "punkte":
        # K7: Detaillierte EP-Akkumulation bis Rentenbeginn
        ep_bei_beginn = e.get("punkte", 0.0)
        
        # Simuliere Jahre von heute bis Beginn
        for j_sim in range(aktuelles_jahr, int(rentenbeginn)):
            phase_sim = get_phase(j_sim + 0.5, params.get('atz_simulieren', False), params.get('atz_start', 9999), rentenbeginn)
            if phase_sim == "Aktiv":
                ep_bei_beginn += ep_pro_jahr_voll
            elif "ATZ" in phase_sim:
                # K7: In ATZ werden i.d.R. Beiträge auf Basis von 80% des Vollzeit-Bruttos gezahlt
                ep_bei_beginn += ep_pro_jahr_voll * 0.8
        
        # Bruchstück für das letzte Jahr vor Rentenbeginn (falls nicht glatt 01.01.)
        rest_jahr = rentenbeginn - int(rentenbeginn)
        if rest_jahr > 0:
            phase_sim = get_phase(rentenbeginn - 0.01, params.get('atz_simulieren', False), params.get('atz_start', 9999), rentenbeginn)
            factor = 0.8 if "ATZ" in phase_sim else 1.0
            ep_bei_beginn += ep_pro_jahr_voll * factor * rest_jahr

        # K2: Rentenwert auf das Startjahr projizieren
        jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
        rentenwert_projiziert = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        val_base = ep_bei_beginn * rentenwert_projiziert
        
        # Beitragsverlust (was man noch hätte sammeln können bis RAG)
        bv_res = berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr_voll, rentenwert_projiziert)
        bv_jahr = bv_res["euro"]
        val_at_rag = val_base + bv_jahr
    else:
        # Euro-Modus: Wie bisher (vereinfacht)
        jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
        betrag_heute = e.get("betrag", 0.0)
        val_at_rag = betrag_heute * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        rentenwert_projiziert = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
        bv_res = berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr_voll, rentenwert_projiziert)
        bv_jahr = bv_res["euro"]
        val_base = val_at_rag - bv_jahr
        
    # Dynamisierung (Rentenwert-Steigerung ab Rentenbeginn)
    start_der_rente = e.get("start", rentenbeginn)
    val_dyn = _dynamisiere_betrag(val_base, start_der_rente, jahr_float, rentenanpassung_rate)
    bv_dyn = _dynamisiere_betrag(bv_jahr, start_der_rente, jahr_float, rentenanpassung_rate)
    
    # Gesetzlicher Abschlag (0,3% pro Monat)
    abs_pct = min(14.4, monate_frueher * 0.3)
    abs_euro = val_dyn * (abs_pct / 100)
    pot_dyn = _dynamisiere_betrag(val_at_rag, start_der_rente, jahr_float, rentenanpassung_rate)
    
    return {
        "beitragsverlust": bv_dyn,
        "abschlag_betrag": abs_euro,
        "basis_brutto": val_dyn - abs_euro,
        "potential": pot_dyn
    }


def calculate_financials_for_year(jahr_float, params, assets_state=None, segment_weight=1.0, start_t=None, end_t=None):
    """
    Zentrale Berechnungspipeline für ein spezifisches Jahr.
    1. Einnahmen (Aktiv, ATZ oder Rente)
    2. Assets (Rendite, Steuern, Entnahmen)
    3. Ausgaben (Basis, Dynamik, befristete Posten, Einmalausgaben)
    """
    if start_t is None:
        start_t = float(int(jahr_float))
    if end_t is None:
        end_t = float(int(jahr_float)) + 1.0
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

    aktuelles_jahr = params.get('aktuelles_jahr', 2026)
    geburtsjahr = params.get('geburtsjahr', 1965)
    rentenbeginn = params.get('rentenbeginn', 2030)
    kinderzahl = params.get('kinderzahl', 0)
    kirchensteuer_satz = params.get('kirchensteuer_satz', 0.0)
    inflation_rate = params.get('inflation_rate', 2.0)
    rentenanpassung_rate = params.get('rentenanpassung_rate', 2.0)
    bav_anpassung_rate = params.get('bav_anpassung_rate', 1.0)
    
    jahr = int(jahr_float)
    phase = get_phase(jahr_float, params.get('atz_simulieren', False), params.get('atz_start', 9999), rentenbeginn)

    # --- INITIALISIERUNG ---
    sparer_pausch_frei = 1000.0
    b_g = 0.0  # Brutto gesamt (monatlich)
    st_b = 0.0 # Steuer-Basis (monatlich)
    income_details = {}
    rentenabschlag_gesamt = 0.0
    beitragsverlust_gesamt = 0.0
    potential_gesamt = 0.0
    kapitalzuwachs_sonder = 0.0
    sv = 0.0
    steuer_ekst = 0.0
    soli = 0.0
    kist = 0.0
    netto = 0.0
    grv_netto = 0.0

    gehalts_dyn = params.get('gehalts_dynamik', 1.0) / 100
    
    # --- 1. HAUPTEINNAHMEN (GEHALT ODER RENTE) ---
    if phase == "Aktiv" or "ATZ" in phase:
        # Dynamisierung Gehalt (K6-Fix)
        jahre_seit_start = max(0, jahr - params.get('aktuelles_jahr', 2026))
        brutto_base = params.get('aktuelles_brutto', 0.0)
        brutto_dyn = brutto_base * (1 + gehalts_dyn) ** jahre_seit_start

        if phase == "Aktiv":
            brutto_st = brutto_dyn
            brutto_auszahlung = brutto_st
            income_details["Gehalt"] = brutto_st
            from logic.sozialversicherung import berechne_sv_aktiv
            sv_dict = berechne_sv_aktiv(brutto_st, jahr, kinderzahl)
            aufstockung = 0.0
        else: # ATZ
            h_br = brutto_dyn / 2
            aufstockung = h_br * (params.get('atz_aufstockung_pct', 20) / 100)
            brutto_st = h_br
            brutto_auszahlung = h_br + aufstockung
            income_details["Gehalt (ATZ)"] = h_br
            income_details["Aufstockung"] = aufstockung
            from logic.sozialversicherung import berechne_sv_atz
            sv_dict = berechne_sv_atz(h_br, jahr, kinderzahl)

        b_g, sv = brutto_auszahlung, sv_dict["Gesamt"]
        va_jahr = berechne_vorsorgeaufwendungen_steuerlich(brutto_st, jahr, phase="Aktiv")
        zve_jahr = ermittle_zve_naherung(brutto_st * 12, jahr, phase="Aktiv", vorsorgeaufwendungen_jahr=va_jahr)
        
        from logic.taxes import berechne_einkommensteuer, berechne_progressionsvorbehalt
        if aufstockung > 0:
            steuer_ekst = berechne_progressionsvorbehalt(zve_jahr, aufstockung * 12, jahr) / 12
        else:
            steuer_ekst = berechne_einkommensteuer(zve_jahr, jahr) / 12
            
        soli = berechne_soli(steuer_ekst * 12, jahr=jahr) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12
        netto = b_g - steuer_ekst - soli - kist - sv

    else: # Phase: Rente
        from logic.taxes import berechne_rentensteuer_anteil, berechne_ertragsanteil, berechne_einkommensteuer, berechne_abgeltungsteuer, berechne_fuenftelregelung
        from logic.sozialversicherung import berechne_sv_rentner
        
        r_ant = berechne_rentensteuer_anteil(int(rentenbeginn))
        alter_bei_rentenbeginn = int(rentenbeginn - geburtsjahr)
        ertragsanteil = berechne_ertragsanteil(alter_bei_rentenbeginn)
        sv_einnahmen, einmalzahlungen_bav = [], []
        kapitalertraege_jahressumme = 0.0

        for e in params.get('einnahmen', []):
            if jahr_float >= e.get("start", 0) and jahr_float <= e.get("ende", 9999):
                if e["typ"] == "Gesetzlich":
                    grv = _calculate_grv_components(jahr_float, e, params)
                    val = grv["basis_brutto"]
                    rentenabschlag_gesamt += grv["abschlag_betrag"]
                    beitragsverlust_gesamt += grv["beitragsverlust"]
                    potential_gesamt += grv["potential"]
                    income_details["Beitragsverlust"] = income_details.get("Beitragsverlust", 0) + grv["beitragsverlust"]
                elif e["typ"] == "bAV":
                    val = _dynamisiere_betrag(e.get("betrag", 0.0), e.get("start", jahr), jahr, bav_anpassung_rate)
                elif e["typ"] == "bAV (Einmalzahlung)":
                    if jahr_float >= e["start"] and jahr_float < e["start"] + 10:
                        sv_einnahmen.append({"name": e["name"] + " (SV)", "betrag": e["betrag"] / 120, "typ": "bAV"})
                    if int(jahr_float) == int(e["start"]): einmalzahlungen_bav.append(e["betrag"])
                    continue
                elif e["typ"] == "Entnahmeplan (Vermögen)":
                    found = any(a_s["name"] == e["name"] for a_s in (assets_state or []))
                    if not found:
                        income_details[e["name"]] = e["betrag"]
                        b_g += e["betrag"]
                    continue
                else:
                    val = e.get("betrag", 0.0)

                income_details[e["name"]] = val
                b_g += val
                sv_einnahmen.append({"name": e["name"], "betrag": val, "typ": e["typ"]})

                # Steuer-Basis
                if e["typ"] == "Gesetzlich": st_b += val * (r_ant / 100)
                elif e["typ"] == "bAV": st_b += val
                elif e["typ"] == "Privat": st_b += val * (ertragsanteil / 100)
                elif e["typ"] == "Kapital": kapitalertraege_jahressumme += val * 12
                else: st_b += val

        sv_res = berechne_sv_rentner(sv_einnahmen, jahr, kinderzahl)
        sv = sv_res["Gesamt"]
        va_jahr = berechne_vorsorgeaufwendungen_steuerlich(st_b, jahr, phase="Rente", kinderzahl=kinderzahl, einnahmen_liste=sv_einnahmen)
        zve_jahr = ermittle_zve_naherung(st_b * 12, jahr, phase="Rente", vorsorgeaufwendungen_jahr=va_jahr)
        
        steuer_ekst = berechne_einkommensteuer(zve_jahr, jahr) / 12
        soli = berechne_soli(steuer_ekst * 12, jahr=jahr) / 12
        kist = berechne_kirchensteuer(steuer_ekst * 12, kirchensteuer_satz) / 12
        
        # M6: Konsistenter Sparerpauschbetrag (Rente-Einnahme)
        st_pfl_kapital = max(0.0, kapitalertraege_jahressumme - sparer_pausch_frei)
        sparer_pausch_frei = max(0.0, sparer_pausch_frei - kapitalertraege_jahressumme)
        steuer_kapital = berechne_abgeltungsteuer(st_pfl_kapital, kirchensteuer_satz, sparerpauschbetrag=0) / 12
        steuer_ekst += steuer_kapital
        
        for ez in einmalzahlungen_bav:
            m_ekst = berechne_fuenftelregelung(st_b * 12, ez, jahr)
            kapitalzuwachs_sonder += ez - m_ekst 
            
        netto = b_g - steuer_ekst - soli - kist - sv
        # Isolierte Netto-GRV für Strategie-Check (K5-Fix)
        grv_brutto_mtl = income_details.get("Gesetzliche Rente", 0.0)
        if grv_brutto_mtl > 0:
            sv_grv = berechne_sv_rentner([{"name": "GRV", "betrag": grv_brutto_mtl, "typ": "Gesetzlich"}], jahr, kinderzahl)["Gesamt"]
            st_b_grv = grv_brutto_mtl * (r_ant / 100)
            zve_grv = ermittle_zve_naherung(st_b_grv * 12, jahr, phase="Rente", vorsorgeaufwendungen_jahr=sv_grv * 12)
            steuer_grv_full = berechne_einkommensteuer(zve_grv, jahr)
            steuer_grv = steuer_grv_full / 12
            soli_grv = berechne_soli(steuer_grv_full, jahr=jahr) / 12
            kist_grv = berechne_kirchensteuer(steuer_grv_full, kirchensteuer_satz) / 12
            grv_netto = grv_brutto_mtl - sv_grv - steuer_grv - soli_grv - kist_grv
        else:
            grv_netto = 0.0

    # --- 2. ASSETS-SIMULATION ---
    asset_netto_einnahmen = 0.0
    asset_results = {}
    if assets_state is not None:
        from logic.taxes import berechne_abgeltungsteuer
        for a_s in assets_state:
            cfg = a_s["config"]
            gewinn = a_s["kapital"] * (cfg["rendite_pa"] / 100.0)
            st = 0.0
            if cfg["steuertyp"] == "abgeltung":
                st_pfl = max(0.0, gewinn - sparer_pausch_frei)
                sparer_pausch_frei = max(0.0, sparer_pausch_frei - gewinn)
                st = berechne_abgeltungsteuer(st_pfl, kirchensteuer_satz, sparerpauschbetrag=0)
            elif cfg["steuertyp"] == "teilfreistellung":
                tfs = cfg.get("teilfreistellung_pct", 30.0)
                br_gew = gewinn * (1 - tfs / 100.0)
                st_pfl = max(0.0, br_gew - sparer_pausch_frei)
                sparer_pausch_frei = max(0.0, sparer_pausch_frei - br_gew)
                st = berechne_abgeltungsteuer(st_pfl, kirchensteuer_satz, sparerpauschbetrag=0)
            
            a_s["kapital"] += gewinn - st
            if cfg.get("entnahme_aktiv") and jahr_float >= cfg.get("entnahme_start", 0) and jahr_float <= cfg.get("entnahme_ende", 9999):
                # Unterscheidung: Fixer Betrag vs. Kapitalverzehr (Annuität)
                if cfg.get("entnahme_modus") == "verzehr":
                    rem_years = max(1, int(cfg.get("entnahme_ende", jahr_float) - jahr_float + 1))
                    if rem_years > 0:
                        r = cfg.get("rendite_pa", 0.0) / 100
                        if r > 0:
                            # Annuitätenformel (nachschüssig, da Verzinsung bereits erfolgt)
                            # Rate = K * (r / (1 - (1+r)^-n))
                            jahres_e = a_s["kapital"] * (r / (1 - (1+r)**(-rem_years)))
                        else:
                            jahres_e = a_s["kapital"] / rem_years
                        ent_mtl = jahres_e / 12
                    else:
                        ent_mtl = 0.0
                else:
                    ent_mtl = cfg.get("entnahme_betrag_mtl", 0.0)

                eff_e_jahr = min(ent_mtl * 12, a_s["kapital"])
                a_s["kapital"] -= eff_e_jahr
                ent_actual_mtl = eff_e_jahr / 12
                asset_netto_einnahmen += ent_actual_mtl
                income_details[f"Entnahme: {cfg['name']}"] = ent_actual_mtl
            
            asset_results[f"ASSET_VAL_{cfg['name']}"] = a_s["kapital"]

    netto += asset_netto_einnahmen

    # --- 3. AUSGABEN ---
    ausgaben = 0.0
    ausgaben_details = {}
    for k in params.get('ausgaben_kategorien', []):
        bas = params.get('ausgaben_input', {}).get(k, 0.0)
        val = _dynamisiere_betrag(bas, aktuelles_jahr, jahr_float, inflation_rate)
        if phase == "Rente": val *= (params.get('anpassungsfaktor_input', {}).get(k, 100) / 100)
        ausgaben += val
        ausgaben_details[f"EXP_{k}"] = val

    for ba in params.get('befristete_ausgaben', []):
        if jahr_float >= ba.get('start', 0) and jahr_float <= ba.get('ende', 9999):
            b = ba['betrag_mtl']
            if ba.get('inflationsgebunden', False): b = _dynamisiere_betrag(b, aktuelles_jahr, jahr_float, inflation_rate)
            kat = ba.get('kategorie', ba['name'])
            ausgaben_details[f"EXP_{kat}"] = ausgaben_details.get(f"EXP_{kat}", 0) + b
            ausgaben += b

    for ea in params.get('einmalige_ausgaben', []):
        t_event = float(ea['jahr']) + (int(ea.get('monat', 1)) - 1) / 12.0
        if start_t <= t_event < end_t:
            b = ea['betrag']
            if ea.get('inflationsgebunden', True):
                b = _dynamisiere_betrag(b, aktuelles_jahr, ea['jahr'], inflation_rate)
            
            b_eff = b / (12.0 * segment_weight)
            kat = ea.get('kategorie', '')
            final_kat = kat if kat else ea['name']
            ausgaben_details[f"EXP_{final_kat}"] = ausgaben_details.get(f"EXP_{final_kat}", 0) + b_eff
            ausgaben += b_eff

    steuer_g = steuer_ekst + soli + kist
    tax_rate = (steuer_g / b_g * 100) if b_g > 0 else 0
    res = {
        "Jahr": jahr, "Phase": phase, "Brutto": b_g, "EkSt": steuer_ekst, "Soli": soli, "KiSt": kist,
        "Steuern": steuer_g, "Steuersatz": tax_rate,
        "Sozialabgaben": sv, "Netto-Einkommen": netto, "Netto-GRV": grv_netto, "Bedarf": ausgaben,
        "Überschuss/Defizit": netto - ausgaben, "Rentenabschlag": rentenabschlag_gesamt,
        "Beitragsverlust": beitragsverlust_gesamt, "Gesetzliche Rente (Potenzial)": potential_gesamt,
        "Kapitalzuwachs_Sonder": kapitalzuwachs_sonder,
        "_debug_zve": zve_jahr,
        "_debug_st_b": st_b * 12 if phase == "Rente" else b_g * 12,
        "_debug_sv": sv * 12,
        "_debug_rentenwert": (RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** max(0, jahr - aktuelles_jahr)) if phase == "Rente" else 0
    }
    res.update(income_details); res.update(ausgaben_details); res.update(asset_results)
    return res


def generate_trend_data(jahre, params):
    assets_state = []
    for a in params.get("assets", []):
        assets_state.append({"name": a["name"], "kapital": a["startwert"], "config": a})
    
    # Reinvest-Config
    reinvest_target_name = params.get("reinvest_target", "— Keine (nur Cash-Reserven) —")
    liq_limit = params.get("liquidity_reserve", 10000.0)
    liq_yield = params.get("liquidity_yield", 0.0)

    # Virtuelles Asset für Cashflow-Überschüsse
    liquiditaet = {"name": "Cash-Reserven (kum.)", "kapital": 0.0, 
                   "config": {"name": "Cash-Reserven (kum.)", "rendite_pa": liq_yield, "steuertyp": "steuerfrei", "entnahme_aktiv": False}}
    assets_state.append(liquiditaet)

    data = []
    
    # Bestimme alle Übergangspunkte (als float)
    transitions_global = []
    atz_sim = params.get('atz_simulieren', False)
    atz_start = float(params.get('atz_start', 9999))
    rentenbeginn = float(params.get('rentenbeginn', 2030))
    if atz_sim:
        if atz_start % 1 != 0: transitions_global.append(atz_start)
        dauer = rentenbeginn - atz_start
        mitte = atz_start + (dauer / 2)
        if mitte % 1 != 0: transitions_global.append(mitte)
    if rentenbeginn % 1 != 0: transitions_global.append(rentenbeginn)

    for ea in params.get('einmalige_ausgaben', []):
        t_event = float(ea['jahr']) + (int(ea.get('monat', 1)) - 1) / 12.0
        if t_event % 1 != 0:
            transitions_global.append(t_event)

    for j in jahre:
        # Finde Übergänge in DIESEM Jahr
        transitions = [t for t in transitions_global if j < t < j + 1]
        transitions = sorted(list(set(transitions)))
        
        if not transitions:
            res = calculate_financials_for_year(j + 0.5, params, assets_state, segment_weight=1.0, start_t=float(j), end_t=float(j) + 1.0)
            res["Jahr_Float"] = float(j)
            res["start_t"] = float(j)
            res["end_t"] = float(j) + 1.0
            res["Label"] = str(j)
            res["weight"] = 1.0
            periods = [res]
        else:
            periods = []
            last_t = float(j)
            segments = transitions + [j + 1.0]
            for tr in segments:
                weight = tr - last_t
                if weight > 0:
                    mid_t = last_t + weight / 2.0
                    res = calculate_financials_for_year(mid_t, params, assets_state, segment_weight=weight, start_t=last_t, end_t=tr)
                    res["Jahr_Float"] = mid_t
                    res["start_t"] = last_t
                    res["end_t"] = tr
                    
                    # Berechne den genauen Monatsbereich für das Label (z.B. "2027 (01-02)")
                    start_month = int(round((last_t - j) * 12)) + 1
                    end_month = int(round((tr - j) * 12))
                    if start_month < 1: start_month = 1
                    if end_month > 12: end_month = 12
                    if start_month > 12: start_month = 12
                    if end_month < 1: end_month = 1
                    
                    if start_month == end_month:
                        res["Label"] = f"{j} ({start_month:02d})"
                    else:
                        res["Label"] = f"{j} ({start_month:02d}-{end_month:02d})"
                        
                    res["weight"] = weight
                    periods.append(res)
                last_t = tr
                
        for res in periods:
            weight = res.pop("weight")
            
            # 2. Überschuss/Defizit des Jahres behandeln
            # Korrektur: Wir reinvestieren nur den "echten" Überschuss, der NICHT aus Asset-Entnahmen stammt.
            # Sonst entsteht ein Loop, wenn ein Asset mit Entnahmeplan gleichzeitig Reinvest-Ziel ist.
            entnahmen_aus_assets = sum(v for k, v in res.items() if k.startswith("Entnahme: "))
            jahres_saldo = (res["Überschuss/Defizit"] - entnahmen_aus_assets) * 12 * weight
            
            if jahres_saldo > 0:
                # Wohin mit dem Geld?
                diff_to_limit = max(0, liq_limit - liquiditaet["kapital"])
                if diff_to_limit > 0:
                    flow_to_liq = min(jahres_saldo, diff_to_limit)
                    liquiditaet["kapital"] += flow_to_liq
                    jahres_saldo -= flow_to_liq
                
                if jahres_saldo > 0 and reinvest_target_name != "— Keine (nur Cash-Reserven) —":
                    # In Ziel-Asset investieren
                    target_asset = next((a for a in assets_state if a["name"] == reinvest_target_name), None)
                    if target_asset:
                        target_asset["kapital"] += jahres_saldo
                        jahres_saldo = 0
                
                # Falls immer noch Rest (weil kein Target gewählt oder Asset nicht gefunden)
                if jahres_saldo > 0:
                    liquiditaet["kapital"] += jahres_saldo
            else:
                # Defizit: Erst aus Liquidität decken (kann negativ gehen)
                # Hier nutzen wir den vollen Saldo (inkl. Entnahmen), da Entnahmen ja dazu da sind, Defizite zu decken.
                liquiditaet["kapital"] += res["Überschuss/Defizit"] * 12 * weight 
            
            # 3. Asset-Werte in 'res' aktualisieren, damit das Chart den Stand NACH Reinvestition zeigt
            for a_s in assets_state:
                res[f"ASSET_VAL_{a_s['name']}"] = a_s["kapital"]
                
            res["bar_width"] = weight * 0.9
            data.append(res)
            
    return pd.DataFrame(data).fillna(0)


def calculate_break_even_data(params):
    from logic.rentenrecht import berechne_regelaltersgrenze
    geburtsjahr = params.get("geburtsjahr", 1965)
    aktuelles_jahr = params.get("aktuelles_jahr", 2026)
    einnahmen = params.get("einnahmen", [])
    
    rag_jahre, rag_monate = berechne_regelaltersgrenze(geburtsjahr)
    rag = geburtsjahr + rag_jahre + (rag_monate / 12)
    
    params_a = params.copy()
    params_b = params.copy()
    params_b["rentenbeginn"] = rag
    
    einnahmen_b = []
    for e in einnahmen:
        e_copy = e.copy()
        if e.get("typ") == "Gesetzlich": e_copy["start"] = rag
        einnahmen_b.append(e_copy)
    params_b["einnahmen"] = einnahmen_b

    rentenbeginn_a = params_a["rentenbeginn"]
    rentenbeginn_b = params_b["rentenbeginn"]

    jahre = list(range(aktuelles_jahr, geburtsjahr + 101))
    kum_a, kum_b = 0.0, 0.0
    results = []
    
    for j in jahre:
        res_a = calculate_financials_for_year(j + 0.5, params_a)
        res_b = calculate_financials_for_year(j + 0.5, params_b)
        n_a = res_a.get("Netto-GRV", 0.0)
        n_b = res_b.get("Netto-GRV", 0.0)
        
        # M5: Unterjährige, monatsgenaue Ermittlung der Bezugsmonate im Kalenderjahr j
        if j + 1.0 <= rentenbeginn_a:
            monate_a = 0.0
        elif j >= rentenbeginn_a:
            monate_a = 12.0
        else:
            monate_a = (j + 1.0 - rentenbeginn_a) * 12.0
            
        if j + 1.0 <= rentenbeginn_b:
            monate_b = 0.0
        elif j >= rentenbeginn_b:
            monate_b = 12.0
        else:
            monate_b = (j + 1.0 - rentenbeginn_b) * 12.0
            
        kum_a += n_a * monate_a
        kum_b += n_b * monate_b
        
        results.append({
            "Jahr": j, 
            "Alter": j - geburtsjahr, 
            "Netto_A": n_a * monate_a / 12, 
            "Netto_B": n_b * monate_b / 12, 
            "Kumuliert_A": kum_a, 
            "Kumuliert_B": kum_b
        })
        
    df = pd.DataFrame(results)
    be_row = df[df["Kumuliert_B"] > df["Kumuliert_A"]].head(1)
    be_jahr = int(be_row["Jahr"].values[0]) if not be_row.empty else None
    be_alter = int(be_row["Alter"].values[0]) if not be_row.empty else None
    return df, be_jahr, be_alter
