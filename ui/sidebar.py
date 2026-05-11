import streamlit as st
from datetime import datetime
from data.persistence import export_settings, import_settings
from logic.rentenrecht import berechne_regelaltersgrenze, format_regelaltersgrenze, berechne_monate_frueher
from config import DATENSCHUTZ_INFO

def render_sidebar():
    """Rendert die Sidebar des Rente-O-Mat in logischer Reihenfolge."""
    
    aktuelles_jahr = datetime.now().year
    
    # --- 0. INITIALISIERUNG ---
    if "einnahmen" not in st.session_state:
        # Standard-Werte für Erststart
        regel_jahre, _ = berechne_regelaltersgrenze(1965)
        def_beginn = 1965 + regel_jahre
        st.session_state.einnahmen = [
            {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": def_beginn, "ende": 2065},
            {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": def_beginn, "ende": 2065},
        ]
    if "assets" not in st.session_state:
        st.session_state.assets = []
    if "befristete_ausgaben" not in st.session_state:
        st.session_state.befristete_ausgaben = []
    
    # --- 1. IMPORT-LOGIK (Muss vor dem Rendern der Widgets laufen) ---
    if st.session_state.get("do_import") and st.session_state.get("import_file"):
        import_settings(st.session_state.import_file)
        # Flags zurücksetzen
        st.session_state.do_import = False
        st.session_state.import_file = None
        st.rerun()

    with st.sidebar:
        # --- 2. PROFIL ---
        with st.expander("👤 Profil", expanded=True):
            nutzer_name = st.text_input("Name", value=st.session_state.get("nutzer_name_key", "Max Mustermann"), key="nutzer_name_key", help="Wird für den Dateinamen beim Export verwendet.")
            geburtsjahr = st.number_input("Geburtsjahr", value=st.session_state.get("geburtsjahr_key", 1965), min_value=1940, max_value=2010, key="geburtsjahr_key", help="Dient der Berechnung von Freibeträgen und Renten-Altersgrenzen.")
            
            kinderzahl = st.number_input("Anzahl Kinder", value=st.session_state.get("kinderzahl_key", 0), min_value=0, max_value=10, key="kinderzahl_key", help="Beeinflusst den Beitrag zur Pflegeversicherung")
            
            kist_options = {"Keine": 0.0, "8% (Bayern, BW)": 0.08, "9% (Restl. Bundesländer)": 0.09}
            kist_display = st.selectbox("Kirchensteuer", list(kist_options.keys()), index=0, key="kist_display_key")
            kirchensteuer_satz = kist_options[kist_display]
            st.session_state["kist_key"] = kirchensteuer_satz # Speichern für Export
            
            st.divider()
            
            # EXPORT
            export_params = {
                "nutzer_name": nutzer_name,
                "geburtsjahr": geburtsjahr,
                "kinderzahl": kinderzahl,
                "kirchensteuer_satz": kirchensteuer_satz,
                "rentenbeginn": st.session_state.get("rentenbeginn_input", geburtsjahr + 67),
                "atz_simulieren": st.session_state.get("atz_sim_input", False),
                "atz_dauer": st.session_state.get("atz_dauer_input", 6),
                "atz_aufstockung_pct": st.session_state.get("atz_aufst_key", 20),
                "aktuelles_brutto": st.session_state.get("brutto_key", 6000.0),
                "aktuelles_netto": st.session_state.get("netto_key", 4500.0),
                "show_values": st.session_state.get("show_vals_key", True),
                "einnahmen": st.session_state.get("einnahmen", []),
                "ausgaben_input": {k: st.session_state.get(f"c_{k}", 200.0) for k in ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]},
                "anpassungsfaktor_input": {k: st.session_state.get(f"a_{k}", 100) for k in ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]},
                "inflation_rate": st.session_state.get("infl_rate_key", 2.0),
                "rentenanpassung_rate": st.session_state.get("renten_anp_key", 2.0),
                "bav_anpassung_rate": st.session_state.get("bav_anp_key", 1.0),
                "startvermoegen": st.session_state.get("startvermoegen_key", 0.0),
                "kapitalrendite": st.session_state.get("rendite_key", 3.0),
                "befristete_ausgaben": st.session_state.get("befristete_ausgaben", []),
                "assets": st.session_state.get("assets", [])
            }
            json_str = export_settings(export_params)
            
            st.markdown("💾 **Export / Import**", help=DATENSCHUTZ_INFO)
            st.download_button(
                label="Einstellungen exportieren", 
                data=json_str, 
                file_name=f"R-O-M_{nutzer_name.replace(' ', '_')}.json", 
                mime="application/json", 
                width='stretch'
            )
            
            uploaded_file = st.file_uploader("Import", type=["json"], key="json_uploader_widget", help=DATENSCHUTZ_INFO)
            if uploaded_file and st.button("Importieren", width='stretch'):
                st.session_state.import_file = uploaded_file
                st.session_state.do_import = True
                st.rerun()

        # --- 3. MEILENSTEINE ---
        rag_jahre, rag_monate = berechne_regelaltersgrenze(geburtsjahr)
        default_jahr = geburtsjahr + rag_jahre
        default_monat = rag_monate + 1 # +1 weil Monate 1-12
        if default_monat > 12:
            default_jahr += 1
            default_monat -= 12
            
        with st.expander("📅 Meilensteine", expanded=True):
            col_j, col_m = st.columns([0.6, 0.4])
            r_jahr = col_j.number_input("Rentenbeginn (Jahr)", value=st.session_state.get("rentenbeginn_jahr_input", default_jahr), min_value=aktuelles_jahr, key="rentenbeginn_jahr_input")
            r_monat = col_m.selectbox("Monat", range(1, 13), index=st.session_state.get("rentenbeginn_monat_input", default_monat) - 1, key="rentenbeginn_monat_input")
            
            # Rentenbeginn als Dezimaljahr für die Engine
            rentenbeginn = r_jahr + (r_monat - 1) / 12
            
            if "prev_rentenbeginn" not in st.session_state:
                st.session_state.prev_rentenbeginn = rentenbeginn
                
            if rentenbeginn != st.session_state.prev_rentenbeginn:
                for e in st.session_state.einnahmen:
                    if e["start"] == st.session_state.prev_rentenbeginn:
                        e["start"] = rentenbeginn
                st.session_state.prev_rentenbeginn = rentenbeginn

            atz_simulieren = st.checkbox("ATZ einplanen", value=st.session_state.get("atz_sim_input", False), key="atz_sim_input", help="Simuliert eine Altersteilzeit (Blockmodell) direkt vor dem Rentenbeginn.")
            if atz_simulieren:
                max_atz = int(max(1, rentenbeginn - aktuelles_jahr))
                if max_atz > 1:
                    atz_dauer = st.slider("ATZ Dauer (Jahre)", 1, max_atz, int(min(6, max_atz)), key="atz_dauer_input")
                else:
                    atz_dauer = 1
                    st.write(f"ATZ Dauer: **{atz_dauer} Jahr** (begrenzt durch Rentenbeginn)")
                
                atz_start = rentenbeginn - atz_dauer
                st.info(f"ATZ-Beginn: {atz_start}")
                atz_ende = rentenbeginn
            else:
                atz_dauer = 0
                atz_start, atz_ende = 9999, 9999

            # --- INFOBOX FÜR ABSCHLAG UND STEUER ---
            st.divider()
            from logic.rentenrecht import format_regelaltersgrenze, berechne_monate_frueher
            monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn)
            abschlag_pct = min(14.4, monate_frueher * 0.3)
            
            from logic.taxes import berechne_rentensteuer_anteil
            steuer_anteil = berechne_rentensteuer_anteil(rentenbeginn)
            
            rag_str = format_regelaltersgrenze(geburtsjahr)
            st.success(f"**Deine Regelaltersgrenze:** {rag_str}")
            
            # --- NEU: Präzise EP-Analyse für die Infobox ---
            from logic.rentenrecht import berechne_ep_pro_jahr, berechne_beitragsverlust_logic
            from config import RENTENWERT_AKTUELL
            
            rentenanpassung_rate = st.session_state.get("renten_anp_key", 2.0)
            brutto_fuer_ep = st.session_state.get("brutto_key", 6000.0)
            ep_pro_jahr = berechne_ep_pro_jahr(brutto_fuer_ep, aktuelles_jahr)
            
            jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
            ep_zuwachs = jahre_bis_beginn * ep_pro_jahr
            
            # K2: Rentenwert projizieren für Infobox
            rw_proj = RENTENWERT_AKTUELL * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
            
            monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn)
            bv_res = berechne_beitragsverlust_logic(monate_frueher, ep_pro_jahr, rw_proj)
            
            # --- NEU: Break-Even Berechnung für Infobox ---
            from logic.engine import calculate_break_even_data
            
            # Params-Pack für Break-Even (muss aktuellste Werte enthalten)
            be_params = {
                "geburtsjahr": geburtsjahr,
                "aktuelles_jahr": aktuelles_jahr,
                "rentenbeginn": rentenbeginn,
                "aktuelles_brutto": st.session_state.get("brutto_key", 6000.0),
                "kinderzahl": kinderzahl,
                "kirchensteuer_satz": kirchensteuer_satz,
                "einnahmen": st.session_state.einnahmen,
                "rentenanpassung_rate": st.session_state.get("renten_anp_key", 2.0),
                "inflation_rate": st.session_state.get("infl_rate_key", 2.0)
            }
            
            try:
                _, be_jahr, be_alter = calculate_break_even_data(be_params)
                be_info = f"{be_alter} J. ({be_jahr})" if be_jahr else "Nicht erreicht"
            except:
                be_info = "Berechnung läuft..."

            info_text = f"""
            **Regelaltersgrenze:** {rag_str}
            
            **Analyse vorzeitiger Eintritt:**
            * **Rentenabschlag (GRV):** {abschlag_pct:.1f} %
            * **Beitragsverlust:** -{bv_res['ep']:.2f} EP / -{bv_res['euro']:.2f} € mtl.
            * **EP-Zuwachs bis Start:** +{ep_zuwachs:.2f} EP
            * **Break-Even (vs. RAG):** {be_info}
            
            **Steuerpflichtiger Anteil:** {steuer_anteil:.1f} %
            """
            st.info(info_text)
            
            with st.popover("❓ Erläuterung der Werte"):
                st.markdown(f"""
                **Rentenabschlag ({abschlag_pct:.1f} %):**
                Dies ist der *versicherungsmathematische Abschlag*. Da du früher in Rente gehst und diese somit voraussichtlich länger beziehst, wird die Rente lebenslang um 0,3 % pro Monat gekürzt.
                
                **Beitragsverlust (-{bv_res['ep']:.2f} EP):**
                Dies sind die Rentenpunkte, die du *nicht* mehr sammelst, weil du vor der Regelaltersgrenze aufhörst zu arbeiten. In dieser Zeit zahlst du keine Beiträge mehr ein.
                
                **EP-Zuwachs bis Start (+{ep_zuwachs:.2f} EP):**
                Das ist die Prognose der Punkte, die du ab heute bis zu deinem Rentenbeginn in {jahre_bis_beginn} Jahren voraussichtlich noch durch deine Arbeit verdienen wirst.
                
                **Steuerpflichtiger Anteil ({steuer_anteil:.1f} %):**
                Der Teil deiner gesetzlichen Rente, der mit deinem persönlichen Steuersatz versteuert werden muss. Dieser Anteil wird durch das Jahr deines Renteneintritts festgeschrieben.
                
                **Netto-Berechnung (zvE):**
                Deine Steuern werden nicht auf das volle Brutto, sondern auf das **zu versteuernde Einkommen (zvE)** berechnet. Wir ziehen automatisch Vorsorgeaufwendungen (RV, KV, PV) und Pauschbeträge (Werbungskosten 1.230€) ab, um ein realistisches Netto zu ermitteln.
                
                **Break-Even ({be_info}):**
                Das Alter, ab dem die Summe der erhaltenen Regelrente (Szenario B) die Summe der früher bezogenen Frührente (Szenario A) übersteigt. Erst ab diesem Alter "lohnt" sich der spätere Rentenbeginn rein finanziell bezogen auf die gesetzliche Rente.
                """)

        # --- 4. FINANZEN AKTUELL ---
        with st.expander("💶 Finanzen Aktuell", expanded=False):
            aktuelles_brutto = st.number_input("Brutto/mtl.", value=st.session_state.get("brutto_key", 6000.0), key="brutto_key", help="Dein aktuelles monatliches Bruttogehalt (als Basis für die Aktivphase).")
            atz_aufst = st.slider("ATZ-Aufst. % (vom halben Brutto)", 20, 50, st.session_state.get("atz_aufst_key", 20), key="atz_aufst_key", help="Gesetzliches Minimum sind 20%. Viele Tarifverträge garantieren z.B. 82% des vorherigen Nettos. Verschiebe den Regler, um die Netto-Quote unten abzulesen.")
            
            # --- Echtzeit-Berechnung der ATZ-Nettoquote ---
            from logic.engine import calculate_financials_for_year
            
            # Minimaler params-dict für die Engine
            tmp_params = {
                "aktuelles_brutto": aktuelles_brutto,
                "atz_aufstockung_pct": atz_aufst,
                "kinderzahl": kinderzahl,
                "kirchensteuer_satz": kirchensteuer_satz,
                "atz_simulieren": True, 
                "atz_start": aktuelles_jahr, 
                "rentenbeginn": aktuelles_jahr + 10,
                "ausgaben_kategorien": [], "ausgaben_input": {}, "einnahmen": []
            }
            
            # 1. Aktiv-Netto berechnen (Jahr < ATZ_start -> Aktiv)
            res_aktiv = calculate_financials_for_year(aktuelles_jahr - 1, tmp_params)
            
            # 2. ATZ-Netto berechnen (Jahr = ATZ_start -> ATZ(A))
            res_atz = calculate_financials_for_year(aktuelles_jahr, tmp_params)
            
            if res_aktiv["Netto-Einkommen"] > 0:
                quote = (res_atz["Netto-Einkommen"] / res_aktiv["Netto-Einkommen"]) * 100
                st.info(f"**ATZ-Netto:** {res_atz['Netto-Einkommen']:.0f} €/mtl.\n\n*(Entspricht **{quote:.1f} %** deines bisherigen Netto-Gehalts von {res_aktiv['Netto-Einkommen']:.0f} €)*")
            
            aktuelles_netto = st.number_input("Netto/mtl. (Optional)", value=st.session_state.get("netto_key", 4500.0), key="netto_key", help="Dein echtes ausgezahltes Netto. Wird nur für das Status-Quo-Sankey ganz oben verwendet, um Abweichungen zu erkennen.")
            show_values = st.checkbox("Werte im Sankey zeigen", value=st.session_state.get("show_vals_key", True), key="show_vals_key")

        # --- 5. EINNAHMEQUELLEN ---
        with st.expander("💰 Einnahmequellen (Rente)", expanded=False):
            if "edit_idx" not in st.session_state: st.session_state.edit_idx = None
            if "show_add_form" not in st.session_state: st.session_state.show_add_form = False
            
            if not st.session_state.show_add_form and st.session_state.edit_idx is None:
                if st.button("➕ Neu"):
                    st.session_state.show_add_form = True
                    st.rerun()
                    
            if st.session_state.show_add_form or st.session_state.edit_idx is not None:
                is_edit = st.session_state.edit_idx is not None
                current_e = st.session_state.einnahmen[st.session_state.edit_idx] if is_edit else {"name": "Neue Quelle", "betrag": 500.0, "typ": "Privat", "start": rentenbeginn, "ende": 2065}
                st.markdown("##### " + ("Editieren" if is_edit else "Hinzufügen"))
                f_name = st.text_input("Name", value=current_e["name"])
                f_typ_options = ["Gesetzlich", "bAV", "Privat", "Kapital", "bAV (Einmalzahlung)", "Entnahmeplan (Vermögen)", "Sonstiges"]
                f_typ_index = f_typ_options.index(current_e["typ"]) if current_e.get("typ") in f_typ_options else 0
                f_typ = st.selectbox("Typ", f_typ_options, index=f_typ_index)
                
                if f_typ == "bAV (Einmalzahlung)":
                    f_betrag = st.number_input("Einmalbetrag (€ Brutto)", value=float(current_e["betrag"]), min_value=0.0)
                    f_start = st.number_input("Auszahlungsjahr", value=int(current_e["start"]), min_value=aktuelles_jahr)
                    f_ende = f_start
                elif f_typ == "Entnahmeplan (Vermögen)":
                    f_betrag = st.number_input("Entnahme (€/mtl. Netto)", value=float(current_e["betrag"]), min_value=0.0)
                    f_start = st.number_input("Von Jahr", value=int(current_e["start"]), min_value=aktuelles_jahr)
                    f_ende = st.number_input("Bis Jahr", value=int(current_e["ende"]), min_value=f_start)
                elif f_typ == "Gesetzlich":
                    eingabe_modus_options = ["Euro-Betrag", "Entgeltpunkte (EP)"]
                    current_modus = current_e.get("eingabe_modus", "euro")
                    eingabe_modus_idx = 0 if current_modus == "euro" else 1
                    
                    f_eingabe_modus_radio = st.radio("Eingabemodus", eingabe_modus_options, index=eingabe_modus_idx, horizontal=True)
                    
                    if f_eingabe_modus_radio == "Entgeltpunkte (EP)":
                        f_eingabe_modus = "punkte"
                        f_punkte = st.number_input("Anzahl Entgeltpunkte (lt. Renteninformation)", value=float(current_e.get("punkte", 40.0)), min_value=0.0, step=0.1)
                        from config import RENTENWERT_AKTUELL
                        f_betrag = f_punkte * RENTENWERT_AKTUELL
                        st.info(f"Basiswert: **{f_betrag:.2f} €/mtl.** (bei aktuellem Rentenwert, vor Abschlägen)")
                    else:
                        f_eingabe_modus = "euro"
                        f_punkte = 0.0
                        f_betrag = st.number_input("Betrag (€/mtl., heutige Anwartschaft lt. Renteninfo)", value=float(current_e["betrag"]), min_value=0.0, help="Nimm hier den Wert 'Bisher erreichte Rentenanwartschaft'. Der Rente-O-Mat berechnet die Hochrechnung mit der gewählten Rate (0, 1, 2%) dann automatisch.")
                        
                    f_start = st.number_input("Von Jahr", value=int(current_e["start"]), min_value=aktuelles_jahr)
                    f_ende = st.number_input("Bis Jahr", value=int(current_e["ende"]), min_value=f_start)
                else:
                    f_betrag = st.number_input("Betrag (€/mtl.)", value=float(current_e["betrag"]), min_value=0.0)
                    f_start = st.number_input("Von Jahr", value=int(current_e["start"]), min_value=aktuelles_jahr)
                    f_ende = st.number_input("Bis Jahr", value=int(current_e["ende"]), min_value=f_start)
                c1, c2 = st.columns(2)
                if c1.button("💾 Speichern"):
                    new_data = {"name": f_name, "betrag": f_betrag, "typ": f_typ, "start": f_start, "ende": f_ende}
                    if f_typ == "Gesetzlich":
                        new_data["eingabe_modus"] = f_eingabe_modus
                        new_data["punkte"] = f_punkte
                    if is_edit: st.session_state.einnahmen[st.session_state.edit_idx] = new_data
                    else: st.session_state.einnahmen.append(new_data)
                    st.session_state.edit_idx, st.session_state.show_add_form = None, False
                    st.rerun()
                if c2.button("❌ Abbrechen"):
                    st.session_state.edit_idx, st.session_state.show_add_form = None, False
                    st.rerun()
                    
            for i, e in enumerate(st.session_state.einnahmen):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                col1.write(f"**{e['name']}**\n{e['betrag']}€")
                if col2.button("✏️", key=f"e_{i}"):
                    st.session_state.edit_idx, st.session_state.show_add_form = i, False
                    st.rerun()
                if col3.button("🗑️", key=f"d_{i}"):
                    st.session_state.einnahmen.pop(i)
                    st.rerun()

        # --- 5b. VERMÖGENSWERTE ---
        if "assets" not in st.session_state:
            st.session_state.assets = []
        if "asset_edit_idx" not in st.session_state:
            st.session_state.asset_edit_idx = None
        if "asset_show_add" not in st.session_state:
            st.session_state.asset_show_add = False

        with st.expander("💎 Vermögenswerte", expanded=False):
            st.caption("Individuelle Assets (Depot, Tagesgeld) mit optionalem Entnahmeplan")
            
            if not st.session_state.asset_show_add and st.session_state.asset_edit_idx is None:
                if st.button("➕ Neues Asset"):
                    st.session_state.asset_show_add = True
                    st.rerun()
            
            if st.session_state.asset_show_add or st.session_state.asset_edit_idx is not None:
                is_edit = st.session_state.asset_edit_idx is not None
                curr = st.session_state.assets[st.session_state.asset_edit_idx] if is_edit else {
                    "name": "Welt-ETF", "startwert": 10000.0, "rendite_pa": 5.0,
                    "steuertyp": "abgeltung", "teilfreistellung_pct": 30.0,
                    "entnahme_aktiv": False, "entnahme_betrag_mtl": 500.0,
                    "entnahme_start": aktuelles_jahr, "entnahme_ende": aktuelles_jahr + 20
                }
                st.markdown("##### " + ("Editieren" if is_edit else "Hinzufügen"))
                a_name = st.text_input("Name", value=curr["name"], key="a_name")
                a_start = st.number_input("Startwert (€)", value=float(curr["startwert"]), min_value=0.0, key="a_start")
                a_rendite = st.slider("Rendite (% p.a.)", 0.0, 10.0, float(curr["rendite_pa"]), 0.1, key="a_rendite")
                
                a_steuertyp_options = {"Abgeltungsteuer": "abgeltung", "Teilfreistellung (ETF)": "teilfreistellung", "Steuerfrei": "steuerfrei"}
                a_steuertyp_display = st.selectbox("Besteuerung", list(a_steuertyp_options.keys()), 
                                                   index=list(a_steuertyp_options.values()).index(curr["steuertyp"]), key="a_steuer")
                a_steuertyp = a_steuertyp_options[a_steuertyp_display]
                
                a_tfs = 0.0
                if a_steuertyp == "teilfreistellung":
                    a_tfs = st.number_input("Teilfreistellung (%)", value=float(curr.get("teilfreistellung_pct", 30.0)), min_value=0.0, max_value=100.0, key="a_tfs")

                st.divider()
                a_ent_aktiv = st.checkbox("Entnahmeplan aktivieren", value=curr.get("entnahme_aktiv", False), key="a_ent_aktiv")
                if a_ent_aktiv:
                    a_ent_mode = st.selectbox("Entnahme-Modus", ["Fester Betrag", "Kapitalverzehr (bis Ende)"], 
                                             index=0 if curr.get("entnahme_modus") == "fix" else 1, key="a_ent_mode")
                    a_ent_modus_val = "fix" if a_ent_mode == "Fester Betrag" else "verzehr"
                    
                    if a_ent_modus_val == "fix":
                        a_ent_betrag = st.number_input("Entnahme (€/mtl. Netto)", value=float(curr.get("entnahme_betrag_mtl", 500.0)), min_value=0.0, key="a_ent_betrag")
                    else:
                        st.info("💡 Der Betrag wird automatisch berechnet, damit das Kapital am Ende auf 0€ sinkt.")
                        a_ent_betrag = 0.0
                    
                    a_ent_c1, a_ent_c2 = st.columns(2)
                    a_ent_start = a_ent_c1.number_input("Von Jahr", value=max(2000, int(curr.get("entnahme_start", aktuelles_jahr))), min_value=2000, key="a_ent_start")
                    a_ent_ende = a_ent_c2.number_input("Bis Jahr (Ende)", value=max(a_ent_start, int(curr.get("entnahme_ende", a_ent_start + 10))), min_value=a_ent_start, key="a_ent_ende")
                else:
                    a_ent_betrag, a_ent_start, a_ent_ende, a_ent_modus_val = 0.0, aktuelles_jahr, aktuelles_jahr + 10, "fix"
                
                ac1, ac2 = st.columns(2)
                if ac1.button("💾 Speichern", key="a_save"):
                    new_asset = {
                        "name": a_name, "startwert": a_start, "rendite_pa": a_rendite,
                        "steuertyp": a_steuertyp, "teilfreistellung_pct": a_tfs,
                        "entnahme_aktiv": a_ent_aktiv, "entnahme_betrag_mtl": a_ent_betrag,
                        "entnahme_start": a_ent_start, "entnahme_ende": a_ent_ende,
                        "entnahme_modus": a_ent_modus_val
                    }
                    if is_edit:
                        st.session_state.assets[st.session_state.asset_edit_idx] = new_asset
                    else:
                        st.session_state.assets.append(new_asset)
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = None, False
                    st.rerun()
                if ac2.button("❌ Abbrechen", key="a_cancel"):
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = None, False
                    st.rerun()
            
            for i, asset in enumerate(st.session_state.assets):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                if asset.get('entnahme_aktiv'):
                    if asset.get('entnahme_modus') == 'verzehr':
                        ent_str = " | Entnahme: Berechnet"
                    else:
                        ent_str = f" | Entnahme: {asset['entnahme_betrag_mtl']:.0f}€"
                else:
                    ent_str = ""
                col1.write(f"**{asset['name']}**\n{asset['startwert']:,.0f}€{ent_str}")
                if col2.button("✏️", key=f"a_e_{i}"):
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = i, False
                    st.rerun()
                if col3.button("🗑️", key=f"a_d_{i}"):
                    st.session_state.assets.pop(i)
                    st.rerun()

        # --- 6. HAUSHALTSBUCH ---
        with st.expander("🏠 Haushaltsbuch (Ausgaben)", expanded=False):
            ausgaben_kategorien = ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]
            ausgaben_input, anpassungsfaktor_input = {}, {}
            st.caption("Ausgabe in Aktivphase | Rentenanpassung in %")
            for kat in ausgaben_kategorien:
                c1, c2 = st.columns([0.6, 0.4])
                ausgaben_input[kat] = c1.number_input(f"{kat}", value=st.session_state.get(f"c_{kat}", 1200.0 if kat=="Wohnen" else 200.0), min_value=0.0, key=f"c_{kat}")
                anpassungsfaktor_input[kat] = c2.slider(f"RV%", 0, 200, st.session_state.get(f"a_{kat}", 100), key=f"a_{kat}", label_visibility="collapsed")

        # --- 6b. BEFRISTETE AUSGABEN ---
        if "befristete_ausgaben" not in st.session_state:
            st.session_state.befristete_ausgaben = []
        if "ba_edit_idx" not in st.session_state:
            st.session_state.ba_edit_idx = None
        if "ba_show_add" not in st.session_state:
            st.session_state.ba_show_add = False

        with st.expander("⏱️ Befristete Ausgaben", expanded=False):
            st.caption("Zeitlich begrenzte Kosten (Kredit, Unterhalt, etc.)")
            
            if not st.session_state.ba_show_add and st.session_state.ba_edit_idx is None:
                if st.button("➕ Neue befristete Ausgabe"):
                    st.session_state.ba_show_add = True
                    st.rerun()
            
            if st.session_state.ba_show_add or st.session_state.ba_edit_idx is not None:
                is_edit = st.session_state.ba_edit_idx is not None
                curr = st.session_state.befristete_ausgaben[st.session_state.ba_edit_idx] if is_edit else {
                    "name": "Neue Ausgabe", "betrag_mtl": 500.0, "start": aktuelles_jahr, "ende": aktuelles_jahr + 10,
                    "kategorie": "", "inflationsgebunden": False
                }
                st.markdown("##### " + ("Editieren" if is_edit else "Hinzufügen"))
                ba_name = st.text_input("Name", value=curr["name"], key="ba_name")
                ba_betrag = st.number_input("Betrag (€/mtl.)", value=float(curr["betrag_mtl"]), min_value=0.0, key="ba_betrag")
                ba_c1, ba_c2 = st.columns(2)
                ba_start = ba_c1.number_input("Von Jahr", value=int(curr["start"]), min_value=2000, key="ba_start")
                ba_ende = ba_c2.number_input("Bis Jahr", value=int(curr["ende"]), min_value=ba_start, key="ba_ende")
                
                # Kategorie: bestehende wählen ODER neue eingeben
                kat_optionen = ausgaben_kategorien + ["— Neue Kategorie —"]
                curr_kat = curr.get("kategorie", "")
                if curr_kat in ausgaben_kategorien:
                    kat_idx = ausgaben_kategorien.index(curr_kat)
                else:
                    kat_idx = len(kat_optionen) - 1  # "Neue Kategorie"
                
                ba_kat_sel = st.selectbox("Kategorie", kat_optionen, index=kat_idx, key="ba_kat_sel")
                if ba_kat_sel == "— Neue Kategorie —":
                    ba_kat = st.text_input("Neue Kategorie", value=curr_kat if curr_kat not in ausgaben_kategorien else "", key="ba_kat_new")
                else:
                    ba_kat = ba_kat_sel
                
                ba_infl = st.checkbox("Steigt mit Inflation", value=curr.get("inflationsgebunden", False), key="ba_infl")
                
                bc1, bc2 = st.columns(2)
                if bc1.button("💾 Speichern", key="ba_save"):
                    new_ba = {"name": ba_name, "betrag_mtl": ba_betrag, "start": ba_start, "ende": ba_ende,
                              "kategorie": ba_kat if ba_kat else ba_name, "inflationsgebunden": ba_infl}
                    if is_edit:
                        st.session_state.befristete_ausgaben[st.session_state.ba_edit_idx] = new_ba
                    else:
                        st.session_state.befristete_ausgaben.append(new_ba)
                    st.session_state.ba_edit_idx, st.session_state.ba_show_add = None, False
                    st.rerun()
                if bc2.button("❌ Abbrechen", key="ba_cancel"):
                    st.session_state.ba_edit_idx, st.session_state.ba_show_add = None, False
                    st.rerun()
            
            for i, ba in enumerate(st.session_state.befristete_ausgaben):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                col1.write(f"**{ba['name']}**\n{ba['betrag_mtl']:.0f}€ bis {ba['ende']}")
                if col2.button("✏️", key=f"ba_e_{i}"):
                    st.session_state.ba_edit_idx, st.session_state.ba_show_add = i, False
                    st.rerun()
                if col3.button("🗑️", key=f"ba_d_{i}"):
                    st.session_state.befristete_ausgaben.pop(i)
                    st.rerun()

        # Dynamische Kategorien: aus befristeten Ausgaben neue Kategorien sammeln
        alle_kategorien = list(ausgaben_kategorien)
        for ba in st.session_state.befristete_ausgaben:
            kat = ba.get('kategorie', ba['name'])
            if kat not in alle_kategorien:
                alle_kategorien.append(kat)

        # --- 7. ANNAHMEN (Inflation & Co.) ---
        with st.expander("⚙️ Annahmen (Dynamik)", expanded=False):
            st.markdown("**Inflationsraten (% p.a.)**")
            infl_rate = st.slider("Ausgaben (Allg. Inflation)", 0.0, 5.0, st.session_state.get("infl_rate_key", 2.0), 0.1, key="infl_rate_key", help="Jährliche Steigerung aller Ausgaben")
            
            anp_options = {"0% (Pessimistisch)": 0.0, "1% (Moderat)": 1.0, "2% (Standard)": 2.0}
            default_idx = 2 # 2% ist Standard
            
            stored_val = st.session_state.get("renten_anp_key", 2.0)
            if stored_val == 0.0: default_idx = 0
            elif stored_val == 1.0: default_idx = 1
            
            anp_label = st.selectbox("Gesetzliche Rente (Anpassung)", list(anp_options.keys()), index=default_idx, key="renten_anp_display", help="Jährliche Anpassung der GRV. Wird auch zur Projektion des Rentenwerts bis zum Start verwendet (DRV-Standard).")
            renten_anp = anp_options[anp_label]
            st.session_state["renten_anp_key"] = renten_anp
            
            bav_anp = st.slider("Betriebsrente (bAV)", 0.0, 3.0, st.session_state.get("bav_anp_key", 1.0), 0.1, key="bav_anp_key", help="Jährliche garantierte Anpassung der bAV")
            
            st.divider()
            st.markdown("**Vermögensaufbau**")
            startvermoegen = st.number_input("Startvermögen (€)", value=st.session_state.get("startvermoegen_key", 0.0), key="startvermoegen_key")
            rendite = st.slider("Kapitalrendite p.a. (%)", 0.0, 10.0, st.session_state.get("rendite_key", 3.0), 0.1, key="rendite_key")

        return {
            "nutzer_name": nutzer_name, "geburtsjahr": geburtsjahr, "rentenbeginn": rentenbeginn,
            "atz_simulieren": atz_simulieren, "atz_dauer": atz_dauer if atz_simulieren else 0,
            "atz_start": atz_start, "atz_ende": rentenbeginn, "atz_aufstockung_pct": atz_aufst,
            "aktuelles_brutto": aktuelles_brutto, "aktuelles_netto": aktuelles_netto,
            "ausgaben_input": ausgaben_input, "anpassungsfaktor_input": anpassungsfaktor_input,
            "einnahmen": st.session_state.einnahmen, "show_values": show_values,
            "ausgaben_kategorien": alle_kategorien, "aktuelles_jahr": aktuelles_jahr,
            "kinderzahl": kinderzahl, "kirchensteuer_satz": kirchensteuer_satz,
            "inflation_rate": infl_rate, "rentenanpassung_rate": renten_anp,
            "bav_anpassung_rate": bav_anp, "startvermoegen": startvermoegen,
            "kapitalrendite": rendite,
            "befristete_ausgaben": st.session_state.befristete_ausgaben,
            "assets": st.session_state.assets
        }
