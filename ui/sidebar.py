import streamlit as st
from data.persistence import export_settings, import_settings

def render_sidebar():
    """Rendert die Sidebar des Rente-O-Mat."""
    
    # --- 1. IMPORT-LOGIK (Muss vor dem Rendern der Widgets laufen) ---
    if st.session_state.get("do_import") and st.session_state.get("import_file"):
        import_settings(st.session_state.import_file)
        # Flags zurücksetzen
        st.session_state.do_import = False
        st.session_state.import_file = None
        st.rerun()

    with st.sidebar:
        # --- PROFIL ---
        with st.expander("👤 Profil", expanded=True):
            nutzer_name = st.text_input("Name", value="Max Mustermann", key="nutzer_name_key")
            geburtsjahr = st.number_input("Geburtsjahr", value=1965, key="geburtsjahr_key")
            aktuelles_jahr = 2026
            
            st.divider()
            
            # EXPORT
            export_params = {
                "nutzer_name": nutzer_name,
                "geburtsjahr": geburtsjahr,
                "rentenbeginn": st.session_state.get("rentenbeginn_input", 2031),
                "atz_simulieren": st.session_state.get("atz_sim_input", False),
                "atz_dauer": st.session_state.get("atz_dauer_input", 6),
                "atz_aufstockung_pct": st.session_state.get("atz_aufst_key", 20),
                "aktuelles_brutto": st.session_state.get("brutto_key", 6000.0),
                "aktuelles_netto": st.session_state.get("netto_key", 4500.0),
                "show_values": st.session_state.get("show_vals_key", True),
                "einnahmen": st.session_state.einnahmen,
                "ausgaben_input": {k: st.session_state.get(f"c_{k}", 200.0 if k=="Wohnen" else 200.0) for k in ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]},
                "anpassungsfaktor_input": {k: st.session_state.get(f"a_{k}", 100) for k in ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]}
            }
            json_str = export_settings(export_params)
            
            # Button 1: Exportieren
            st.download_button(
                label="Exportieren", 
                data=json_str, 
                file_name=f"R-O-M_{nutzer_name.replace(' ', '_')}.json", 
                mime="application/json", 
                use_container_width=True
            )
            
            # Button 2: Import (Uploader)
            uploaded_file = st.file_uploader(
                "Import", 
                type=["json"], 
                key="json_uploader_widget",
                label_visibility="visible"
            )
            
            # Button 3: Importieren (nur wenn Datei vorhanden)
            if uploaded_file:
                if st.button("Importieren", use_container_width=True):
                    st.session_state.import_file = uploaded_file
                    st.session_state.do_import = True
                    st.rerun()
        
        # --- ZEITSTRAHL-SIMULATION ---
        if "betrachtungsjahr" not in st.session_state:
            st.session_state.betrachtungsjahr = aktuelles_jahr

        with st.expander("🕒 Zeitstrahl-Simulation", expanded=True):
            rentenbeginn_val = st.session_state.get("rentenbeginn_input", 2031)
            atz_sim_val = st.session_state.get("atz_sim_input", False)
            atz_dauer_val = st.session_state.get("atz_dauer_input", 6)
            
            atz_start_val = rentenbeginn_val - atz_dauer_val
            atz_mitte = atz_start_val + (atz_dauer_val / 2)
            
            curr_year = st.session_state.betrachtungsjahr
            if atz_sim_val and atz_start_val <= curr_year < rentenbeginn_val:
                phase_label = "ATZ(A)" if curr_year < atz_mitte else "ATZ(P)"
                st.warning(f"Phase: {phase_label}")
            elif curr_year < rentenbeginn_val:
                phase_label = "Erwerb"
                st.info(f"Phase: {phase_label}")
            else:
                phase_label = "Ruhestand"
                st.success(f"Phase: {phase_label}")

            def fmt_j(j): return f"{j:.1f}".replace(".0", "") if j % 1 != 0 else f"{int(j)}"
            st.caption("Wichtige Meilensteine:")
            if atz_sim_val:
                m_cols = st.columns(3)
                m_cols[0].caption(f"🔵 A: {fmt_j(atz_start_val)}")
                m_cols[1].caption(f"🟡 P: {fmt_j(atz_mitte)}")
                m_cols[2].caption(f"🟢 Rente: {fmt_j(rentenbeginn_val)}")
            else:
                m_cols = st.columns(2)
                m_cols[0].caption(f"📍 Heute: {aktuelles_jahr}")
                m_cols[1].caption(f"🟢 Rente: {fmt_j(rentenbeginn_val)}")

            betrachtungsjahr = st.slider("Betrachtungsjahr", aktuelles_jahr, geburtsjahr + 100, key="betrachtungsjahr")
            st.caption(f"Alter: {betrachtungsjahr - geburtsjahr} Jahre")

        # --- MEILENSTEINE ---
        with st.expander("📅 Meilensteine", expanded=False):
            rentenbeginn = st.number_input("Rentenbeginn (Jahr)", value=2031, key="rentenbeginn_input")
            
            if "prev_rentenbeginn" not in st.session_state:
                st.session_state.prev_rentenbeginn = rentenbeginn
                
            if rentenbeginn != st.session_state.prev_rentenbeginn:
                for e in st.session_state.einnahmen:
                    if e["start"] == st.session_state.prev_rentenbeginn:
                        e["start"] = rentenbeginn
                st.session_state.prev_rentenbeginn = rentenbeginn

            atz_simulieren = st.checkbox("ATZ einplanen", value=False, key="atz_sim_input")
            if atz_simulieren:
                atz_dauer = st.slider("ATZ Dauer (Jahre)", 1, 10, 6, key="atz_dauer_input")
                atz_start = rentenbeginn - atz_dauer
                st.info(f"ATZ-Beginn: {atz_start}")
                atz_ende = rentenbeginn
            else:
                atz_start, atz_ende = 9999, 9999

        # --- EINNAHMEQUELLEN ---
        with st.expander("💰 Einnahmequellen", expanded=False):
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
                f_betrag = st.number_input("Betrag (€)", value=float(current_e["betrag"]))
                f_start = st.number_input("Von", value=int(current_e["start"]))
                f_ende = st.number_input("Bis", value=int(current_e["ende"]))
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

        # --- FINANZEN AKTUELL ---
        with st.expander("💶 Finanzen Aktuell", expanded=False):
            aktuelles_brutto = st.number_input("Brutto/mtl.", value=6000.0, key="brutto_key")
            atz_aufst = st.slider("ATZ-Aufst. %", 20, 50, 20, key="atz_aufst_key")
            aktuelles_netto = st.number_input("Netto/mtl.", value=4500.0, key="netto_key")
            show_values = st.checkbox("Werte zeigen", value=True, key="show_vals_key")

        # --- HAUSHALTSBUCH ---
        with st.expander("🏠 Haushaltsbuch", expanded=False):
            ausgaben_kategorien = ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]
            ausgaben_input, anpassungsfaktor_input = {}, {}
            for kat in ausgaben_kategorien:
                c1, c2 = st.columns([0.6, 0.4])
                ausgaben_input[kat] = c1.number_input(f"{kat}", value=1200.0 if kat=="Wohnen" else 200.0, key=f"c_{kat}")
                anpassungsfaktor_input[kat] = c2.slider(f"RV%", 0, 200, 100, key=f"a_{kat}")

        return {
            "nutzer_name": nutzer_name, "geburtsjahr": geburtsjahr, "rentenbeginn": rentenbeginn,
            "atz_simulieren": atz_simulieren, "atz_dauer": atz_dauer if atz_simulieren else 0,
            "atz_start": atz_start_val, "atz_ende": rentenbeginn, "atz_aufstockung_pct": atz_aufst,
            "aktuelles_brutto": aktuelles_brutto, "aktuelles_netto": aktuelles_netto,
            "ausgaben_input": ausgaben_input, "anpassungsfaktor_input": anpassungsfaktor_input,
            "einnahmen": st.session_state.einnahmen, "show_values": show_values,
            "ausgaben_kategorien": ausgaben_kategorien, "aktuelles_jahr": aktuelles_jahr,
            "betrachtungsjahr": betrachtungsjahr
        }
