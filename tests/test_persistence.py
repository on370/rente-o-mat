import sys
from unittest.mock import MagicMock

# Mock streamlit before importing persistence
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

import io
import json
import pytest
from data.persistence import import_settings

def test_import_settings_clears_old_category_widgets():
    # Setup mock session state
    session_state = MagicMock()
    mock_st.session_state = session_state
    
    # Define old categories that exist in session_state
    session_state.haushaltsbuch_kategorien = [
        {"id": "Wohnen", "name": "Wohnen", "parent_id": None, "is_group": False}
    ]
    
    # Simulate keys present in session_state dict-like access
    session_state.__contains__.side_effect = lambda k: k in [
        "c_Wohnen", "a_Wohnen", "p_sel_Wohnen", "ren_Wohnen", "tg_Wohnen", "collapsed_Wohnen",
        "haushaltsbuch_kategorien"
    ]
    
    deleted_keys = []
    def delitem(key):
        deleted_keys.append(key)
    session_state.__delitem__.side_effect = delitem

    # Prepare JSON import data
    import_data = {
        "version": "2.0",
        "data": {
            "haushaltsbuch_kategorien": [
                {"id": "Wohnen", "name": "Miete", "parent_id": "group_1", "is_group": False, "betrag": 96.0, "rv_pct": 100},
                {"id": "group_1", "name": "Wohnen", "parent_id": None, "is_group": True, "betrag": 0.0, "rv_pct": 100}
            ]
        }
    }
    json_file = io.StringIO(json.dumps(import_data))
    
    # Run import
    success = import_settings(json_file)
    assert success
    
    # Verify that the old widget keys were deleted from session_state
    assert "p_sel_Wohnen" in deleted_keys
    assert "ren_Wohnen" in deleted_keys
    assert "c_Wohnen" in deleted_keys
    assert "a_Wohnen" in deleted_keys


def test_import_settings_loads_entnahme_start():
    # Setup mock session state
    state = {}
    session_state = MagicMock()
    session_state.__setitem__.side_effect = state.__setitem__
    session_state.__getitem__.side_effect = state.__getitem__
    session_state.__contains__.side_effect = state.__contains__
    mock_st.session_state = session_state
    
    # Prepare JSON import data
    import_data = {
        "version": "2.0",
        "data": {
            "entnahme_start_modus": "Ab Rentenbeginn",
            "entnahme_start_jahr": 2045,
            "entnahme_start_monat": 6
        }
    }
    json_file = io.StringIO(json.dumps(import_data))
    
    # Run import
    success = import_settings(json_file)
    assert success
    
    # Verify that the keys were written to session_state
    assert state.get("entnahme_start_modus") == "Ab Rentenbeginn"
    assert state.get("entnahme_start_jahr") == 2045
    assert state.get("entnahme_start_monat") == 6


