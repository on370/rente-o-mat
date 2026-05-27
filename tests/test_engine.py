import pytest
from logic.engine import (
    calculate_financials_for_year, calculate_break_even_data, get_phase
)

def test_get_phase():
    """Prüft die Phasenübergänge."""
    assert get_phase(2033, False, 9999, 2032) == "Rente"
    assert get_phase(2030, False, 9999, 2032) == "Aktiv"
    assert get_phase(2031, True, 2030, 2032) == "ATZ(P)"

def test_engine_ruhestand():
    """Prüft die Finanzengine in der Rentenphase."""
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2032.0,
        'aktuelles_brutto': 6000.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [
            {"name": "Gesetzliche Rente", "betrag": 2000.0, "typ": "Gesetzlich", 
             "start": 2032.0, "ende": 2060, "eingabe_modus": "euro"}
        ],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'anpassungsfaktor_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
    }

    res = calculate_financials_for_year(2033, test_params)
    assert res["Brutto"] == 2000.0
    assert pytest.approx(res["Sozialabgaben"], 0.5) == 211.0
    assert pytest.approx(res["EkSt"], 0.5) == 101.5
    assert pytest.approx(res["Netto-Einkommen"], 0.5) == 1687.5

def test_break_even_underjahrig():
    """Prüft, ob die monatsgenaue Break-Even-Berechnung sauber läuft (M5)."""
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2032.5, # 1. Juli 2032
        'aktuelles_brutto': 6000.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 2.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 1.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [
            {"name": "Gesetzliche Rente", "betrag": 2000.0, "typ": "Gesetzlich", 
             "start": 2032.5, "ende": 2060, "eingabe_modus": "euro"}
        ],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'anpassungsfaktor_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
    }
    
    df, be_jahr, be_alter = calculate_break_even_data(test_params)
    assert not df.empty
    # Break-Even sollte innerhalb der Lebensspanne erreicht werden
    assert be_jahr is not None
    assert be_alter >= 67
