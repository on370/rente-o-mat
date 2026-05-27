import pytest
from logic.rentenrecht import (
    berechne_regelaltersgrenze, berechne_monate_frueher,
    berechne_ep_pro_jahr, berechne_beitragsverlust_logic
)
from config import DURCHSCHNITTSENTGELT_AKTUELL

def test_regelaltersgrenze():
    """Prüft die Regelaltersgrenze (§ 35 SGB VI) nach Geburtsjahr."""
    tests = [
        (1946, (65, 0)),
        (1947, (65, 1)),
        (1952, (65, 6)),
        (1958, (66, 0)),
        (1959, (66, 2)),
        (1963, (66, 10)),
        (1964, (67, 0)),
        (1965, (67, 0))
    ]
    for gj, expected in tests:
        assert berechne_regelaltersgrenze(gj) == expected

def test_monate_frueher():
    """Prüft die vorzeitigen Rentenbezugsmonate vor der RAG."""
    # GJ 1965: RAG = 67
    assert berechne_monate_frueher(1965, 2032.0) == 0      # Punktlandung RAG
    assert berechne_monate_frueher(1965, 2030.0) == 24     # 2 Jahre früher

def test_ep_pro_jahr():
    """Prüft die Ermittlung der Entgeltpunkte."""
    # 6000 mtl -> 72000 jährlich, unter BBG RV 2025
    ep_exp = 72000 / DURCHSCHNITTSENTGELT_AKTUELL
    assert berechne_ep_pro_jahr(6000, 2025) == ep_exp

def test_beitragsverlust():
    """Prüft den berechneten Beitragsverlust."""
    # 24 Monate früher, 1.5 EP/Jahr, Rentenwert 42.0
    bv = berechne_beitragsverlust_logic(24, 1.5, 42.0)
    assert bv["ep"] == 3.0
    assert bv["euro"] == 126.0
