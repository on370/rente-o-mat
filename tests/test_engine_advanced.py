import pytest
import pandas as pd
from logic.engine import generate_trend_data

def test_steuerguenstig_strategy():
    """
    Prüft, ob die steuergünstige Entnahmestrategie die Töpfe in der korrekten Reihenfolge leert:
    1. Steuerfrei
    2. Teilfreistellung
    3. Abgeltungsteuer
    """
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
        'ausgaben_input': {"Lebenshaltung": 1000.0},  # 12.000 € Defizit pro Jahr
        'anpassungsfaktor_input': {"Lebenshaltung": 100},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            # Alle haben 10.000 € Startwert und 0% Rendite zur einfacheren Verprobung
            {"name": "Depot Abgeltung", "startwert": 10000.0, "rendite_pa": 0.0, "steuertyp": "abgeltung", "entnahme_aktiv": False},
            {"name": "Depot Teilfreistellung", "startwert": 10000.0, "rendite_pa": 0.0, "steuertyp": "teilfreistellung", "entnahme_aktiv": False},
            {"name": "Depot Steuerfrei", "startwert": 10000.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Bedarfsgesteuert: Steuergünstig (Steuerfreie zuerst)',
        'reinvest_target': '— Keine (nur Cash-Reserven) —',
        'liquidity_reserve': 0.0,
        'liquidity_yield': 0.0
    }

    df = generate_trend_data([2026], test_params)
    
    # Depot Steuerfrei sollte komplett geleert sein (10.000 €)
    assert df.loc[0, "ASSET_VAL_Depot Steuerfrei"] == 0.0
    # Depot Teilfreistellung sollte die restlichen 2.000 € gedeckt haben -> 8.000 € Restwert
    assert df.loc[0, "ASSET_VAL_Depot Teilfreistellung"] == 8000.0
    # Depot Abgeltung sollte unberührt sein -> 10.000 € Restwert
    assert df.loc[0, "ASSET_VAL_Depot Abgeltung"] == 10000.0


def test_substanzerhalt_strategy():
    """
    Prüft, ob die Substanzerhalt-Strategie nur den Netto-Gewinn der Periode entnimmt
    und das ursprüngliche Kapital erhält.
    """
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
        'ausgaben_input': {"Lebenshaltung": 2000.0},  # 24.000 € Defizit pro Jahr
        'anpassungsfaktor_input': {"Lebenshaltung": 100},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            # 100.000 € Startwert, 5% Rendite -> 5.000 € steuerfreier Zuwachs
            {"name": "Depot Erhalt", "startwert": 100000.0, "rendite_pa": 5.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Substanzerhalt (Nur Rendite entnehmen)',
        'entnahme_wasserfall_reihenfolge': ["Depot Erhalt"],
        'reinvest_target': '— Keine (nur Cash-Reserven) —',
        'liquidity_reserve': 0.0,
        'liquidity_yield': 0.0
    }

    df = generate_trend_data([2026], test_params)
    
    # Obwohl das Defizit 24.000 € beträgt, dürfen nur maximal 5.000 € (Rendite) entnommen werden.
    # Kapitalwert nach Verzinsung: 105.000 €
    # Abzüglich Entnahme von 5.000 €: 100.000 € (Substanz erhalten)
    assert df.loc[0, "ASSET_VAL_Depot Erhalt"] == 100000.0


def test_zielverzehr_strategy():
    """
    Prüft, ob der Zielverzehr bei einer Restlaufzeit von 1 Jahr das Asset
    am Jahresende durch eine passende Annuitätenentnahme exakt auf Null bringt.
    """
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
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            # 100.000 € Startwert, 10% Rendite -> 110.000 € nach Zinsung
            {"name": "Ziel Depot", "startwert": 100000.0, "rendite_pa": 10.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Zielverzehr (Null-Landung bis Alter X)',
        # Alter im Jahr 2026 ist 2026 - 1965 = 61 Jahre.
        # Zielalter 62 bedeutet 1 verbleibendes Jahr.
        'entnahme_ziel_alter': 62,
        'reinvest_target': '— Keine (nur Cash-Reserven) —',
        'liquidity_reserve': 0.0,
        'liquidity_yield': 0.0
    }

    df = generate_trend_data([2026], test_params)
    
    # Das Asset muss exakt bei 0.0 landen
    assert pytest.approx(df.loc[0, "ASSET_VAL_Ziel Depot"], abs=1e-5) == 0.0
