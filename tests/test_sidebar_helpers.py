import sys
from unittest.mock import MagicMock

# Mock streamlit before importing get_auto_entnahme_stats
mock_st = MagicMock()
sys.modules['streamlit'] = mock_st

import pandas as pd
import pytest
from ui.sidebar import get_auto_entnahme_stats

def test_get_auto_entnahme_stats():
    # Setup mock session state
    session_state = MagicMock()
    mock_st.session_state = session_state
    
    # When df_timeline is None, should return None
    session_state.get.return_value = None
    assert get_auto_entnahme_stats("Depot A") is None
    
    # Create a mock df_timeline DataFrame
    df = pd.DataFrame([
        {"Jahr": 2026, "Entnahme: Depot A": 500.0, "Entnahme: Depot B": 0.0},
        {"Jahr": 2027, "Entnahme: Depot A": 600.0, "Entnahme: Depot B": 0.0},
        {"Jahr": 2028, "Entnahme: Depot A": 0.0, "Entnahme: Depot B": 1000.0},
    ])
    session_state.get.return_value = df
    
    # Test for Depot A
    stats_a = get_auto_entnahme_stats("Depot A")
    assert stats_a is not None
    assert stats_a["start"] == 2026
    assert stats_a["ende"] == 2027
    assert stats_a["betrag"] == 550.0  # (500 + 600) / 2
    
    # Test for Depot B
    stats_b = get_auto_entnahme_stats("Depot B")
    assert stats_b is not None
    assert stats_b["start"] == 2028
    assert stats_b["ende"] == 2028
    assert stats_b["betrag"] == 1000.0
    
    # Test for non-existent Depot C
    stats_c = get_auto_entnahme_stats("Depot C")
    assert stats_c is None
