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


def test_individual_start_transition():
    """
    Prüft, ob die automatische Entnahme bei individuellem Start (z.B. September 2028)
    exakt im gewählten Monat startet und das Jahr korrekt gesplittet wird (M10).
    """
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2035.0,
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
            {"name": "Depot A", "startwert": 100000.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Bedarfsgesteuert: Wasserfall (Priorisiert)',
        'entnahme_wasserfall_reihenfolge': ["Depot A"],
        'entnahme_start_modus': 'Individuell (Jahr/Monat)',
        'entnahme_start_jahr': 2028,
        'entnahme_start_monat': 9, # September
        'reinvest_target': '— Keine (nur Cash-Reserven) —',
        'liquidity_reserve': 0.0,
        'liquidity_yield': 0.0
    }

    # Wir generieren Daten für 2028. Da im September (9) gestartet wird,
    # muss das Jahr 2028 gesplittet sein in:
    # 1. Segment: Jan-Aug (8 Monate) -> Keine Entnahme
    # 2. Segment: Sep-Dez (4 Monate) -> Entnahme aktiv
    df = generate_trend_data([2028], test_params)
    
    # Es müssen exakt zwei Segmente für das Jahr 2028 existieren
    assert len(df) == 2
    
    # Erstes Segment: Beginn 2028.0 (Januar) bis 2028.666667 (Ende August)
    row_1 = df.iloc[0]
    assert pytest.approx(row_1["start_t"]) == 2028.0
    assert pytest.approx(row_1["end_t"]) == 2028.0 + 8/12
    assert row_1.get("Entnahme: Depot A", 0.0) == 0.0
    
    # Zweites Segment: Beginn 2028.666667 (September) bis 2029.0 (Ende Dezember)
    row_2 = df.iloc[1]
    assert pytest.approx(row_2["start_t"]) == 2028.0 + 8/12
    assert pytest.approx(row_2["end_t"]) == 2029.0
    assert row_2.get("Entnahme: Depot A", 0.0) > 0.0


def test_bav_einmalzahlung_cash_accumulation():
    """
    Prüft, ob eine bAV (Einmalzahlung) im Fälligkeitsjahr den Cash-Reserven
    netto gutgeschrieben wird (wenn Reinvestition deaktiviert ist).
    """
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2030.0,
        'aktuelles_brutto': 0.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [
            {"name": "Einmal-bAV", "betrag": 50000.0, "typ": "bAV (Einmalzahlung)", "start": 2030.0, "ende": 2030.0}
        ],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [],
        'entnahme_strategie': 'Manuell (Keine Automatik)',
        'reinvest_target': '— Keine (nur Cash-Reserven) —',
        'liquidity_reserve': 10000.0,
        'liquidity_yield': 0.0
    }

    # Wir generieren Daten von 2026 bis 2031
    df = generate_trend_data(list(range(2026, 2032)), test_params)
    
    # Vor 2030 muss Cash 0 sein (da kein Gehalt/Ausgaben)
    assert df[df["Jahr"] == 2029]["ASSET_VAL_Cash-Reserven (kum.)"].values[0] == 0.0
    
    # In 2030 findet die bAV-Auszahlung statt.
    cash_2030 = df[df["Jahr"] == 2030]["ASSET_VAL_Cash-Reserven (kum.)"].values[0]
    assert cash_2030 > 45000.0
    assert cash_2030 < 50000.0


def test_bav_einmalzahlung_reinvestment():
    """
    Prüft, ob die Einmalzahlung bei gesetztem Reinvestitions-Ziel
    automatisch in das Ziel-Asset fließt, sobald die Cash-Reserve voll ist.
    """
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2030.0,
        'aktuelles_brutto': 0.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [
            {"name": "Einmal-bAV", "betrag": 50000.0, "typ": "bAV (Einmalzahlung)", "start": 2030.0, "ende": 2030.0}
        ],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            {"name": "Welt-ETF", "startwert": 0.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Manuell (Keine Automatik)',
        'reinvest_target': 'Welt-ETF',
        'liquidity_reserve': 1000.0, # Niedriger Notgroschen
        'liquidity_yield': 0.0
    }

    df = generate_trend_data(list(range(2026, 2032)), test_params)
    
    # Cash-Reserve darf maximal das Limit (1000.0) erreichen
    cash_2030 = df[df["Jahr"] == 2030]["ASSET_VAL_Cash-Reserven (kum.)"].values[0]
    assert cash_2030 == pytest.approx(1000.0)
    
    # Der verbleibende Rest der Netto-Auszahlung muss im Welt-ETF liegen
    etf_2030 = df[df["Jahr"] == 2030]["ASSET_VAL_Welt-ETF"].values[0]
    assert etf_2030 > 44000.0
    assert etf_2030 < 49000.0


def test_bav_einmalzahlung_specific_reinvestment():
    """
    Prüft, ob bei zwei bAV (Einmalzahlungen) im selben Jahr, die auf
    unterschiedliche Reinvestitionsziele verweisen, das Geld korrekt aufgeteilt wird.
    """
    test_params = {
        'geburtsjahr': 1965,
        'aktuelles_jahr': 2026,
        'rentenbeginn': 2030.0,
        'aktuelles_brutto': 0.0,
        'kinderzahl': 0,
        'kirchensteuer_satz': 0.0,
        'inflation_rate': 0.0,
        'rentenanpassung_rate': 0.0,
        'bav_anpassung_rate': 1.0,
        'gehalts_dynamik': 0.0,
        'atz_simulieren': False,
        'atz_start': 9999,
        'einnahmen': [
            {"name": "bAV-Cash", "betrag": 30000.0, "typ": "bAV (Einmalzahlung)", "start": 2030.0, "ende": 2030.0, "reinvest_target": "— Keine (nur Cash-Reserven) —"},
            {"name": "bAV-ETF", "betrag": 30000.0, "typ": "bAV (Einmalzahlung)", "start": 2030.0, "ende": 2030.0, "reinvest_target": "Spezial-ETF"}
        ],
        'ausgaben_kategorien': [],
        'ausgaben_input': {},
        'befristete_ausgaben': [],
        'einmalige_ausgaben': [],
        'assets': [
            {"name": "Spezial-ETF", "startwert": 0.0, "rendite_pa": 0.0, "steuertyp": "steuerfrei", "entnahme_aktiv": False}
        ],
        'entnahme_strategie': 'Manuell (Keine Automatik)',
        'reinvest_target': '— Keine (nur Cash-Reserven) —',  # Global kein Reinvestment
        'liquidity_reserve': 10000.0,
        'liquidity_yield': 0.0
    }

    df = generate_trend_data(list(range(2026, 2032)), test_params)

    cash_2030 = df[df["Jahr"] == 2030]["ASSET_VAL_Cash-Reserven (kum.)"].values[0]
    etf_2030 = df[df["Jahr"] == 2030]["ASSET_VAL_Spezial-ETF"].values[0]

    # bAV-Cash Netto-Betrag fließt in Cash, füllt Liquidität auf (10k), Rest bleibt in Cash.
    # bAV-ETF Netto-Betrag fließt vollständig in Spezial-ETF, da Liquidität bereits durch bAV-Cash voll ist.
    assert cash_2030 > 20000.0
    assert etf_2030 > 20000.0



