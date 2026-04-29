import json
import streamlit as st

def export_settings(params):
    """Exportiert alle Parameter als JSON-String."""
    return json.dumps(params, indent=4, ensure_ascii=False)

def import_settings(json_file):
    """Importiert Einstellungen aus einer hochgeladenen Datei in den Session State."""
    if json_file is not None:
        try:
            data = json.load(json_file)
            
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
                "show_values": "show_vals_key"
            }
            
            for json_key, ss_key in mapping.items():
                if json_key in data:
                    st.session_state[ss_key] = data[json_key]
            
            # 3. Haushaltsbuch-Einträge
            if "ausgaben_input" in data:
                for kat, val in data["ausgaben_input"].items():
                    st.session_state[f"c_{kat}"] = val
            if "anpassungsfaktor_input" in data:
                for kat, val in data["anpassungsfaktor_input"].items():
                    st.session_state[f"a_{kat}"] = val

            return True
        except Exception as e:
            st.error(f"Fehler beim Import: {e}")
    return False
