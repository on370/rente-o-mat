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
            
            # 1. Einnahmen-Liste (Spezialfall)
            if "einnahmen" in data:
                st.session_state.einnahmen = data["einnahmen"]
            
            # 2. Mapping von JSON-Keys auf Session State Keys
            mapping = {
                "nutzer_name": "nutzer_name_key",
                "geburtsjahr": "geburtsjahr_key",
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

            return True
        except Exception as e:
            st.error(f"Fehler beim Import: {e}")
    return False
