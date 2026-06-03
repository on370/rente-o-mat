from datetime import datetime

import streamlit as st

from config import DATENSCHUTZ_INFO
from data.persistence import export_settings, import_settings
from logic.rentenrecht import (
    berechne_monate_frueher,
    berechne_regelaltersgrenze,
    format_regelaltersgrenze,
)


def get_auto_entnahme_stats(asset_name):
    """
    Scans st.session_state.get("df_timeline") and retrieves the start/end years
    and average monthly rate of positive columns named f"Entnahme: {asset_name}".
    """
    df = st.session_state.get("df_timeline")
    if df is None or df.empty:
        return None
    
    col_name = f"Entnahme: {asset_name}"
    if col_name not in df.columns:
        return None
        
    df_pos = df[df[col_name] > 0.01]
    if df_pos.empty:
        return None
        
    start_jahr = int(df_pos["Jahr"].min())
    end_jahr = int(df_pos["Jahr"].max())
    avg_betrag = df_pos[col_name].mean()
    
    return {
        "start": start_jahr,
        "ende": end_jahr,
        "betrag": avg_betrag
    }


def render_sidebar():
    """Rendert die Sidebar des Rente-O-Mat in logischer Reihenfolge."""

    aktuelles_jahr = datetime.now().year

    # --- 0. INITIALISIERUNG ---
    if "uploader_id" not in st.session_state:
        st.session_state.uploader_id = 0
    geburtsjahr = st.session_state.get("geburtsjahr_key", 1965)
    geburtsmonat = st.session_state.get("geburtsmonat_key", 1)
    
    # Check if birth year or month changed, to update default retirement age
    if "prev_geburtsjahr" not in st.session_state:
        st.session_state["prev_geburtsjahr"] = geburtsjahr
    if "prev_geburtsmonat" not in st.session_state:
        st.session_state["prev_geburtsmonat"] = geburtsmonat
        
    regel_jahre, rag_monate = berechne_regelaltersgrenze(geburtsjahr)
    def_beginn_jahr = geburtsjahr + regel_jahre
    def_beginn_monat = geburtsmonat + rag_monate
    if def_beginn_monat > 12:
        def_beginn_jahr += 1
        def_beginn_monat -= 12
    
    if geburtsjahr != st.session_state["prev_geburtsjahr"] or geburtsmonat != st.session_state["prev_geburtsmonat"]:
        st.session_state["rentenbeginn_jahr_input"] = def_beginn_jahr
        st.session_state["rentenbeginn_monat_input"] = def_beginn_monat
        st.session_state["prev_geburtsjahr"] = geburtsjahr
        st.session_state["prev_geburtsmonat"] = geburtsmonat

    defaults = {
        "nutzer_name_key": "Max Mustermann",
        "geburtsjahr_key": 1965,
        "geburtsmonat_key": 1,
        "kinderzahl_key": 0,
        "rentenbeginn_jahr_input": def_beginn_jahr,
        "rentenbeginn_monat_input": def_beginn_monat,
        "atz_sim_input": False,
        "atz_dauer_input": 6,
        "brutto_key": 6000.0,
        "atz_aufst_key": 20,
        "netto_key": 4500.0,
        "show_vals_key": True,
        "infl_rate_key": 2.0,
        "renten_anp_key": 2.0,
        "renten_anp_display_key": "2% (Standard)",
        "bav_anp_key": 1.0,
        "gehalts_dyn_key": 1.0,
        "reinvest_target_key": "— Keine (nur Cash-Reserven) —",
        "liq_reserve_key": 10000.0,
        "liq_yield_key": 0.0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    r_jahr = st.session_state.get("rentenbeginn_jahr_input", def_beginn_jahr)
    r_monat = st.session_state.get("rentenbeginn_monat_input", def_beginn_monat)
    rentenbeginn = r_jahr + (r_monat - 1) / 12
    st.session_state["rentenbeginn_input"] = rentenbeginn

    if "einnahmen" not in st.session_state:
        st.session_state.einnahmen = [
            {
                "name": "Gesetzliche Rente",
                "betrag": 2200.0,
                "typ": "Gesetzlich",
                "start": def_beginn_jahr + (def_beginn_monat-1)/12,
                "ende": def_beginn_jahr + 40,
            },
            {
                "name": "Betriebsrente",
                "betrag": 600.0,
                "typ": "bAV",
                "start": def_beginn_jahr + (def_beginn_monat-1)/12,
                "ende": def_beginn_jahr + 40,
            },
        ]
    if "assets" not in st.session_state:
        st.session_state.assets = []
    if "befristete_ausgaben" not in st.session_state:
        st.session_state.befristete_ausgaben = []
    if "einmalige_ausgaben" not in st.session_state:
        st.session_state.einmalige_ausgaben = []

    # Initialisierung des strukturierten Haushaltsbuchs
    def sync_haushaltsbuch():
        if "haushaltsbuch_kategorien" not in st.session_state:
            default_kats = ["Wohnen", "Mobilität", "Lebensmittel", "Versicherungen", "Gesundheit", "Freizeit", "Sonstiges"]
            st.session_state.haushaltsbuch_kategorien = []
            for kat in default_kats:
                c_key = f"c_{kat}"
                a_key = f"a_{kat}"
                val = st.session_state.get(c_key, 1200.0 if kat == "Wohnen" else 200.0)
                rv = st.session_state.get(a_key, 100)
                st.session_state.haushaltsbuch_kategorien.append({
                    "id": kat,
                    "name": kat,
                    "parent_id": None,
                    "is_group": False,
                    "betrag": float(val),
                    "rv_pct": int(rv)
                })

        for kat in st.session_state.haushaltsbuch_kategorien:
            if not kat.get("is_group"):
                c_key = f"c_{kat['id']}"
                a_key = f"a_{kat['id']}"
                if c_key in st.session_state:
                    kat["betrag"] = float(st.session_state[c_key])
                else:
                    st.session_state[c_key] = float(kat.get("betrag", 0.0))
                if a_key in st.session_state:
                    kat["rv_pct"] = int(st.session_state[a_key])
                else:
                    st.session_state[a_key] = int(kat.get("rv_pct", 100))

    sync_haushaltsbuch()

    ausgaben_kategorien = [
        kat["id"]
        for kat in st.session_state.haushaltsbuch_kategorien
        if not kat.get("is_group")
    ]
    id_to_name = {
        kat["id"]: kat["name"]
        for kat in st.session_state.haushaltsbuch_kategorien
    }

    # --- 1. IMPORT-LOGIK (Muss vor dem Rendern der Widgets laufen) ---
    if st.session_state.get("do_import") and st.session_state.get("import_file"):
        success = import_settings(st.session_state.import_file)
        # Flags zurücksetzen
        st.session_state.do_import = False
        st.session_state.import_file = None
        if success:
            st.session_state.uploader_id += 1
            st.toast("✅ Import erfolgreich!", icon="🎉")
        st.session_state.global_rerun = True

    with st.sidebar:
        # --- 2. PROFIL ---
        with st.expander("👤 Profil", expanded=True):
            nutzer_name = st.text_input(
                "Name",
                key="nutzer_name_key",
                help="Wird für den Dateinamen beim Export verwendet.",
            )
            col_gj, col_gm = st.columns([0.6, 0.4])
            geburtsjahr = col_gj.number_input(
                "Geburtsjahr",
                min_value=1940,
                max_value=2010,
                key="geburtsjahr_key",
                help="Dient der Berechnung von Freibeträgen und Renten-Altersgrenzen.",
            )
            monate_namen = [
                "Januar", "Februar", "März", "April", "Mai", "Juni",
                "Juli", "August", "September", "Oktober", "November", "Dezember"
            ]
            geburtsmonat = col_gm.selectbox(
                "Geburtsmonat",
                options=range(1, 13),
                format_func=lambda m: monate_namen[m-1],
                key="geburtsmonat_key",
            )

            kinderzahl = st.number_input(
                "Anzahl Kinder",
                min_value=0,
                max_value=10,
                key="kinderzahl_key",
                help="Beeinflusst den Beitrag zur Pflegeversicherung",
            )

            kist_options = {
                "Keine": 0.0,
                "8% (Bayern, BW)": 0.08,
                "9% (Restl. Bundesländer)": 0.09,
            }
            kist_display = st.selectbox(
                "Kirchensteuer",
                list(kist_options.keys()),
                index=0,
                key="kist_display_key",
            )
            kirchensteuer_satz = kist_options[kist_display]
            st.session_state["kist_key"] = kirchensteuer_satz  # Speichern für Export

            st.divider()

            # EXPORT
            export_params = {
                "nutzer_name": nutzer_name,
                "geburtsjahr": geburtsjahr,
                "geburtsmonat": st.session_state.get("geburtsmonat_key", 1),
                "kinderzahl": kinderzahl,
                "kirchensteuer_satz": kirchensteuer_satz,
                "rentenbeginn": st.session_state.get(
                    "rentenbeginn_input", geburtsjahr + 67
                ),
                "atz_simulieren": st.session_state.get("atz_sim_input", False),
                "atz_dauer": st.session_state.get("atz_dauer_input", 6),
                "atz_aufstockung_pct": st.session_state.get("atz_aufst_key", 20),
                "aktuelles_brutto": st.session_state.get("brutto_key", 6000.0),
                "aktuelles_netto": st.session_state.get("netto_key", 4500.0),
                "show_values": st.session_state.get("show_vals_key", True),
                "einnahmen": st.session_state.get("einnahmen", []),
                "haushaltsbuch_kategorien": st.session_state.get("haushaltsbuch_kategorien", []),
                "ausgaben_input": {
                    kat["id"]: kat["betrag"]
                    for kat in st.session_state.get("haushaltsbuch_kategorien", [])
                    if not kat.get("is_group")
                },
                "anpassungsfaktor_input": {
                    kat["id"]: kat["rv_pct"]
                    for kat in st.session_state.get("haushaltsbuch_kategorien", [])
                    if not kat.get("is_group")
                },
                "inflation_rate": st.session_state.get("infl_rate_key", 2.0),
                "rentenanpassung_rate": st.session_state.get("renten_anp_key", 2.0),
                "bav_anpassung_rate": st.session_state.get("bav_anp_key", 1.0),
                "gehalts_dynamik": st.session_state.get("gehalts_dyn_key", 1.0),
                "reinvest_target": st.session_state.get("reinvest_target_key", ""),
                "liquidity_reserve": st.session_state.get("liq_reserve_key", 10000.0),
                "liquidity_yield": st.session_state.get("liq_yield_key", 0.0),
                "befristete_ausgaben": st.session_state.get("befristete_ausgaben", []),
                "einmalige_ausgaben": st.session_state.get("einmalige_ausgaben", []),
                "assets": st.session_state.get("assets", []),
                "entnahme_strategie": st.session_state.get("entnahme_strategie_key", "Manuell (Keine Automatik)"),
                "entnahme_wasserfall_reihenfolge": st.session_state.get("entnahme_wasserfall_reihenfolge", []),
                "entnahme_fix_pct": st.session_state.get("entnahme_fix_pct", 4.0),
                "entnahme_ziel_alter": st.session_state.get("entnahme_ziel_alter", 95),
            }
            json_str = export_settings(export_params)

            st.markdown("💾 **Datenmanagement**", help=DATENSCHUTZ_INFO)
            with st.popover("⚙️ Einstellungen exportieren", use_container_width=True):
                exp_fn_default = f"ROM_Profil_{nutzer_name.replace(' ', '_')}"
                exp_fn = st.text_input("Dateiname (.json)", value=exp_fn_default)
                st.download_button(
                    label="Export",
                    data=json_str,
                    file_name=f"{exp_fn}.json",
                    mime="application/json",
                    use_container_width=True,
                )

            uploaded_file = st.file_uploader(
                "Import",
                type=["json"],
                key=f"json_uploader_widget_{st.session_state.uploader_id}",
                help=DATENSCHUTZ_INFO,
            )
            if uploaded_file and st.button("Importieren", width="stretch"):
                st.session_state.import_file = uploaded_file
                st.session_state.do_import = True
                st.session_state.global_rerun = True

        # --- 3. MEILENSTEINE ---
        rag_jahre, rag_monate = berechne_regelaltersgrenze(geburtsjahr)
        default_jahr = geburtsjahr + rag_jahre
        default_monat = rag_monate + 1  # +1 weil Monate 1-12
        if default_monat > 12:
            default_jahr += 1
            default_monat -= 12

        with st.expander("📅 Meilensteine", expanded=True):
            col_j, col_m = st.columns([0.6, 0.4])
            r_jahr = col_j.number_input(
                "Rentenbeginn (Jahr)",
                min_value=aktuelles_jahr,
                key="rentenbeginn_jahr_input",
            )
            r_monat = col_m.selectbox(
                "Monat",
                range(1, 13),
                key="rentenbeginn_monat_input",
            )

            # Rentenbeginn als Dezimaljahr für die Engine
            rentenbeginn = r_jahr + (r_monat - 1) / 12
            st.session_state["rentenbeginn_input"] = rentenbeginn

            if "prev_rentenbeginn" not in st.session_state:
                st.session_state.prev_rentenbeginn = rentenbeginn

            if rentenbeginn != st.session_state.prev_rentenbeginn:
                for e in st.session_state.einnahmen:
                    if e["start"] == st.session_state.prev_rentenbeginn:
                        e["start"] = rentenbeginn
                st.session_state.prev_rentenbeginn = rentenbeginn

            atz_simulieren = st.checkbox(
                "ATZ einplanen",
                key="atz_sim_input",
                help="Simuliert eine Altersteilzeit (Blockmodell) direkt vor dem Rentenbeginn.",
            )
            if atz_simulieren:
                max_atz = int(max(1, rentenbeginn - aktuelles_jahr))
                if max_atz > 1:
                    atz_dauer = st.slider(
                        "ATZ Dauer (Jahre)",
                        1,
                        max_atz,
                        key="atz_dauer_input",
                    )
                else:
                    atz_dauer = 1
                    st.write(
                        f"ATZ Dauer: **{atz_dauer} Jahr** (begrenzt durch Rentenbeginn)"
                    )

                atz_start = rentenbeginn - atz_dauer
                monate_namen = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
                # Da atz_dauer eine ganze Zahl ist, bleibt der Monat identisch mit dem Rentenbeginn
                atz_start_str = f"{monate_namen[r_monat-1]} {int(r_jahr - atz_dauer)}"
                st.info(f"📅 **ATZ-Beginn:** {atz_start_str}")
                atz_ende = rentenbeginn
            else:
                atz_dauer = 0
                atz_start, atz_ende = 9999, 9999

            # --- INFOBOX FÜR ABSCHLAG UND STEUER ---
            st.divider()
            from logic.rentenrecht import (
                berechne_monate_frueher,
                format_regelaltersgrenze,
            )

            monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn, geburtsmonat)
            abschlag_pct = min(14.4, monate_frueher * 0.3)

            from logic.taxes import berechne_rentensteuer_anteil

            steuer_anteil = berechne_rentensteuer_anteil(rentenbeginn)

            rag_str = format_regelaltersgrenze(geburtsjahr)
            st.success(f"**Deine Regelaltersgrenze:** {rag_str}")

            # --- NEU: Präzise EP-Analyse für die Infobox ---
            from config import RENTENWERT_AKTUELL
            from logic.rentenrecht import (
                berechne_beitragsverlust_logic,
                berechne_ep_pro_jahr,
            )

            rentenanpassung_rate = st.session_state.get("renten_anp_key", 2.0)
            brutto_fuer_ep = st.session_state.get("brutto_key", 6000.0)
            ep_pro_jahr = berechne_ep_pro_jahr(brutto_fuer_ep, aktuelles_jahr)

            # K7/M1: Präzise EP-Akkumulation unter Berücksichtigung der ATZ (80% Aufstockung)
            from logic.engine import get_phase
            jahre_bis_beginn = max(0, rentenbeginn - aktuelles_jahr)
            ep_zuwachs = 0.0
            atz_start_jahr = rentenbeginn - atz_dauer if atz_simulieren else 9999
            
            for j_sim in range(aktuelles_jahr, int(rentenbeginn)):
                phase_sim = get_phase(j_sim + 0.5, atz_simulieren, atz_start_jahr, rentenbeginn)
                if phase_sim == "Aktiv":
                    ep_zuwachs += ep_pro_jahr
                elif "ATZ" in phase_sim:
                    ep_zuwachs += ep_pro_jahr * 0.8
            
            # Bruchstück für das letzte Jahr vor Rentenbeginn
            rest_jahr = rentenbeginn - int(rentenbeginn)
            if rest_jahr > 0:
                phase_sim = get_phase(rentenbeginn - 0.01, atz_simulieren, atz_start_jahr, rentenbeginn)
                factor = 0.8 if "ATZ" in phase_sim else 1.0
                ep_zuwachs += ep_pro_jahr * factor * rest_jahr

            # K2: Rentenwert projizieren für Infobox
            rw_proj = (
                RENTENWERT_AKTUELL
                * (1 + rentenanpassung_rate / 100) ** jahre_bis_beginn
            )

            monate_frueher = berechne_monate_frueher(geburtsjahr, rentenbeginn, geburtsmonat)
            bv_res = berechne_beitragsverlust_logic(
                monate_frueher, ep_pro_jahr, rw_proj
            )

            # --- NEU: Break-Even Berechnung für Infobox ---
            from logic.engine import calculate_break_even_data

            # Params-Pack für Break-Even (muss aktuellste Werte enthalten)
            be_params = {
                "geburtsjahr": geburtsjahr,
                "geburtsmonat": geburtsmonat,
                "aktuelles_jahr": aktuelles_jahr,
                "rentenbeginn": rentenbeginn,
                "aktuelles_brutto": st.session_state.get("brutto_key", 6000.0),
                "kinderzahl": kinderzahl,
                "kirchensteuer_satz": kirchensteuer_satz,
                "einnahmen": st.session_state.einnahmen,
                "rentenanpassung_rate": st.session_state.get("renten_anp_key", 2.0),
                "inflation_rate": st.session_state.get("infl_rate_key", 2.0),
            }

            try:
                _, be_jahr, be_alter = calculate_break_even_data(be_params)
                be_info = f"{be_alter} J. ({be_jahr})" if be_jahr else "Nicht erreicht"
            except Exception:
                be_info = "Berechnung läuft..."

            info_text = f"""
            **Regelaltersgrenze:** {rag_str}

            **Analyse vorzeitiger Eintritt:**
            * **Rentenabschlag (GRV):** {abschlag_pct:.1f} %
            * **Beitragsverlust:** -{bv_res["ep"]:.2f} EP / -{bv_res["euro"]:.2f} € mtl.
            * **EP-Zuwachs bis Start:** +{ep_zuwachs:.2f} EP
            * **Break-Even (vs. RAG):** {be_info}

            **Steuerpflichtiger Anteil:** {steuer_anteil:.1f} %
            """
            st.info(info_text)

            with st.popover("❓ Erläuterung der Werte"):
                st.markdown(f"""
                **Rentenabschlag ({abschlag_pct:.1f} %):**
                Dies ist der *versicherungsmathematische Abschlag*. Da du früher in Rente gehst und diese somit voraussichtlich länger beziehst, wird die Rente lebenslang um 0,3 % pro Monat gekürzt.

                **Beitragsverlust (-{bv_res["ep"]:.2f} EP):**
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

        # --- 4. ERWERBSEINNAHMEN ---
        with st.expander("💶 Erwerbseinnahmen", expanded=False):
            aktuelles_brutto = st.number_input(
                "Brutto/mtl.",
                key="brutto_key",
                help="Dein aktuelles monatliches Bruttogehalt (als Basis für die Aktivphase).",
            )
            atz_aufst = st.slider(
                "ATZ-Aufst. % (vom halben Brutto)",
                20,
                50,
                key="atz_aufst_key",
                help="Gesetzliches Minimum sind 20% (§3 AltTZG). Viele Tarifverträge (z.B. Metall/Chemie) liegen bei ca. 35-40%, um eine Netto-Quote von 85-90% zu erreichen. Die Aufstockung ist steuerfrei (Progressionsvorbehalt).",
            )

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
                "ausgaben_kategorien": [],
                "ausgaben_input": {},
                "einnahmen": [],
            }

            # 1. Aktiv-Netto berechnen (Jahr < ATZ_start -> Aktiv)
            res_aktiv = calculate_financials_for_year(aktuelles_jahr - 1, tmp_params)

            # 2. ATZ-Netto berechnen (Jahr = ATZ_start -> ATZ(A))
            res_atz = calculate_financials_for_year(aktuelles_jahr, tmp_params)

            if res_aktiv["Netto-Einkommen"] > 0:
                quote = (
                    res_atz["Netto-Einkommen"] / res_aktiv["Netto-Einkommen"]
                ) * 100
                st.info(
                    f"**ATZ-Netto:** {res_atz['Netto-Einkommen']:.0f} €/mtl.\n\n*(Entspricht **{quote:.1f} %** deines bisherigen Netto-Gehalts von {res_aktiv['Netto-Einkommen']:.0f} €)*"
                )

            aktuelles_netto = st.number_input(
                "Netto/mtl. (Optional)",
                key="netto_key",
                help="Dein echtes ausgezahltes Netto. Wird nur für das Status-Quo-Sankey ganz oben verwendet, um Abweichungen zu erkennen.",
            )
            show_values = st.checkbox(
                "Werte im Sankey zeigen",
                key="show_vals_key",
            )

        # --- 6. HAUSHALTSBUCH ---
        with st.expander("🏠 Haushaltsbuch (Ausgaben)", expanded=False):
            st.caption("Ausgabe in Aktivphase | Rentenanpassung in %")
            
            kats = st.session_state.haushaltsbuch_kategorien
            group_ids = {k["id"] for k in kats if k.get("is_group")}
            
            # Helper to calculate group sum
            def get_group_sum(group_id):
                s = 0.0
                for kat in kats:
                    if not kat.get("is_group") and kat.get("parent_id") == group_id:
                        s += float(st.session_state.get(f"c_{kat['id']}", kat.get("betrag", 0.0)))
                return s

            # Group children and find top level items
            group_children = {gid: [] for gid in group_ids}
            top_level_items = []

            for kat in kats:
                pid = kat.get("parent_id")
                if pid and pid in group_ids:
                    group_children[pid].append(kat)
                else:
                    top_level_items.append(kat)

            # Separate top level categories (main level) and groups (Sammelkategorien)
            main_level_categories = [item for item in top_level_items if not item.get("is_group")]
            group_categories = [item for item in top_level_items if item.get("is_group")]

            # 1. Render all main level categories first
            for item in main_level_categories:
                # Top-level leaf rendering
                # Header: Name next to settings gear
                c_lbl, c_gear = st.columns([0.85, 0.15])
                c_lbl.markdown(f"**{item['name']}**")
                with c_gear:
                    with st.popover("⚙️", key=f"opt_{item['id']}_{st.session_state.uploader_id}"):
                        st.markdown("**Kategorie-Optionen**")
                        # Rename
                        new_name = st.text_input("Name bearbeiten", value=item["name"], key=f"ren_{item['id']}_{st.session_state.uploader_id}")
                        if new_name != item["name"] and new_name.strip():
                            cleaned_name = new_name.strip()
                            if any(k["name"].lower() == cleaned_name.lower() and k["id"] != item["id"] for k in st.session_state.haushaltsbuch_kategorien):
                                st.error("Name existiert bereits!")
                            else:
                                item["name"] = cleaned_name
                                st.session_state.global_rerun = True
                                st.rerun()
                        # Move parent group
                        p_options = ["— Hauptebene —"] + [g["name"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                        p_ids = [None] + [g["id"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                        curr_pid = item.get("parent_id")
                        curr_idx = p_ids.index(curr_pid) if curr_pid in p_ids else 0
                        sel_p = st.selectbox("Gruppe wählen", options=range(len(p_options)), format_func=lambda idx: p_options[idx], index=curr_idx, key=f"p_sel_{item['id']}_{st.session_state.uploader_id}")
                        new_pid = p_ids[sel_p]
                        if new_pid != curr_pid:
                            item["parent_id"] = new_pid
                            st.session_state.global_rerun = True
                            st.rerun()
                        # Delete
                        if st.button("🗑️ Löschen", key=f"del_{item['id']}_{st.session_state.uploader_id}", use_container_width=True):
                            st.session_state.haushaltsbuch_kategorien = [k for k in st.session_state.haushaltsbuch_kategorien if k["id"] != item["id"]]
                            # Fix M5: Bereinige befristete und einmalige Ausgaben
                            for ba in st.session_state.befristete_ausgaben:
                                if ba.get("kategorie") == item["id"]:
                                    ba["kategorie"] = ""
                            for ea in st.session_state.einmalige_ausgaben:
                                if ea.get("kategorie") == item["id"]:
                                    ea["kategorie"] = ""
                            c_key = f"c_{item['id']}"
                            a_key = f"a_{item['id']}"
                            if c_key in st.session_state:
                                del st.session_state[c_key]
                            if a_key in st.session_state:
                                del st.session_state[a_key]
                            st.session_state.global_rerun = True
                            st.rerun()
                
                # Inputs: side-by-side
                c_val, c_sl = st.columns([0.5, 0.5])
                c_val.number_input(
                    "Betrag",
                    min_value=0.0,
                    key=f"c_{item['id']}",
                    label_visibility="collapsed",
                )
                c_sl.slider(
                    "RV%",
                    0,
                    200,
                    key=f"a_{item['id']}",
                    label_visibility="collapsed",
                )

            # 2. Render groups (Sammelkategorien) if present
            if group_categories:
                st.markdown("---") # Divider between main level and groups
                
                # Render "Alle Sammel-Kat." Button below the divider
                for g in group_categories:
                    col_key = f"collapsed_{g['id']}"
                    if col_key not in st.session_state:
                        st.session_state[col_key] = False
                
                any_expanded = any(not st.session_state[f"collapsed_{g['id']}"] for g in group_categories)
                all_toggle_icon = "▼" if any_expanded else "▶"
                if st.button(f"{all_toggle_icon} Alle Sammel-Kat.", key=f"toggle_all_groups_{st.session_state.uploader_id}", use_container_width=True):
                    target_state = any_expanded
                    for g in group_categories:
                        st.session_state[f"collapsed_{g['id']}"] = target_state
                    st.session_state.global_rerun = True
                    st.rerun()
                
                # Loop to render Sammelkategorien
                for item in group_categories:
                    g_sum = get_group_sum(item["id"])
                    
                    col_key = f"collapsed_{item['id']}"
                    if col_key not in st.session_state:
                        st.session_state[col_key] = False
                    
                    collapsed = st.session_state[col_key]
                    toggle_icon = "▶" if collapsed else "▼"
                    
                    c_g1, c_g2, c_g3 = st.columns([0.12, 0.73, 0.15])
                    if c_g1.button(toggle_icon, key=f"tg_{item['id']}_{st.session_state.uploader_id}", use_container_width=True):
                        st.session_state[col_key] = not collapsed
                        st.session_state.global_rerun = True
                        st.rerun()
                        
                    g_sum_str = f"{g_sum:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                    c_g2.markdown(f"📁 **{item['name']}** ({g_sum_str})")
                    with c_g3:
                        with st.popover("⚙️", key=f"opt_{item['id']}_{st.session_state.uploader_id}"):
                            st.markdown("**Gruppen-Optionen**")
                            # Rename group
                            new_name = st.text_input("Name bearbeiten", value=item["name"], key=f"ren_{item['id']}_{st.session_state.uploader_id}")
                            if new_name != item["name"] and new_name.strip():
                                cleaned_name = new_name.strip()
                                if any(k["name"].lower() == cleaned_name.lower() and k["id"] != item["id"] for k in st.session_state.haushaltsbuch_kategorien):
                                    st.error("Name existiert bereits!")
                                else:
                                    item["name"] = cleaned_name
                                    st.session_state.global_rerun = True
                                    st.rerun()
                            # Delete group with child promotion
                            if st.button("🗑️ Gruppe löschen", key=f"del_{item['id']}_{st.session_state.uploader_id}", use_container_width=True):
                                for child in st.session_state.haushaltsbuch_kategorien:
                                    if child.get("parent_id") == item["id"]:
                                        child["parent_id"] = None
                                st.session_state.haushaltsbuch_kategorien = [k for k in st.session_state.haushaltsbuch_kategorien if k["id"] != item["id"]]
                                # Fix M5: Bereinige befristete und einmalige Ausgaben
                                for ba in st.session_state.befristete_ausgaben:
                                    if ba.get("kategorie") == item["id"]:
                                        ba["kategorie"] = ""
                                for ea in st.session_state.einmalige_ausgaben:
                                    if ea.get("kategorie") == item["id"]:
                                        ea["kategorie"] = ""
                                st.session_state.global_rerun = True
                                st.rerun()
                    
                    # Children of this group (only if expanded)
                    if not collapsed:
                        children = group_children.get(item["id"], [])
                        for child in children:
                            # Child Header: Name next to settings gear
                            c_lbl, c_gear = st.columns([0.85, 0.15])
                            c_lbl.markdown(f"└─ **{child['name']}**")
                            with c_gear:
                                with st.popover("⚙️", key=f"opt_{child['id']}_{st.session_state.uploader_id}"):
                                    st.markdown("**Kategorie-Optionen**")
                                    # Rename
                                    new_name = st.text_input("Name bearbeiten", value=child["name"], key=f"ren_{child['id']}_{st.session_state.uploader_id}")
                                    if new_name != child["name"] and new_name.strip():
                                        cleaned_name = new_name.strip()
                                        if any(k["name"].lower() == cleaned_name.lower() and k["id"] != child["id"] for k in st.session_state.haushaltsbuch_kategorien):
                                            st.error("Name existiert bereits!")
                                        else:
                                            child["name"] = cleaned_name
                                            st.session_state.global_rerun = True
                                            st.rerun()
                                    # Move parent group
                                    p_options = ["— Hauptebene —"] + [g["name"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                                    p_ids = [None] + [g["id"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                                    curr_pid = child.get("parent_id")
                                    curr_idx = p_ids.index(curr_pid) if curr_pid in p_ids else 0
                                    sel_p = st.selectbox("Gruppe wählen", options=range(len(p_options)), format_func=lambda idx: p_options[idx], index=curr_idx, key=f"p_sel_{child['id']}_{st.session_state.uploader_id}")
                                    new_pid = p_ids[sel_p]
                                    if new_pid != curr_pid:
                                        child["parent_id"] = new_pid
                                        st.session_state.global_rerun = True
                                        st.rerun()
                                    # Delete
                                    if st.button("🗑️ Löschen", key=f"del_{child['id']}_{st.session_state.uploader_id}", use_container_width=True):
                                        st.session_state.haushaltsbuch_kategorien = [k for k in st.session_state.haushaltsbuch_kategorien if k["id"] != child["id"]]
                                        # Fix M5: Bereinige befristete und einmalige Ausgaben
                                        for ba in st.session_state.befristete_ausgaben:
                                            if ba.get("kategorie") == child["id"]:
                                                ba["kategorie"] = ""
                                        for ea in st.session_state.einmalige_ausgaben:
                                            if ea.get("kategorie") == child["id"]:
                                                ea["kategorie"] = ""
                                        c_key = f"c_{child['id']}"
                                        a_key = f"a_{child['id']}"
                                        if c_key in st.session_state:
                                            del st.session_state[c_key]
                                        if a_key in st.session_state:
                                            del st.session_state[a_key]
                                        st.session_state.global_rerun = True
                                        st.rerun()
                            
                            # Child Inputs: side-by-side
                            c_val, c_sl = st.columns([0.5, 0.5])
                            c_val.number_input(
                                "Betrag",
                                min_value=0.0,
                                key=f"c_{child['id']}",
                                label_visibility="collapsed",
                            )
                            c_sl.slider(
                                "RV%",
                                0,
                                200,
                                key=f"a_{child['id']}",
                                label_visibility="collapsed",
                            )
                    st.markdown("---")

            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                with st.popover("➕ Kategorie", use_container_width=True):
                    new_cat_name = st.text_input("Name", key="new_cat_name")
                    new_cat_betrag = st.number_input("Betrag (€/mtl.)", min_value=0.0, value=100.0, key="new_cat_betrag")
                    # Optional: choose parent on creation
                    group_options = ["— Hauptebene —"] + [g["name"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                    g_ids = [None] + [g["id"] for g in st.session_state.haushaltsbuch_kategorien if g.get("is_group")]
                    new_cat_parent_idx = st.selectbox("Gruppe", options=range(len(group_options)), format_func=lambda idx: group_options[idx], key="new_cat_parent")
                    new_cat_parent_id = g_ids[new_cat_parent_idx]
                    
                    if st.button("Hinzufügen", key="add_cat_confirm", use_container_width=True):
                        if new_cat_name.strip():
                            cleaned_name = new_cat_name.strip()
                            if any(k["name"].lower() == cleaned_name.lower() for k in st.session_state.haushaltsbuch_kategorien):
                                st.error("Name existiert bereits!")
                            else:
                                import time
                                new_id = f"kat_{int(time.time() * 1000)}"
                                st.session_state.haushaltsbuch_kategorien.append({
                                    "id": new_id,
                                    "name": cleaned_name,
                                    "parent_id": new_cat_parent_id,
                                    "is_group": False,
                                    "betrag": float(new_cat_betrag),
                                    "rv_pct": 100
                                })
                                # Set session state keys for the new category
                                st.session_state[f"c_{new_id}"] = float(new_cat_betrag)
                                st.session_state[f"a_{new_id}"] = 100
                                st.session_state.global_rerun = True
                                st.rerun()

            with col_btn2:
                with st.popover("📁 Sammel-Kat.", use_container_width=True):
                    new_group_name = st.text_input("Gruppenname", key="new_group_name")
                    if st.button("Hinzufügen", key="add_group_confirm", use_container_width=True):
                        if new_group_name.strip():
                            cleaned_name = new_group_name.strip()
                            if any(k["name"].lower() == cleaned_name.lower() for k in st.session_state.haushaltsbuch_kategorien):
                                st.error("Name existiert bereits!")
                            else:
                                import time
                                new_id = f"group_{int(time.time() * 1000)}"
                                st.session_state.haushaltsbuch_kategorien.append({
                                    "id": new_id,
                                    "name": cleaned_name,
                                    "parent_id": None,
                                    "is_group": True,
                                    "betrag": 0.0,
                                    "rv_pct": 100
                                })
                                st.session_state.global_rerun = True
                                st.rerun()

        # --- 6b. BEFRISTETE AUSGABEN ---
        if "befristete_ausgaben" not in st.session_state:
            st.session_state.befristete_ausgaben = []
        if "ba_edit_idx" not in st.session_state:
            st.session_state.ba_edit_idx = None
        if "ba_show_add" not in st.session_state:
            st.session_state.ba_show_add = False

        if "einmalige_ausgaben" not in st.session_state:
            st.session_state.einmalige_ausgaben = []
        if "ea_edit_idx" not in st.session_state:
            st.session_state.ea_edit_idx = None
        if "ea_show_add" not in st.session_state:
            st.session_state.ea_show_add = False

        with st.expander("⏱️ Befristete & Einmalige Ausgaben", expanded=False):
            st.caption("Zeitlich begrenzte Kosten und deine einmaligen Sonderausgaben (z.B. Weltreise, neues Dach)")

            if (
                not st.session_state.ba_show_add
                and st.session_state.ba_edit_idx is None
                and not st.session_state.ea_show_add
                and st.session_state.ea_edit_idx is None
            ):
                col_btn_ba, col_btn_ea = st.columns(2)
                if col_btn_ba.button("➕ Befristete Ausg.", use_container_width=True):
                    st.session_state.ba_show_add = True
                    st.session_state.global_rerun = True
                    st.rerun()
                if col_btn_ea.button("➕ Einmalausgabe", use_container_width=True):
                    st.session_state.ea_show_add = True
                    st.session_state.global_rerun = True
                    st.rerun()

            # Formular befristete Ausgabe
            if st.session_state.ba_show_add or st.session_state.ba_edit_idx is not None:
                is_edit = st.session_state.ba_edit_idx is not None
                curr = (
                    st.session_state.befristete_ausgaben[st.session_state.ba_edit_idx]
                    if is_edit
                    else {
                        "name": "Neue befristete Ausgabe",
                        "betrag_mtl": 500.0,
                        "start": aktuelles_jahr,
                        "ende": aktuelles_jahr + 10,
                        "kategorie": "",
                        "inflationsgebunden": False,
                    }
                )
                st.markdown("##### " + ("Befristete Ausgabe bearbeiten" if is_edit else "Befristete Ausgabe hinzufügen"))
                ba_name = st.text_input("Name deiner Ausgabe", value=curr["name"], key="ba_name")
                ba_betrag = st.number_input(
                    "Betrag (€/mtl.)",
                    value=float(curr["betrag_mtl"]),
                    min_value=0.0,
                    key="ba_betrag",
                )
                ba_c1, ba_c2 = st.columns(2)
                ba_start = ba_c1.number_input(
                    "Von Jahr", value=int(curr["start"]), min_value=2000, key="ba_start"
                )
                ba_ende = ba_c2.number_input(
                    "Bis Jahr",
                    value=int(curr["ende"]),
                    min_value=ba_start,
                    key="ba_ende",
                )

                # Kategorie: bestehende wählen ODER neue eingeben
                leaves = [kat for kat in st.session_state.haushaltsbuch_kategorien if not kat.get("is_group")]
                kat_optionen = [kat["name"] for kat in leaves] + ["Hauptebene", "— Neue Kategorie —"]
                kat_ids = [kat["id"] for kat in leaves] + ["", "— Neue Kategorie —"]
                
                curr_kat_id = curr.get("kategorie", "")
                if curr_kat_id in kat_ids:
                    kat_idx = kat_ids.index(curr_kat_id)
                else:
                    matching_ids = [kat["id"] for kat in leaves if kat["name"] == curr_kat_id]
                    if matching_ids:
                        kat_idx = kat_ids.index(matching_ids[0])
                    else:
                        kat_idx = len(kat_optionen) - 1  # "Neue Kategorie"

                ba_kat_sel = st.selectbox(
                    "Kategorie",
                    options=range(len(kat_optionen)),
                    format_func=lambda idx: kat_optionen[idx],
                    index=kat_idx,
                    key="ba_kat_sel"
                )
                selected_kat_id = kat_ids[ba_kat_sel]
                
                if selected_kat_id == "— Neue Kategorie —":
                    ba_kat = st.text_input(
                        "Neue Kategorie",
                        value=curr_kat_id if curr_kat_id not in kat_ids else "",
                        key="ba_kat_new",
                    )
                else:
                    ba_kat = selected_kat_id

                ba_infl = st.checkbox(
                    "Steigt mit Inflation",
                    value=curr.get("inflationsgebunden", False),
                    key="ba_infl",
                )

                bc1, bc2 = st.columns(2)
                if bc1.button("💾 Speichern", key="ba_save"):
                    if selected_kat_id == "— Neue Kategorie —":
                        typed_name = ba_kat.strip() if ba_kat else ba_name.strip()
                        existing = [k for k in st.session_state.haushaltsbuch_kategorien if k["name"].lower() == typed_name.lower()]
                        if existing:
                            final_kat_id = existing[0]["id"]
                        else:
                            # Create new leaf category
                            import time
                            new_id = f"kat_{int(time.time() * 1000)}"
                            st.session_state.haushaltsbuch_kategorien.append({
                                "id": new_id,
                                "name": typed_name,
                                "parent_id": None,
                                "is_group": False,
                                "betrag": 0.0,
                                "rv_pct": 100
                            })
                            st.session_state[f"c_{new_id}"] = 0.0
                            st.session_state[f"a_{new_id}"] = 100
                            final_kat_id = new_id
                    else:
                        final_kat_id = selected_kat_id

                    new_ba = {
                        "name": ba_name,
                        "betrag_mtl": ba_betrag,
                        "start": ba_start,
                        "ende": ba_ende,
                        "kategorie": final_kat_id,
                        "inflationsgebunden": ba_infl,
                    }
                    if is_edit:
                        st.session_state.befristete_ausgaben[
                            st.session_state.ba_edit_idx
                        ] = new_ba
                    else:
                        st.session_state.befristete_ausgaben.append(new_ba)
                    st.session_state.ba_edit_idx, st.session_state.ba_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                    st.rerun()
                if bc2.button("❌ Abbrechen", key="ba_cancel"):
                    st.session_state.ba_edit_idx, st.session_state.ba_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                    st.rerun()

            # Formular einmalige Ausgabe
            if st.session_state.ea_show_add or st.session_state.ea_edit_idx is not None:
                is_edit = st.session_state.ea_edit_idx is not None
                curr = (
                    st.session_state.einmalige_ausgaben[st.session_state.ea_edit_idx]
                    if is_edit
                    else {
                        "name": "Neue Einmalausgabe",
                        "betrag": 5000.0,
                        "jahr": aktuelles_jahr,
                        "monat": 1,
                        "kategorie": "",
                        "inflationsgebunden": True,
                    }
                )
                st.markdown("##### " + ("Einmalausgabe bearbeiten" if is_edit else "Einmalausgabe hinzufügen"))
                ea_name = st.text_input("Name deiner Einmalausgabe", value=curr["name"], key="ea_name")
                ea_betrag = st.number_input(
                    "Einmalbetrag (€)",
                    value=float(curr["betrag"]),
                    min_value=0.0,
                    key="ea_betrag",
                )
                ea_c1, ea_c2 = st.columns(2)
                ea_jahr = ea_c1.number_input(
                    "Jahr", value=int(curr["jahr"]), min_value=2000, key="ea_jahr"
                )
                monate_namen = [
                    "Januar", "Februar", "März", "April", "Mai", "Juni",
                    "Juli", "August", "September", "Oktober", "November", "Dezember"
                ]
                ea_monat = ea_c2.selectbox(
                    "Monat",
                    options=range(1, 13),
                    format_func=lambda m: monate_namen[m-1],
                    index=int(curr.get("monat", 1)) - 1,
                    key="ea_monat",
                )

                # Kategorie
                leaves = [kat for kat in st.session_state.haushaltsbuch_kategorien if not kat.get("is_group")]
                kat_optionen = [kat["name"] for kat in leaves] + ["Hauptebene", "— Neue Kategorie —"]
                kat_ids = [kat["id"] for kat in leaves] + ["", "— Neue Kategorie —"]
                
                curr_kat_id = curr.get("kategorie", "")
                if curr_kat_id in kat_ids:
                    kat_idx = kat_ids.index(curr_kat_id)
                else:
                    matching_ids = [kat["id"] for kat in leaves if kat["name"] == curr_kat_id]
                    if matching_ids:
                        kat_idx = kat_ids.index(matching_ids[0])
                    else:
                        kat_idx = len(kat_optionen) - 1  # "Neue Kategorie"

                ea_kat_sel = st.selectbox(
                    "Kategorie",
                    options=range(len(kat_optionen)),
                    format_func=lambda idx: kat_optionen[idx],
                    index=kat_idx,
                    key="ea_kat_sel"
                )
                selected_kat_id = kat_ids[ea_kat_sel]
                
                if selected_kat_id == "— Neue Kategorie —":
                    ea_kat = st.text_input(
                        "Neue Kategorie",
                        value=curr_kat_id if curr_kat_id not in kat_ids else "",
                        key="ea_kat_new",
                    )
                else:
                    ea_kat = selected_kat_id

                ea_infl = st.checkbox(
                    "Steigt mit Inflation",
                    value=curr.get("inflationsgebunden", True),
                    key="ea_infl",
                )

                eac1, eac2 = st.columns(2)
                if eac1.button("💾 Speichern", key="ea_save"):
                    if selected_kat_id == "— Neue Kategorie —":
                        typed_name = ea_kat.strip() if ea_kat else ea_name.strip()
                        existing = [k for k in st.session_state.haushaltsbuch_kategorien if k["name"].lower() == typed_name.lower()]
                        if existing:
                            final_kat_id = existing[0]["id"]
                        else:
                            import time
                            new_id = f"kat_{int(time.time() * 1000)}"
                            st.session_state.haushaltsbuch_kategorien.append({
                                "id": new_id,
                                "name": typed_name,
                                "parent_id": None,
                                "is_group": False,
                                "betrag": 0.0,
                                "rv_pct": 100
                            })
                            st.session_state[f"c_{new_id}"] = 0.0
                            st.session_state[f"a_{new_id}"] = 100
                            final_kat_id = new_id
                    else:
                        final_kat_id = selected_kat_id

                    new_ea = {
                        "name": ea_name,
                        "betrag": ea_betrag,
                        "jahr": ea_jahr,
                        "monat": ea_monat,
                        "kategorie": final_kat_id,
                        "inflationsgebunden": ea_infl,
                    }
                    if is_edit:
                        st.session_state.einmalige_ausgaben[
                            st.session_state.ea_edit_idx
                        ] = new_ea
                    else:
                        st.session_state.einmalige_ausgaben.append(new_ea)
                    st.session_state.ea_edit_idx, st.session_state.ea_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                    st.rerun()
                if eac2.button("❌ Abbrechen", key="ea_cancel"):
                    st.session_state.ea_edit_idx, st.session_state.ea_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                    st.rerun()

            # Auflistung befristete Ausgaben
            if st.session_state.befristete_ausgaben:
                st.markdown("**Befristete Ausgaben:**")
                for i, ba in enumerate(st.session_state.befristete_ausgaben):
                    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                    kat_id = ba.get("kategorie", "")
                    kat_display = id_to_name.get(kat_id, kat_id) if kat_id else "Hauptebene"
                    col1.write(
                        f"⏱️ **{ba['name']}** ({kat_display})\n{ba['betrag_mtl']:.0f}€/mtl. ({ba['start']} - {ba['ende']})"
                    )
                    if col2.button("✏️", key=f"ba_e_{i}"):
                        st.session_state.ba_edit_idx, st.session_state.ba_show_add = (
                            i,
                            False,
                        )
                        st.session_state.global_rerun = True
                        st.rerun()
                    if col3.button("🗑️", key=f"ba_d_{i}"):
                        st.session_state.befristete_ausgaben.pop(i)
                        st.session_state.global_rerun = True
                        st.rerun()

            # Auflistung einmalige Ausgaben
            if st.session_state.einmalige_ausgaben:
                st.markdown("**Einmalige Ausgaben:**")
                monate_namen = [
                    "Januar", "Februar", "März", "April", "Mai", "Juni",
                    "Juli", "August", "September", "Oktober", "November", "Dezember"
                ]
                for i, ea in enumerate(st.session_state.einmalige_ausgaben):
                    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                    kat_id = ea.get("kategorie", "")
                    kat_display = id_to_name.get(kat_id, kat_id) if kat_id else "Hauptebene"
                    monat_idx = int(ea.get("monat", 1))
                    monat_str = monate_namen[monat_idx - 1]
                    col1.write(
                        f"📅 **{ea['name']}** ({kat_display})\n{ea['betrag']:.0f}€ im {monat_str} {ea['jahr']}"
                    )
                    if col2.button("✏️", key=f"ea_e_{i}"):
                        st.session_state.ea_edit_idx, st.session_state.ea_show_add = (
                            i,
                            False,
                        )
                        st.session_state.global_rerun = True
                        st.rerun()
                    if col3.button("🗑️", key=f"ea_d_{i}"):
                        st.session_state.einmalige_ausgaben.pop(i)
                        st.session_state.global_rerun = True
                        st.rerun()

        # Dynamische Kategorien: aus befristeten Ausgaben und Einmalausgaben neue Kategorien sammeln
        alle_kategorien = list(ausgaben_kategorien)
        for ba in st.session_state.befristete_ausgaben:
            kat = ba.get("kategorie", ba["name"])
            if kat not in alle_kategorien:
                alle_kategorien.append(kat)

        # --- 7. ANNAHMEN (Inflation & Dynamik) ---
        with st.expander("⚙️ Annahmen (Dynamik)", expanded=False):
            st.markdown("**Inflations- & Steigerungsraten (% p.a.)**")
            infl_rate = st.slider(
                "Ausgaben (Inflation)",
                0.0,
                5.0,
                step=0.1,
                key="infl_rate_key",
                help="Jährliche Steigerung aller Ausgaben",
            )
            gehalts_dyn = st.slider(
                "Gehalt (Dynamik)",
                0.0,
                5.0,
                step=0.1,
                key="gehalts_dyn_key",
                help="Jährliche reale Steigerung des Bruttogehalts während der Aktivphase",
            )

            anp_options = {
                "0% (Pessimistisch)": 0.0,
                "1% (Moderat)": 1.0,
                "2% (Standard)": 2.0,
            }
            anp_label = st.selectbox(
                "Gesetzliche Rente (Anpassung)",
                list(anp_options.keys()),
                key="renten_anp_display_key",
                help="Jährliche Anpassung der GRV. Wird auch zur Projektion des Rentenwerts bis zum Start verwendet (DRV-Standard).",
            )
            renten_anp = anp_options[anp_label]
            st.session_state["renten_anp_key"] = renten_anp

            bav_anp = st.slider(
                "Betriebsrente (bAV)",
                0.0,
                3.0,
                step=0.1,
                key="bav_anp_key",
                help="Jährliche garantierte Anpassung der bAV",
            )

            st.divider()
            st.markdown("**💰 Intelligente Reinvestition (Spar-Loop)**")
            
            # Asset-Auswahl für Überschüsse
            asset_names = [a["name"] for a in st.session_state.get("assets", [])]
            reinvest_options = ["— Keine (nur Cash-Reserven) —"] + asset_names
            
            reinvest_target = st.selectbox(
                "Ziel-Asset für Überschüsse",
                reinvest_options,
                key="reinvest_target_key",
                help="Wähle ein Asset, in das jährliche Überschüsse automatisch reinvestiert werden sollen."
            )
            
            liq_reserve = st.number_input(
                "Liquiditäts-Reserve (€)",
                step=1000.0,
                key="liq_reserve_key",
                help="Betrag, der vorrangig in den Cash-Reserven gehalten wird (Notgroschen)."
            )
            
            liq_yield = st.slider(
                "Zins Cash-Reserve (% p.a.)",
                0.0, 3.0,
                step=0.1,
                key="liq_yield_key",
                help="Verzinsung für den Notgroschen (z.B. Tagesgeld)."
            )

        # --- 5. EINNAHMEQUELLEN ---
        with st.expander("💰 Einnahmequellen (Rente)", expanded=False):
            if "edit_idx" not in st.session_state:
                st.session_state.edit_idx = None
            if "show_add_form" not in st.session_state:
                st.session_state.show_add_form = False

            if not st.session_state.show_add_form and st.session_state.edit_idx is None:
                if st.button("➕ Neu"):
                    st.session_state.show_add_form = True
                    st.session_state.global_rerun = True

            if st.session_state.show_add_form or st.session_state.edit_idx is not None:
                is_edit = st.session_state.edit_idx is not None
                current_e = (
                    st.session_state.einnahmen[st.session_state.edit_idx]
                    if is_edit
                    else {
                        "name": "Neue Quelle",
                        "betrag": 500.0,
                        "typ": "Privat",
                        "start": rentenbeginn,
                        "ende": 2065,
                    }
                )
                st.markdown("##### " + ("Editieren" if is_edit else "Hinzufügen"))
                f_name = st.text_input("Name", value=current_e["name"])
                f_typ_options = [
                    "Gesetzlich",
                    "bAV",
                    "Privat",
                    "Kapital",
                    "bAV (Einmalzahlung)",
                    "Entnahmeplan (Vermögen)",
                    "Sonstiges",
                ]
                f_typ_index = (
                    f_typ_options.index(current_e["typ"])
                    if current_e.get("typ") in f_typ_options
                    else 0
                )
                f_typ = st.selectbox("Typ", f_typ_options, index=f_typ_index)

                if f_typ == "bAV (Einmalzahlung)":
                    f_betrag = st.number_input(
                        "Einmalbetrag (€ Brutto)",
                        value=float(current_e["betrag"]),
                        min_value=0.0,
                    )
                    f_start = st.number_input(
                        "Auszahlungsjahr",
                        value=int(current_e["start"]),
                        min_value=aktuelles_jahr,
                    )
                    f_ende = f_start
                elif f_typ == "Entnahmeplan (Vermögen)":
                    f_betrag = st.number_input(
                        "Entnahme (€/mtl. Netto)",
                        value=float(current_e["betrag"]),
                        min_value=0.0,
                    )
                    f_start = st.number_input(
                        "Von Jahr",
                        value=int(current_e["start"]),
                        min_value=aktuelles_jahr,
                    )
                    f_ende = st.number_input(
                        "Bis Jahr", value=int(current_e["ende"]), min_value=f_start
                    )
                elif f_typ == "Gesetzlich":
                    eingabe_modus_options = ["Euro-Betrag", "Entgeltpunkte (EP)"]
                    current_modus = current_e.get("eingabe_modus", "euro")
                    eingabe_modus_idx = 0 if current_modus == "euro" else 1

                    f_eingabe_modus_radio = st.radio(
                        "Eingabemodus",
                        eingabe_modus_options,
                        index=eingabe_modus_idx,
                        horizontal=True,
                    )

                    if f_eingabe_modus_radio == "Entgeltpunkte (EP)":
                        f_eingabe_modus = "punkte"
                        f_punkte = st.number_input(
                            "Anzahl Entgeltpunkte (lt. Renteninformation)",
                            value=float(current_e.get("punkte", 40.0)),
                            min_value=0.0,
                            step=0.1,
                        )
                        from config import RENTENWERT_AKTUELL

                        f_betrag = f_punkte * RENTENWERT_AKTUELL
                        st.info(
                            f"Basiswert: **{f_betrag:.2f} €/mtl.** (bei aktuellem Rentenwert, vor Abschlägen)"
                        )
                    else:
                        f_eingabe_modus = "euro"
                        f_punkte = 0.0
                        f_betrag = st.number_input(
                            "Betrag (€/mtl., heutige Anwartschaft lt. Renteninfo)",
                            value=float(current_e["betrag"]),
                            min_value=0.0,
                            help="Nimm hier den Wert 'Bisher erreichte Rentenanwartschaft'. Der Rente-O-Mat berechnet die Hochrechnung mit der gewählten Rate (0, 1, 2%) dann automatisch.",
                        )

                    f_start = st.number_input(
                        "Von Jahr",
                        value=int(current_e["start"]),
                        min_value=aktuelles_jahr,
                    )
                    f_ende = st.number_input(
                        "Bis Jahr", value=int(current_e["ende"]), min_value=f_start
                    )
                else:
                    f_betrag = st.number_input(
                        "Betrag (€/mtl.)",
                        value=float(current_e["betrag"]),
                        min_value=0.0,
                    )
                    f_start = st.number_input(
                        "Von Jahr",
                        value=int(current_e["start"]),
                        min_value=aktuelles_jahr,
                    )
                    f_ende = st.number_input(
                        "Bis Jahr", value=int(current_e["ende"]), min_value=f_start
                    )
                c1, c2 = st.columns(2)
                if c1.button("💾 Speichern"):
                    new_data = {
                        "name": f_name,
                        "betrag": f_betrag,
                        "typ": f_typ,
                        "start": f_start,
                        "ende": f_ende,
                    }
                    if f_typ == "Gesetzlich":
                        new_data["eingabe_modus"] = f_eingabe_modus
                        new_data["punkte"] = f_punkte
                    if is_edit:
                        st.session_state.einnahmen[st.session_state.edit_idx] = new_data
                    else:
                        st.session_state.einnahmen.append(new_data)
                    st.session_state.edit_idx, st.session_state.show_add_form = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                if c2.button("❌ Abbrechen"):
                    st.session_state.edit_idx, st.session_state.show_add_form = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True

            for i, e in enumerate(st.session_state.einnahmen):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                col1.write(f"**{e['name']}**\n{e['betrag']}€")
                if col2.button("✏️", key=f"e_{i}"):
                    st.session_state.edit_idx, st.session_state.show_add_form = i, False
                    st.session_state.global_rerun = True
                if col3.button("🗑️", key=f"d_{i}"):
                    st.session_state.einnahmen.pop(i)
                    st.session_state.global_rerun = True

        # --- 5b. VERMÖGENSWERTE ---
        if "assets" not in st.session_state:
            st.session_state.assets = []
        if "asset_edit_idx" not in st.session_state:
            st.session_state.asset_edit_idx = None
        if "asset_show_add" not in st.session_state:
            st.session_state.asset_show_add = False

        with st.expander("💎 Vermögenswerte", expanded=False):
            st.caption(
                "Erfasse hier deine Depots und Konten. Diese ersetzen das bisherige globale Startvermögen für eine präzisere Simulation."
            )

            if (
                not st.session_state.asset_show_add
                and st.session_state.asset_edit_idx is None
            ):
                if st.button("➕ Neues Asset"):
                    st.session_state.asset_show_add = True
                    st.session_state.global_rerun = True

            if (
                st.session_state.asset_show_add
                or st.session_state.asset_edit_idx is not None
            ):
                is_edit = st.session_state.asset_edit_idx is not None
                curr = (
                    st.session_state.assets[st.session_state.asset_edit_idx]
                    if is_edit
                    else {
                        "name": "Welt-ETF",
                        "startwert": 10000.0,
                        "rendite_pa": 5.0,
                        "steuertyp": "abgeltung",
                        "teilfreistellung_pct": 30.0,
                        "entnahme_aktiv": False,
                        "entnahme_betrag_mtl": 500.0,
                        "entnahme_start": aktuelles_jahr,
                        "entnahme_ende": aktuelles_jahr + 20,
                    }
                )
                st.markdown("##### " + ("Editieren" if is_edit else "Hinzufügen"))
                a_name = st.text_input("Name", value=curr["name"], key="a_name")
                a_start = st.number_input(
                    "Startwert (€)",
                    value=float(curr["startwert"]),
                    min_value=0.0,
                    key="a_start",
                )
                a_rendite = st.slider(
                    "Rendite (% p.a.)",
                    0.0,
                    10.0,
                    float(curr["rendite_pa"]),
                    0.1,
                    key="a_rendite",
                )

                a_steuertyp_options = {
                    "Abgeltungsteuer": "abgeltung",
                    "Teilfreistellung (ETF)": "teilfreistellung",
                    "Steuerfrei": "steuerfrei",
                }
                a_steuertyp_display = st.selectbox(
                    "Besteuerung",
                    list(a_steuertyp_options.keys()),
                    index=list(a_steuertyp_options.values()).index(curr["steuertyp"]),
                    key="a_steuer",
                )
                a_steuertyp = a_steuertyp_options[a_steuertyp_display]

                a_tfs = 0.0
                if a_steuertyp == "teilfreistellung":
                    a_tfs = st.number_input(
                        "Teilfreistellung (%)",
                        value=float(curr.get("teilfreistellung_pct", 30.0)),
                        min_value=0.0,
                        max_value=100.0,
                        key="a_tfs",
                    )

                st.divider()
                a_ent_aktiv = st.checkbox(
                    "Manueller Entnahmeplan",
                    value=curr.get("entnahme_aktiv", False),
                    key="a_ent_aktiv",
                )
                if a_ent_aktiv:
                    a_ent_mode = st.selectbox(
                        "Entnahme-Modus",
                        ["Fester Betrag", "Kapitalverzehr (bis Ende)"],
                        index=0 if curr.get("entnahme_modus") == "fix" else 1,
                        key="a_ent_mode",
                    )
                    a_ent_modus_val = (
                        "fix" if a_ent_mode == "Fester Betrag" else "verzehr"
                    )

                    if a_ent_modus_val == "fix":
                        a_ent_betrag = st.number_input(
                            "Entnahme (€/mtl. Netto)",
                            value=float(curr.get("entnahme_betrag_mtl", 500.0)),
                            min_value=0.0,
                            key="a_ent_betrag",
                        )
                    else:
                        st.info(
                            "💡 Der Betrag wird automatisch berechnet, damit das Kapital am Ende auf 0€ sinkt."
                        )
                        a_ent_betrag = 0.0

                    a_ent_c1, a_ent_c2 = st.columns(2)
                    a_ent_start = a_ent_c1.number_input(
                        "Von Jahr",
                        value=max(
                            2000, int(curr.get("entnahme_start", aktuelles_jahr))
                        ),
                        min_value=2000,
                        key="a_ent_start",
                    )
                    a_ent_ende = a_ent_c2.number_input(
                        "Bis Jahr (Ende)",
                        value=max(
                            a_ent_start,
                            int(curr.get("entnahme_ende", a_ent_start + 10)),
                        ),
                        min_value=a_ent_start,
                        key="a_ent_ende",
                    )
                else:
                    a_ent_betrag, a_ent_start, a_ent_ende, a_ent_modus_val = (
                        0.0,
                        aktuelles_jahr,
                        aktuelles_jahr + 10,
                        "fix",
                    )
                    if st.session_state.get("entnahme_strategie_key", "Manuell (Keine Automatik)") != "Manuell (Keine Automatik)":
                        st.markdown("##### ⚙️ Entnahme durch Automatik")
                        stats = get_auto_entnahme_stats(curr["name"])
                        if stats:
                            auto_start = str(stats["start"])
                            auto_ende = str(stats["ende"])
                            auto_betrag = f"{stats['betrag']:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                        else:
                            auto_start = "—"
                            auto_ende = "—"
                            auto_betrag = "0,00 €"
                        
                        st.text_input("durchschnittlicher Betrag (€/mtl.)", value=auto_betrag, disabled=True, key=f"auto_betrag_{curr['name']}")
                        ac_col1, ac_col2 = st.columns(2)
                        ac_col1.text_input("Start-Jahr", value=auto_start, disabled=True, key=f"auto_start_{curr['name']}")
                        ac_col2.text_input("End-Jahr", value=auto_ende, disabled=True, key=f"auto_ende_{curr['name']}")

                ac1, ac2 = st.columns(2)
                if ac1.button("💾 Speichern", key="a_save"):
                    new_asset = {
                        "name": a_name,
                        "startwert": a_start,
                        "rendite_pa": a_rendite,
                        "steuertyp": a_steuertyp,
                        "teilfreistellung_pct": a_tfs,
                        "entnahme_aktiv": a_ent_aktiv,
                        "entnahme_betrag_mtl": a_ent_betrag,
                        "entnahme_start": a_ent_start,
                        "entnahme_ende": a_ent_ende,
                        "entnahme_modus": a_ent_modus_val,
                    }
                    if is_edit:
                        st.session_state.assets[st.session_state.asset_edit_idx] = (
                            new_asset
                        )
                    else:
                        st.session_state.assets.append(new_asset)
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True
                if ac2.button("❌ Abbrechen", key="a_cancel"):
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = (
                        None,
                        False,
                    )
                    st.session_state.global_rerun = True

            for i, asset in enumerate(st.session_state.assets):
                col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
                if asset.get("entnahme_aktiv"):
                    if asset.get("entnahme_modus") == "verzehr":
                        ent_str = " | Entnahme: Berechnet"
                    else:
                        ent_str = f" | Entnahme: {asset['entnahme_betrag_mtl']:.0f}€"
                elif st.session_state.get("entnahme_strategie_key", "Manuell (Keine Automatik)") != "Manuell (Keine Automatik)":
                    ent_str = " | Entnahme: Automatik"
                else:
                    ent_str = ""
                col1.write(f"**{asset['name']}**\n{asset['startwert']:,.0f}€{ent_str}")
                if col2.button("✏️", key=f"a_e_{i}"):
                    st.session_state.asset_edit_idx, st.session_state.asset_show_add = (
                        i,
                        False,
                    )
                    st.session_state.global_rerun = True
                if col3.button("🗑️", key=f"a_d_{i}"):
                    st.session_state.assets.pop(i)
                    st.session_state.global_rerun = True

        # --- 5c. ENTNAHMESTRATEGIE ---
        with st.expander("🎯 Entnahmestrategie (Automatik)", expanded=False):
            st.caption("Legt fest, wie verbleibende Deckungslücken automatisch aus deinen Vermögenswerten geschlossen werden (nachdem manuelle Pläne ausgeführt wurden).")

            strategie_options = [
                "Manuell (Keine Automatik)",
                "Bedarfsgesteuert: Wasserfall (Priorisiert)",
                "Bedarfsgesteuert: Pro Rata (Gleichmäßig)",
                "Bedarfsgesteuert: Steuergünstig (Steuerfreie zuerst)",
                "Regelbasiert: Fixer Prozentsatz (z.B. 4%-Regel)",
                "Substanzerhalt (Nur Rendite entnehmen)",
                "Zielverzehr (Null-Landung bis Alter X)"
            ]
            
            # Harmonisierung der Entnahmestrategie-Keys bei eventuellen Resten oder alten Profilen
            current_strat = st.session_state.get("entnahme_strategie_key", "Manuell (Keine Automatik)")
            if current_strat:
                s = str(current_strat).strip().lower()
                if "manuell" in s or "keine" in s:
                    current_strat = "Manuell (Keine Automatik)"
                elif "wasserfall" in s:
                    current_strat = "Bedarfsgesteuert: Wasserfall (Priorisiert)"
                elif "pro rata" in s or "prorata" in s or "gleichmäßig" in s:
                    current_strat = "Bedarfsgesteuert: Pro Rata (Gleichmäßig)"
                elif "steueroptimiert" in s or "smart" in s or "steuergünstig" in s or "steuerguenstig" in s:
                    current_strat = "Bedarfsgesteuert: Steuergünstig (Steuerfreie zuerst)"
                elif "prozentsatz" in s or "regelbasiert" in s or "4%" in s:
                    current_strat = "Regelbasiert: Fixer Prozentsatz (z.B. 4%-Regel)"
                elif "substanzerhalt" in s or "rendite" in s:
                    current_strat = "Substanzerhalt (Nur Rendite entnehmen)"
                elif "zielverzehr" in s or "null-landung" in s or "nulllandung" in s:
                    current_strat = "Zielverzehr (Null-Landung bis Alter X)"
                else:
                    current_strat = "Manuell (Keine Automatik)"
            else:
                current_strat = "Manuell (Keine Automatik)"
            
            strat_idx = strategie_options.index(current_strat) if current_strat in strategie_options else 0
            
            selected_strat = st.selectbox(
                "Globale Strategie",
                strategie_options,
                index=strat_idx,
                key="entnahme_strategie_key"
            )

            if selected_strat != "Manuell (Keine Automatik)":
                st.markdown("##### ⏱️ Start der Automatik")
                start_modus_options = [
                    "Sofort (ab aktuellem Jahr)",
                    "Ab Rentenbeginn",
                    "Individuell (Jahr/Monat)"
                ]
                if st.session_state.get("atz_sim_input"):
                    start_modus_options.insert(2, "Ab ATZ-Beginn")
                    
                current_start_modus = st.session_state.get("entnahme_start_modus", "Sofort (ab aktuellem Jahr)")
                if current_start_modus not in start_modus_options:
                    current_start_modus = "Sofort (ab aktuellem Jahr)"
                start_idx = start_modus_options.index(current_start_modus)
                
                start_modus = st.selectbox(
                    "Wann soll die automatische Entnahme frühestens greifen?",
                    start_modus_options,
                    index=start_idx,
                    key="entnahme_start_modus"
                )
                
                if start_modus == "Individuell (Jahr/Monat)":
                    col1, col2 = st.columns(2)
                    col1.number_input("Start-Jahr", min_value=aktuelles_jahr, max_value=2100, value=int(st.session_state.get("entnahme_start_jahr", aktuelles_jahr)), step=1, key="entnahme_start_jahr")
                    col2.number_input("Start-Monat", min_value=1, max_value=12, value=int(st.session_state.get("entnahme_start_monat", 1)), step=1, key="entnahme_start_monat")

            # Exkludiere Assets mit aktivem manuellen Entnahmeplan von der Automatik
            available_assets = [a for a in st.session_state.assets if not a.get("entnahme_aktiv")]
            
            # Zeige einen Hinweis, wenn Assets durch manuelle Entnahmen gesperrt sind
            if len(available_assets) < len(st.session_state.assets):
                st.info("ℹ️ **Hinweis:** Assets mit aktivem manuellen Entnahmeplan sind für die Automatik gesperrt.")

            if selected_strat == "Bedarfsgesteuert: Wasserfall (Priorisiert)":
                st.write("**Entnahme-Reihenfolge (Wasserfall)**")
                asset_names = [a["name"] for a in available_assets]
                current_order = st.session_state.get("entnahme_wasserfall_reihenfolge", [])
                
                # Nur noch existierende Assets behalten
                current_order = [n for n in current_order if n in asset_names]
                # Neue Assets am Ende anfügen
                for n in asset_names:
                    if n not in current_order:
                        current_order.append(n)
                
                selected_order = st.multiselect(
                    "Reihenfolge festlegen (zuerst gewählt = zuerst geleert)",
                    options=asset_names,
                    default=current_order,
                    key="entnahme_wasserfall_reihenfolge"
                )
            elif selected_strat == "Regelbasiert: Fixer Prozentsatz (z.B. 4%-Regel)":
                st.number_input("Jährliche Entnahme (%)", min_value=0.0, max_value=100.0, value=float(st.session_state.get("entnahme_fix_pct", 4.0)), step=0.1, key="entnahme_fix_pct")
            elif selected_strat == "Zielverzehr (Null-Landung bis Alter X)":
                st.number_input("Ziel-Alter", min_value=60, max_value=120, value=int(st.session_state.get("entnahme_ziel_alter", 95)), step=1, key="entnahme_ziel_alter")
            
            with st.popover("❓ Wie funktioniert die Automatik?"):
                st.markdown("""
                **Teilautomatik (Manuell + Automatik)**
                1. Die Engine verrechnet Einnahmen, Ausgaben und Steuern.
                2. Sie führt alle **manuellen Entnahmepläne** aus (die du in den einzelnen Vermögenswerten explizit aktiviert hast).
                3. Entsteht danach immer noch eine **Deckungslücke (Defizit)**, springt diese **Automatik** an und zieht das fehlende Geld gemäß der hier gewählten globalen Strategie aus den verbleibenden Assets ab.
                
                ⚠️ **Wichtig:** Assets mit einem aktiven manuellen Entnahmeplan sind für die automatische Entnahme gesperrt, um doppelte Entnahmen oder Konflikte zu vermeiden.
                
                *Das gibt dir maximale Kontrolle (z.B. "Ich will Depot A bis 2035 fix verzehren") und gleichzeitig den Komfort, dass die Engine Lücken automatisch schließt.*
                """)




        ausgaben_input = {
            kat["id"]: kat["betrag"]
            for kat in st.session_state.haushaltsbuch_kategorien
            if not kat.get("is_group")
        }
        anpassungsfaktor_input = {
            kat["id"]: kat["rv_pct"]
            for kat in st.session_state.haushaltsbuch_kategorien
            if not kat.get("is_group")
        }

        return {
            "nutzer_name": nutzer_name,
            "geburtsjahr": geburtsjahr,
            "geburtsmonat": geburtsmonat,
            "rentenbeginn": rentenbeginn,
            "atz_simulieren": atz_simulieren,
            "atz_dauer": atz_dauer if atz_simulieren else 0,
            "atz_start": atz_start,
            "atz_ende": rentenbeginn,
            "atz_aufstockung_pct": atz_aufst,
            "aktuelles_brutto": aktuelles_brutto,
            "aktuelles_netto": aktuelles_netto,
            "ausgaben_input": ausgaben_input,
            "anpassungsfaktor_input": anpassungsfaktor_input,
            "einnahmen": st.session_state.einnahmen,
            "show_values": show_values,
            "ausgaben_kategorien": alle_kategorien,
            "aktuelles_jahr": aktuelles_jahr,
            "kinderzahl": kinderzahl,
            "kirchensteuer_satz": kirchensteuer_satz,
            "inflation_rate": infl_rate,
            "rentenanpassung_rate": renten_anp,
            "bav_anpassung_rate": bav_anp,
            "gehalts_dynamik": gehalts_dyn,
            "reinvest_target": reinvest_target,
            "liquidity_reserve": liq_reserve,
            "liquidity_yield": liq_yield,
            "befristete_ausgaben": st.session_state.befristete_ausgaben,
            "einmalige_ausgaben": st.session_state.einmalige_ausgaben,
            "assets": st.session_state.assets,
            "haushaltsbuch_kategorien": st.session_state.haushaltsbuch_kategorien,
            # NEUE AUTOMATISCHE STRATEGIE-KEYS
            "entnahme_strategie": st.session_state.get("entnahme_strategie_key", "Manuell (Keine Automatik)"),
            "entnahme_wasserfall_reihenfolge": st.session_state.get("entnahme_wasserfall_reihenfolge", []),
            "entnahme_fix_pct": st.session_state.get("entnahme_fix_pct", 4.0),
            "entnahme_ziel_alter": st.session_state.get("entnahme_ziel_alter", 95),
            "entnahme_start_modus": st.session_state.get("entnahme_start_modus", "Sofort (ab aktuellem Jahr)"),
            "entnahme_start_jahr": st.session_state.get("entnahme_start_jahr", aktuelles_jahr),
            "entnahme_start_monat": st.session_state.get("entnahme_start_monat", 1),
        }
