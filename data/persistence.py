import json
import streamlit as st

def export_settings(params):
    """Exportiert alle Parameter als JSON-String. Enthält eine Versionsnummer zur Abwärtskompatibilität."""
    # Metadaten hinzufügen
    export_data = {
        "version": "2.0",
        "data": params
    }
    return json.dumps(export_data, indent=4, ensure_ascii=False)

def import_settings(json_file):
    """Importiert Einstellungen aus einer hochgeladenen Datei in den Session State. Behandelt v1 und v2 JSONs."""
    if json_file is not None:
        try:
            raw_data = json.load(json_file)
            
            # Versionscheck
            is_v2 = "version" in raw_data and raw_data["version"] >= "2.0"
            data = raw_data["data"] if is_v2 else raw_data
            
            # Vor dem Import: Bereinigen aller alten Kategorie-Widget-Zustände aus dem Session State,
            # um zu verhindern, dass Streamlit veraltete Widget-Werte (wie p_sel_ oder ren_)
            # für die neu geladenen Kategorien beibehält.
            if "haushaltsbuch_kategorien" in st.session_state:
                for kat in st.session_state.haushaltsbuch_kategorien:
                    kid = kat.get("id")
                    if kid:
                        for prefix in ["c_", "a_", "p_sel_", "ren_", "tg_", "collapsed_"]:
                            k = f"{prefix}{kid}"
                            if k in st.session_state:
                                del st.session_state[k]
            
            # 1. Einnahmen-Liste (Spezialfall)
            if "einnahmen" in data:
                st.session_state.einnahmen = data["einnahmen"]
            
            # 2. Mapping von JSON-Keys auf Session State Keys
            mapping = {
                "nutzer_name": "nutzer_name_key",
                "geburtsjahr": "geburtsjahr_key",
                "geburtsmonat": "geburtsmonat_key",
                "rentenbeginn": "rentenbeginn_input",
                "atz_simulieren": "atz_sim_input",
                "atz_dauer": "atz_dauer_input",
                "atz_aufstockung_pct": "atz_aufst_key",
                "aktuelles_brutto": "brutto_key",
                "aktuelles_netto": "netto_key",
                "show_values": "show_vals_key",
                "kinderzahl": "kinderzahl_key",
                "kirchensteuer_satz": "kist_key",
                "inflation_rate": "infl_rate_key",
                "rentenanpassung_rate": "renten_anp_key",
                "bav_anpassung_rate": "bav_anp_key",
                "startvermoegen": "startvermoegen_key",
                "kapitalrendite": "rendite_key"
            }
            
            for json_key, ss_key in mapping.items():
                if json_key in data:
                    st.session_state[ss_key] = data[json_key]
            
            # Spezialfall: Rentenbeginn (Dezimaljahr) in Jahr und Monat aufteilen
            if "rentenbeginn" in data:
                rb = data["rentenbeginn"]
                rb_jahr = int(rb)
                rb_monat = int(round((rb - rb_jahr) * 12)) + 1
                if rb_monat > 12:
                    rb_jahr += 1
                    rb_monat -= 12
                st.session_state["rentenbeginn_jahr_input"] = rb_jahr
                st.session_state["rentenbeginn_monat_input"] = rb_monat
                st.session_state["prev_rentenbeginn"] = rb
                
            # Spezialfall: prev_geburtsjahr setzen, um automatisches Zurücksetzen zu verhindern
            if "geburtsjahr" in data:
                st.session_state["prev_geburtsjahr"] = data["geburtsjahr"]
            if "geburtsmonat" in data:
                st.session_state["prev_geburtsmonat"] = data["geburtsmonat"]
            
            # 3. Haushaltsbuch-Einträge
            if "haushaltsbuch_kategorien" in data:
                st.session_state.haushaltsbuch_kategorien = data["haushaltsbuch_kategorien"]
                for kat in st.session_state.haushaltsbuch_kategorien:
                    if not kat.get("is_group"):
                        st.session_state[f"c_{kat['id']}"] = float(kat.get("betrag", 0.0))
                        st.session_state[f"a_{kat['id']}"] = int(kat.get("rv_pct", 100))
            else:
                # Alt-Format Migration (v1)
                st.session_state.haushaltsbuch_kategorien = []
                if "ausgaben_input" in data:
                    for kat, val in data["ausgaben_input"].items():
                        st.session_state[f"c_{kat}"] = float(val)
                        
                        rv = 100
                        if "anpassungsfaktor_input" in data and kat in data["anpassungsfaktor_input"]:
                            rv = int(data["anpassungsfaktor_input"][kat])
                        st.session_state[f"a_{kat}"] = rv
                        
                        st.session_state.haushaltsbuch_kategorien.append({
                            "id": kat,
                            "name": kat,
                            "parent_id": None,
                            "is_group": False,
                            "betrag": float(val),
                            "rv_pct": int(rv)
                        })

            # 4. Befristete Ausgaben & Assets
            if "befristete_ausgaben" in data:
                st.session_state.befristete_ausgaben = data["befristete_ausgaben"]
            if "assets" in data:
                st.session_state.assets = data["assets"]
            if "einmalige_ausgaben" in data:
                st.session_state.einmalige_ausgaben = data["einmalige_ausgaben"]
            else:
                st.session_state.einmalige_ausgaben = []

            # --- 5. ROBUSTE VALIDIERUNG & BEREINIGUNG DER KATEGORIEN ---
            if hasattr(st.session_state, "haushaltsbuch_kategorien") and st.session_state.haushaltsbuch_kategorien:
                kats = st.session_state.haushaltsbuch_kategorien
                
                # Eindeutige IDs sichern und Duplikate auflösen
                seen_ids = set()
                import time
                for i, kat in enumerate(kats):
                    kid = kat.get("id")
                    if not kid or kid in seen_ids:
                        new_id = f"kat_{int(time.time() * 1000) + i}"
                        kat["id"] = new_id
                    seen_ids.add(kat["id"])
                
                # Gruppe IDs sammeln
                group_ids = {g["id"] for g in kats if g.get("is_group")}
                
                # Zirkelbezüge und ungültige Parents bereinigen
                for kat in kats:
                    kid = kat.get("id")
                    pid = kat.get("parent_id")
                    
                    # Fall 1: Parent zeigt auf sich selbst (Zirkelbezug)
                    if pid == kid:
                        kat["parent_id"] = None
                        pid = None
                        
                    # Fall 2: Parent existiert nicht oder ist keine Gruppe
                    if pid and pid not in group_ids:
                        kat["parent_id"] = None
                        pid = None
                        
                    # Fall 3: Gruppen dürfen selbst kein parent_id haben
                    if kat.get("is_group") and pid:
                        kat["parent_id"] = None
                        
                # Konsistenz im Session State erzwingen
                for kat in kats:
                    if not kat.get("is_group"):
                        c_key = f"c_{kat['id']}"
                        a_key = f"a_{kat['id']}"
                        
                        # Wert-Typisierung absichern
                        try:
                            val = float(kat.get("betrag", 100.0))
                        except (ValueError, TypeError):
                            val = 100.0
                            
                        try:
                            rv = int(kat.get("rv_pct", 100))
                        except (ValueError, TypeError):
                            rv = 100
                            
                        kat["betrag"] = val
                        kat["rv_pct"] = rv
                        
                        st.session_state[c_key] = val
                        st.session_state[a_key] = rv

                # --- 6. HARMONISIERUNG DER KATEGORIE-VERKNÜPFUNGEN ---
                # Wir stellen sicher, dass befristete und einmalige Ausgaben immer die ID (nicht den Namen) der Kategorie referenzieren!
                name_to_id = {}
                id_to_id = set()
                for kat in kats:
                    if not kat.get("is_group"):
                        name_to_id[kat["name"].lower()] = kat["id"]
                        name_to_id[kat["id"].lower()] = kat["id"] # Fallback: Falls die ID selbst gesucht wird
                        id_to_id.add(kat["id"])
                
                # Befristete Ausgaben harmonisieren
                if hasattr(st.session_state, "befristete_ausgaben") and st.session_state.befristete_ausgaben:
                    for ba in st.session_state.befristete_ausgaben:
                        curr_kat = ba.get("kategorie", "")
                        if curr_kat:
                            if curr_kat in id_to_id:
                                continue
                            elif curr_kat.lower() in name_to_id:
                                ba["kategorie"] = name_to_id[curr_kat.lower()]
                            else:
                                ba["kategorie"] = ""
                                
                # Einmalige Ausgaben harmonisieren
                if hasattr(st.session_state, "einmalige_ausgaben") and st.session_state.einmalige_ausgaben:
                    for ea in st.session_state.einmalige_ausgaben:
                        curr_kat = ea.get("kategorie", "")
                        if curr_kat:
                            if curr_kat in id_to_id:
                                continue
                            elif curr_kat.lower() in name_to_id:
                                ea["kategorie"] = name_to_id[curr_kat.lower()]
                            else:
                                ea["kategorie"] = ""

            return True
        except Exception as e:
            st.error(f"Fehler beim Import: {e}")
    return False
