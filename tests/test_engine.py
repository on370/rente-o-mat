import pytest
from logic.engine import (
    calculate_financials_for_year, calculate_break_even_data, get_phase, generate_trend_data
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
        'rentenbeginn': 2033.0,
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

def test_automatic_withdrawals():
    """Prüft die Funktionsweise der verschiedenen automatischen Entnahmestrategien."""
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2032.0,
        'aktuelles_brutto': 0.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [],
        'ausgaben_kategorien': ["Lebenshaltung"],
        'ausgaben_input': {"Lebenshaltung": 1000.0},
        'anpassungsfaktor_input': {"Lebenshaltung": 100},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            {"name": "Depot A", "startwert": 10000.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False},
            {"name": "Depot B", "startwert": 10000.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Bedarfsgesteuert: Wasserfall (Priorisiert)',
        'entnahme_wasserfall_reihenfolge': ["Depot A", "Depot B"]
    }
    
    # 1. Test Wasserfall
    df = generate_trend_data([2026], test_params)
    assert df.loc[0, "ASSET_VAL_Depot A"] == 0.0
    assert df.loc[0, "ASSET_VAL_Depot B"] == 8000.0
    
    # 2. Test Pro Rata
    test_params['entnahme_strategie'] = 'Bedarfsgesteuert: Pro Rata (Gleichmäßig)'
    df_pr = generate_trend_data([2026], test_params)
    assert df_pr.loc[0, "ASSET_VAL_Depot A"] == 4000.0
    assert df_pr.loc[0, "ASSET_VAL_Depot B"] == 4000.0
    
    # 3. Test Fixer Prozentsatz
    test_params['entnahme_strategie'] = 'Regelbasiert: Fixer Prozentsatz (z.B. 4%-Regel)'
    test_params['entnahme_fix_pct'] = 5.0
    df_pct = generate_trend_data([2026], test_params)
    assert df_pct.loc[0, "ASSET_VAL_Depot A"] == 9500.0
    assert df_pct.loc[0, "ASSET_VAL_Depot B"] == 9500.0


def test_abzuege_brutto():
    """Prüft, ob Abzüge vom Brutto das Steuer-/SV-pflichtige Brutto und Netto mindern sowie Rentenpunkte reduzieren."""
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2035.0,
        'aktuelles_brutto': 6000.0,
        'abzuege_brutto': 500.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
    }
    
    # 1. Berechne ohne Abzüge
    params_no_ded = test_params.copy()
    params_no_ded['abzuege_brutto'] = 0.0
    res_no_ded = calculate_financials_for_year(2027, params_no_ded)
    
    # 2. Berechne mit Abzügen
    res_ded = calculate_financials_for_year(2027, test_params)
    
    # Brutto-Einkommens-Wert (Auszahlungsbrutto) soll bei beiden gleich sein
    assert res_no_ded["Brutto"] == 6000.0
    assert res_ded["Brutto"] == 6000.0
    
    # Steuer und SV-pflichtiges Brutto ist reduziert, daher müssen Steuern und SV niedriger sein
    assert res_ded["EkSt"] < res_no_ded["EkSt"]
    assert res_ded["Sozialabgaben"] < res_no_ded["Sozialabgaben"]
    
    # Netto-Einkommen muss bei Abzügen niedriger sein (Brutto - Steuern - SV - Abzug)
    assert res_ded["Netto-Einkommen"] < res_no_ded["Netto-Einkommen"]
    
    # Die Abzüge müssen im Resultat-Dict erfasst sein
    assert res_ded["Abzuege_Brutto"] == 500.0
    assert res_no_ded["Abzuege_Brutto"] == 0.0


