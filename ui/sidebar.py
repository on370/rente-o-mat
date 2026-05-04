import streamlit as st
from datetime import datetime
from data.persistence import export_settings, import_settings

def render_sidebar():
    """Rendert die Sidebar des Rente-O-Mat in logischer Reihenfolge."""
    
    aktuelles_jahr = datetime.now().year
    
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
            nutzer_name = st.text_input("Name", value=st.session_state.get("nutzer_name_key", "Max Mustermann"), key="nutzer_name_key")
            geburtsjahr = st.number_input("Geburtsjahr", value=st.session_state.get("geburtsjahr_key", 1965), min_value=1940, max_value=2010, key="geburtsjahr_key")
            
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
                "kapitalrendite": st.session_state.get("rendite_key", 3.0)
            }
            json_str = export_settings(export_params)
            
            st.download_button(
                label="Exportieren", 
                data=json_str, 
                file_name=f"R-O-M_{nutzer_name.replace(' ', '_')}.json", 
                mime="application/json", 
                use_container_width=True
            )
            
            uploaded_file = st.file_uploader("Import", type=["json"], key="json_uploader_widget")
            if uploaded_file and st.button("Importieren", use_container_width=True):
                st.session_state.import_file = uploaded_file
                st.session_state.do_import = True
                st.rerun()

        # --- 3. MEILENSTEINE ---
        default_rentenbeginn = geburtsjahr + 67
        with st.expander("📅 Meilensteine", expanded=True):
            rentenbeginn = st.number_input("Rentenbeginn (Jahr)", value=st.session_state.get("rentenbeginn_input", default_rentenbeginn), min_value=aktuelles_jahr, key="rentenbeginn_input")
            
            if "prev_rentenbeginn" not in st.session_state:
                st.session_state.prev_rentenbeginn = rentenbeginn
                
            if rentenbeginn != st.session_state.prev_rentenbeginn:
                for e in st.session_state.einnahmen:
                    if e["start"] == st.session_state.prev_rentenbeginn:
                        e["start"] = rentenbeginn
                st.session_state.prev_rentenbeginn = rentenbeginn

            atz_simulieren = st.checkbox("ATZ einplanen", value=st.session_state.get("atz_sim_input", False), key="atz_sim_input")
            if atz_simulieren:
                max_atz = max(1, rentenbeginn - aktuelles_jahr)
                atz_dauer = st.slider("ATZ Dauer (Jahre)", 1, max_atz, min(6, max_atz), key="atz_dauer_input")
                atz_start = rentenbeginn - atz_dauer
                st.info(f"ATZ-Beginn: {atz_start}")
                atz_ende = rentenbeginn
            else:
                atz_dauer = 0
                atz_start, atz_ende = 9999, 9999

        # --- 4. FINANZEN AKTUELL ---
        with st.expander("💶 Finanzen Aktuell", expanded=False):
            aktuelles_brutto = st.number_input("Brutto/mtl.", value=st.session_state.get("brutto_key", 6000.0), key="brutto_key")
            atz_aufst = st.slider("ATZ-Aufst. %", 20, 50, st.session_state.get("atz_aufst_key", 20), key="atz_aufst_key")
            aktuelles_netto = st.number_input("Netto/mtl.", value=st.session_state.get("netto_key", 4500.0), key="netto_key")
            show_values = st.checkbox("Werte im Sankey zeigen", value=st.session_state.get("show_vals_key", True), key="show_vals_key")

        # --- 5. EINNAHMEQUELLEN ---
        if "einnahmen" not in st.session_state:
            st.session_state.einnahmen = [
                {"name": "Gesetzliche Rente", "betrag": 2200.0, "typ": "Gesetzlich", "start": default_rentenbeginn, "ende": 2065},
                {"name": "Betriebsrente", "betrag": 600.0, "typ": "bAV", "start": default_rentenbeginn, "ende": 2065},
            ]

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
                f_typ = st.selectbox("Typ", ["Gesetzlich", "bAV", "Privat", "Kapital", "Sonstiges"], index=["Gesetzlich", "bAV", "Privat", "Kapital", "Sonstiges"].index(current_e["typ"]))
                f_betrag = st.number_input("Betrag (€/mtl.)", value=float(current_e["betrag"]), min_value=0.0)
                f_start = st.number_input("Von Jahr", value=int(current_e["start"]), min_value=aktuelles_jahr)
                f_ende = st.number_input("Bis Jahr", value=int(current_e["ende"]), min_value=f_start)
                c1, c2 = st.columns(2)
                if c1.button("💾 OK"):
                    new_data = {"name": f_name, "betrag": f_betrag, "typ": f_typ, "start": f_start, "ende": f_ende}
                    if is_edit: st.session_state.einnahmen[st.session_state.edit_idx] = new_data
                    else: st.session_state.einnahmen.append(new_data)
                    st.session_state.edit_idx, st.session_state.show_add_form = None, False
                    st.rerun()
                if c2.button("❌ Stop"):
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

        # --- 6. HAUSHALTSBUCH ---
        with st.expander("🏠 Haushaltsbuch (Ausgaben)", expanded=False):
            ausgaben_kategorien = ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]
            ausgaben_input, anpassungsfaktor_input = {}, {}
            st.caption("Ausgabe in Aktivphase | Rentenanpassung in %")
            for kat in ausgaben_kategorien:
                c1, c2 = st.columns([0.6, 0.4])
                ausgaben_input[kat] = c1.number_input(f"{kat}", value=st.session_state.get(f"c_{kat}", 1200.0 if kat=="Wohnen" else 200.0), min_value=0.0, key=f"c_{kat}")
                anpassungsfaktor_input[kat] = c2.slider(f"RV%", 0, 200, st.session_state.get(f"a_{kat}", 100), key=f"a_{kat}", label_visibility="collapsed")

        # --- 7. ANNAHMEN (Inflation & Co.) ---
        with st.expander("⚙️ Annahmen (Dynamik)", expanded=False):
            st.markdown("**Inflationsraten (% p.a.)**")
            infl_rate = st.slider("Ausgaben (Allg. Inflation)", 0.0, 5.0, st.session_state.get("infl_rate_key", 2.0), 0.1, key="infl_rate_key", help="Jährliche Steigerung aller Ausgaben")
            renten_anp = st.slider("Gesetzliche Rente", 0.0, 5.0, st.session_state.get("renten_anp_key", 2.0), 0.1, key="renten_anp_key", help="Jährliche Anpassung der GRV")
            bav_anp = st.slider("Betriebsrente (bAV)", 0.0, 3.0, st.session_state.get("bav_anp_key", 1.0), 0.1, key="bav_anp_key", help="Jährliche garantierte Anpassung der bAV")
            
            st.divider()
            st.markdown("**Vermögensaufbau**")
            startvermoegen = st.number_input("Startvermögen (€)", value=st.session_state.get("startvermoegen_key", 0.0), key="startvermoegen_key")
            rendite = st.slider("Kapitalrendite p.a. (%)", 0.0, 10.0, st.session_state.get("rendite_key", 3.0), 0.1, key="rendite_key")

        # --- 8. ZEITSTRAHL-SIMULATION ---
        if "betrachtungsjahr" not in st.session_state:
            st.session_state.betrachtungsjahr = aktuelles_jahr

        with st.expander("🕒 Zeitstrahl-Navigation", expanded=True):
            curr_year = st.session_state.betrachtungsjahr
            atz_mitte = atz_start + (atz_dauer / 2) if atz_simulieren else 0
            
            if atz_simulieren and atz_start <= curr_year < rentenbeginn:
                phase_label = "ATZ(A)" if curr_year < atz_mitte else "ATZ(P)"
                st.warning(f"Phase: {phase_label}")
            elif curr_year < rentenbeginn:
                phase_label = "Aktiv"
                st.info(f"Phase: {phase_label}")
            else:
                phase_label = "Ruhestand"
                st.success(f"Phase: {phase_label}")

            def fmt_j(j): return f"{j:.1f}".replace(".0", "") if j % 1 != 0 else f"{int(j)}"
            st.caption("Wichtige Meilensteine:")
            if atz_simulieren:
                m_cols = st.columns(3)
                m_cols[0].caption(f"🔵 A: {fmt_j(atz_start)}")
                m_cols[1].caption(f"🟡 P: {fmt_j(atz_mitte)}")
                m_cols[2].caption(f"🟢 Rente: {fmt_j(rentenbeginn)}")
            else:
                m_cols = st.columns(2)
                m_cols[0].caption(f"📍 Heute: {aktuelles_jahr}")
                m_cols[1].caption(f"🟢 Rente: {fmt_j(rentenbeginn)}")

            betrachtungsjahr = st.slider("Betrachtungsjahr ausblenden", aktuelles_jahr, geburtsjahr + 100, key="betrachtungsjahr", label_visibility="collapsed")
            st.caption(f"Betrachtungsjahr: {betrachtungsjahr} (Alter: {betrachtungsjahr - geburtsjahr} Jahre)")

        return {
            "nutzer_name": nutzer_name, "geburtsjahr": geburtsjahr, "rentenbeginn": rentenbeginn,
            "atz_simulieren": atz_simulieren, "atz_dauer": atz_dauer if atz_simulieren else 0,
            "atz_start": atz_start, "atz_ende": rentenbeginn, "atz_aufstockung_pct": atz_aufst,
            "aktuelles_brutto": aktuelles_brutto, "aktuelles_netto": aktuelles_netto,
            "ausgaben_input": ausgaben_input, "anpassungsfaktor_input": anpassungsfaktor_input,
            "einnahmen": st.session_state.einnahmen, "show_values": show_values,
            "ausgaben_kategorien": ausgaben_kategorien, "aktuelles_jahr": aktuelles_jahr,
            "betrachtungsjahr": betrachtungsjahr, "kinderzahl": kinderzahl,
            "kirchensteuer_satz": kirchensteuer_satz, "inflation_rate": infl_rate,
            "rentenanpassung_rate": renten_anp, "bav_anpassung_rate": bav_anp,
            "startvermoegen": startvermoegen, "kapitalrendite": rendite
        }
