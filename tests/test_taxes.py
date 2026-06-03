import pytest
from logic.taxes import (
    berechne_einkommensteuer, berechne_rentensteuer_anteil, 
    berechne_soli, berechne_abgeltungsteuer, 
    berechne_progressionsvorbehalt, berechne_kirchensteuer,
    berechne_ertragsanteil, berechne_fuenftelregelung
)

def test_est_tarif_2025():
    """Prüft den Einkommensteuertarif 2025 gemäß § 32a EStG (abgerundet)."""
    tests = [
        (12096, 0.0),      # Grundfreibetrag
        (12097, 0.0),      # Abgerundet auf 0
        (15000, 485.0),    # Zone 2
        (17443, 1015.0),   # Zone 2 Ende
        (20000, 1639.0),   # Zone 3
        (30000, 4303.0),
        (40000, 7320.0),
        (50000, 10691.0),
        (60000, 14415.0),
        (80000, 22688.0),  # Zone 4
        (100000, 31088.0),
        (200000, 73088.0),
        (277825, 105774.0),
        (300000, 115753.0) # Zone 5
    ]
    for zve, expected in tests:
        assert berechne_einkommensteuer(zve, 2025) == expected

def test_est_tarif_2026():
    """Prüft den Einkommensteuertarif 2026 gemäß Steuerfortentwicklungsgesetz (abgerundet)."""
    tests = [
        (12348, 0.0),      # Grundfreibetrag
        (30000, 4217.0),
        (50000, 10548.0),
        (100000, 30864.0)
    ]
    for zve, expected in tests:
        assert berechne_einkommensteuer(zve, 2026) == expected

def test_est_tarif_2024():
    """Prüft den Einkommensteuertarif 2024 gemäß § 32a EStG (abgerundet)."""
    tests = [
        (11784, 0.0),      # GFB 2024
        (30000, 4412.0),
        (50000, 10872.0)
    ]
    for zve, expected in tests:
        assert berechne_einkommensteuer(zve, 2024) == expected

def test_rentenbesteuerungsanteil():
    """Prüft den steuerpflichtigen Anteil der Rente nach Kohortenjahr."""
    tests = [
        (2005, 50.0),
        (2010, 60.0),
        (2015, 70.0),
        (2020, 80.0),
        (2023, 82.5),
        (2025, 83.5),
        (2030, 86.0),
        (2058, 100.0)
    ]
    for jahr, expected in tests:
        assert berechne_rentensteuer_anteil(jahr) == expected

def test_solidaritaetszuschlag():
    """Prüft den Solidaritätszuschlag mit jahresabhängigen Freigrenzen."""
    # 2024: Freigrenze 18.130 €
    assert berechne_soli(18130, jahr=2024) == 0.0
    assert pytest.approx(berechne_soli(18200, jahr=2024), 0.01) == 8.33
    assert berechne_soli(50000, jahr=2024) == 2750.0

    # 2025+: Freigrenze 19.950 €
    assert berechne_soli(19950, jahr=2025) == 0.0
    assert berechne_soli(18200, jahr=2025) == 0.0

def test_abgeltungsteuer():
    """Prüft die Abgeltungsteuer mit Soli und Kirchensteuer."""
    # Ohne Kirchensteuer (10k Ertrag - 1k Freibetrag = 9k steuerpflichtig * 26.375% = 2373.75)
    assert berechne_abgeltungsteuer(10000, 0.0) == 2373.75
    assert berechne_abgeltungsteuer(800, 0.0) == 0.0
    # Mit 9% Kirchensteuer
    assert pytest.approx(berechne_abgeltungsteuer(10000, 0.09), 1.0) == 2363.53

def test_kirchensteuer():
    """Prüft die Kirchensteuer-Berechnung."""
    assert berechne_kirchensteuer(10000, 0.09) == 900.0
    assert berechne_kirchensteuer(10000, 0.0) == 0.0

def test_ertragsanteil():
    """Prüft den Ertragsanteil bei privater Rente nach Alter."""
    assert berechne_ertragsanteil(60) == 22
    assert berechne_ertragsanteil(65) == 18
    assert berechne_ertragsanteil(67) == 17

def test_progressionsvorbehalt():
    """Prüft den Progressionsvorbehalt."""
    assert pytest.approx(berechne_progressionsvorbehalt(30000, 10000, 2025), 1.0) == 5490.0

def test_fuenftelregelung():
    """Prüft die Fünftelregelung bei Einmalzahlungen."""
    assert pytest.approx(berechne_fuenftelregelung(20000, 100000, 2025), 1.0) == 28405.0
