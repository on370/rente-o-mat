import streamlit as st

def render_sidebar():
    """Rendert die Sidebar und gibt die gesammelten Parameter zurück."""
    with st.sidebar:
        # --- PROFIL ---
        with st.expander("👤 Profil", expanded=True):
            nutzer_name = st.text_input("Name", value="Max Mustermann")
            geburtsjahr = st.number_input("Geburtsjahr", value=1965)
            aktuelles_jahr = 2026
        
        # --- ZEITSTRAHL-SIMULATION ---
        if "betrachtungsjahr" not in st.session_state:
            st.session_state.betrachtungsjahr = aktuelles_jahr

        with st.expander("🕒 Zeitstrahl-Simulation", expanded=True):
            # Hilfsberechnung für Phasen-Label
            rentenbeginn_val = st.session_state.get("rentenbeginn_input", 2031)
            atz_sim_val = st.session_state.get("atz_sim_input", False)
            atz_dauer_val = st.session_state.get("atz_dauer_input", 6)
            
            # ATZ Start ist Rentenbeginn minus Dauer
            atz_start_val = rentenbeginn_val - atz_dauer_val
            atz_mitte = atz_start_val + (atz_dauer_val / 2)
            
            curr_year = st.session_state.betrachtungsjahr
            if atz_sim_val and atz_start_val <= curr_year < rentenbeginn_val:
                # ATZ Phase (Aktiv oder Passiv)
                phase_label = "ATZ(A)" if curr_year < atz_mitte else "ATZ(P)"
                st.warning(f"Aktuelle Phase: {phase_label}")
            elif curr_year < rentenbeginn_val:
                # Vor der ATZ oder ATZ nicht aktiv
                phase_label = "Erwerb"
                st.info(f"Aktuelle Phase: {phase_label}")
            else:
                # Nach Rentenbeginn
                phase_label = "Ruhestand"
                st.success(f"Aktuelle Phase: {phase_label}")

            # Meilenstein-Anzeige (Formatierung ohne .0)
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

            # Der Slider selbst
            betrachtungsjahr = st.slider("Betrachtungsjahr", aktuelles_jahr, geburtsjahr + 100, key="betrachtungsjahr")
            alter = betrachtungsjahr - geburtsjahr
            st.caption(f"Alter im gewählten Jahr: {alter} Jahre")

        # --- MEILENSTEINE ---
        with st.expander("📅 Meilensteine", expanded=False):
            rentenbeginn = st.number_input("Rentenbeginn (Jahr)", value=2031, key="rentenbeginn_input")
            atz_simulieren = st.checkbox("ATZ einplanen", value=False, key="atz_sim_input")
            if atz_simulieren:
                # Dauer ist jetzt das führende Feld für maximale Plausibilität
                atz_dauer = st.slider("ATZ Dauer (Jahre)", 1, 10, 6, key="atz_dauer_input")
                atz_start = rentenbeginn - atz_dauer
                st.info(f"Berechneter ATZ-Beginn: **{atz_start}**")
                st.caption("ℹ️ Dauer wird hälftig in Aktiv- und Passivphase aufgeteilt.")
                atz_ende = rentenbeginn
            else:
                atz_start, atz_ende = 9999, 9999

        # --- EINNAHMEQUELLEN ---
        with st.expander("💰 Einnahmequellen", expanded=False):
            with st.container():
                n_name = st.text_input("Name der Quelle", value="Private Rente")
                n_typ = st.selectbox("Typ", ["Gesetzlich", "bAV", "Privat", "Kapital", "Sonstiges"])
                n_betrag = st.number_input("Monatsbetrag (€)", value=500.0)
                n_start = st.number_input("Start (Jahr)", value=rentenbeginn)
                n_ende = st.number_input("Ende (Jahr)", value=2065)
                if st.button("Hinzufügen"):
                    st.session_state.einnahmen.append({"name": n_name, "betrag": n_betrag, "typ": n_typ, "start": n_start, "ende": n_ende})
                    st.rerun()

            st.divider()
            to_delete = []
            for i, e in enumerate(st.session_state.einnahmen):
                col_e1, col_e2 = st.columns([0.8, 0.2])
                col_e1.write(f"**{e['name']}** ({e['betrag']}€)")
                if col_e2.button("🗑️", key=f"del_{i}"): to_delete.append(i)
            if to_delete:
                for idx in sorted(to_delete, reverse=True): st.session_state.einnahmen.pop(idx)
                st.rerun()

        # --- FINANZEN AKTUELL ---
        with st.expander("💶 Finanzen Aktuell", expanded=False):
            aktuelles_brutto = st.number_input("Aktuelles Brutto-Gehalt (Monat)", value=6000.0)
            atz_aufstockung_pct = st.slider("ATZ-Aufstockung AG (%)", 20, 50, 20)
            aktuelles_netto = st.number_input("Aktuelles Netto-Einkommen (Monat)", value=4500.0)
            show_values = st.checkbox("Werte in Diagrammen anzeigen", value=True)

        # --- HAUSHALTSBUCH ---
        with st.expander("🏠 Haushaltsbuch", expanded=False):
            ausgaben_kategorien = ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]
            ausgaben_input, anpassungsfaktor_input = {}, {}
            for kat in ausgaben_kategorien:
                c1, c2 = st.columns([0.6, 0.4])
                default_val = 1200 if kat == "Wohnen" else 200
                ausgaben_input[kat] = c1.number_input(f"{kat}", value=float(default_val), key=f"c_{kat}")
                anpassungsfaktor_input[kat] = c2.slider(f"RV%", 0, 200, 100, key=f"a_{kat}")

    return {
        "nutzer_name": nutzer_name,
        "geburtsjahr": geburtsjahr,
        "aktuelles_jahr": aktuelles_jahr,
        "betrachtungsjahr": betrachtungsjahr,
        "rentenbeginn": rentenbeginn,
        "atz_simulieren": atz_simulieren,
        "atz_start": atz_start,
        "atz_ende": atz_ende,
        "atz_aufstockung_pct": atz_aufstockung_pct,
        "aktuelles_brutto": aktuelles_brutto,
        "aktuelles_netto": aktuelles_netto,
        "show_values": show_values,
        "ausgaben_input": ausgaben_input,
        "anpassungsfaktor_input": anpassungsfaktor_input,
        "ausgaben_kategorien": ausgaben_kategorien,
        "einnahmen": st.session_state.einnahmen
    }
