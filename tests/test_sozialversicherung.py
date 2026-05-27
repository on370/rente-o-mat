import pytest
from logic.sozialversicherung import (
    berechne_sv_aktiv, berechne_sv_rentner,
    berechne_vorsorgeaufwendungen_steuerlich, berechne_pv_satz, _get_sv_params
)

def test_pv_satz():
    """Prüft den berechneten Pflegeversicherungs-Beitragssatz nach Kinderzahl."""
    p = _get_sv_params(2025)
    # Kinderlos: 1.8% + 0.6% = 2.4%
    assert berechne_pv_satz(0, p) == 0.024
    # 1 Kind: 1.8%
    assert berechne_pv_satz(1, p) == 0.018
    # 2 Kinder: 1.8% - 0.25% = 1.55%
    assert pytest.approx(berechne_pv_satz(2, p), 0.0001) == 0.0155

def test_sv_aktiv():
    """Prüft die SV-Beiträge für aktive Arbeitnehmer."""
    sv = berechne_sv_aktiv(6000, 2025, 0)
    # BBG KV = 5512.50, BBG RV = 8050
    kv_exp = 5512.50 * (0.073 + 0.0085)
    pv_exp = 5512.50 * (0.018 + 0.006)
    rv_exp = 6000 * 0.093
    alv_exp = 6000 * 0.013
    assert pytest.approx(sv["KV"], 0.01) == kv_exp
    assert pytest.approx(sv["PV"], 0.01) == pv_exp
    assert pytest.approx(sv["RV"], 0.01) == rv_exp
    assert pytest.approx(sv["ALV"], 0.01) == alv_exp

def test_sv_rentner():
    """Prüft die SV-Beiträge für Rentner."""
    # Gesetzlich 2000 €: KVdR + PV (kinderlos)
    sv_r = berechne_sv_rentner([{"name": "GRV", "betrag": 2000, "typ": "Gesetzlich"}], 2025, 0)
    kv_r_exp = 2000 * (0.073 + 0.0085)
    pv_r_exp = 2000 * (0.018 + 0.006)
    assert pytest.approx(sv_r["Gesamt"], 0.5) == kv_r_exp + pv_r_exp

    # bAV 600 €: Voller Beitragssatz oberhalb Freibetrag 187.25
    bav_pfl = max(0, 600 - 187.25)
    kv_bav_exp = bav_pfl * (0.073*2 + 0.0085*2)
    pv_bav_exp = bav_pfl * (0.018 + 0.006) * 2
    sv_bav = berechne_sv_rentner([{"name": "bAV", "betrag": 600, "typ": "bAV"}], 2025, 0)
    assert pytest.approx(sv_bav["Gesamt"], 0.5) == kv_bav_exp + pv_bav_exp

def test_sv_rentner_doppel_bav():
    """Prüft die einmalige Anwendung des Freibetrags bei zwei bAV-Bezugsquellen (M3)."""
    # Summe bAV = 800 EUR. Einmaliger Freibetrag 187.25.
    bav_pfl = max(0, 800 - 187.25)
    kv_bav_exp = bav_pfl * (0.073*2 + 0.0085*2)
    pv_bav_exp = bav_pfl * (0.018 + 0.006) * 2
    sv_bav = berechne_sv_rentner([
        {"name": "bAV 1", "betrag": 600, "typ": "bAV"},
        {"name": "bAV 2", "betrag": 200, "typ": "bAV"}
    ], 2025, 0)
    assert pytest.approx(sv_bav["Gesamt"], 0.5) == kv_bav_exp + pv_bav_exp

def test_vorsorgeaufwendungen_steuerlich():
    """Prüft die abziehbaren Vorsorgeaufwendungen (Sonderausgaben)."""
    # Aktiv
    va = berechne_vorsorgeaufwendungen_steuerlich(6000, 2025, 'Aktiv')
    rv_an = min(6000, 8050) * 0.093
    rv_abzug = rv_an * 2
    kv_an = min(6000, 5512.5) * (0.073 + 0.0085)
    pv_an = min(6000, 5512.5) * 0.018
    kv_pv_abzug = (kv_an + pv_an) * 0.96
    assert pytest.approx(va, 0.01) == (rv_abzug + kv_pv_abzug) * 12

    # Rente (2000 € GRV, kinderlos, 96% KV + 100% PV)
    einnahmen_r = [{"name": "GRV", "betrag": 2000.0, "typ": "Gesetzlich"}]
    va_rente = berechne_vorsorgeaufwendungen_steuerlich(2000, 2025, 'Rente', kinderzahl=0, einnahmen_liste=einnahmen_r)
    kv_r_exp = 2000 * (0.073 + 0.0085)
    pv_r_exp = 2000 * (0.018 + 0.006)
    assert pytest.approx(va_rente, 0.01) == (kv_r_exp * 0.96 + pv_r_exp) * 12
