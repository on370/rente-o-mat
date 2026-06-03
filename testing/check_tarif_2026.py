#!/usr/bin/env python3
"""Vergleich: Unser Rechner (2025er Tarif als Fallback) vs. korrekter 2026er Tarif."""
import math

def ekst_2025(zve):
    """Unser aktueller Code (2025er Tarif)."""
    X = math.floor(max(0, zve))
    if X <= 12096: return 0
    elif X <= 17443:
        y = (X - 12096) / 10000
        return math.floor((932.30 * y + 1400) * y)
    elif X <= 68480:
        y = (X - 17443) / 10000
        return math.floor((176.64 * y + 2397) * y + 1015.13)
    elif X <= 277825:
        return math.floor(0.42 * X - 10911.92)
    else:
        return math.floor(0.45 * X - 19246.67)

def ekst_2026(zve):
    """Korrekter 2026er Tarif (BMF)."""
    X = math.floor(max(0, zve))
    if X <= 12348: return 0
    elif X <= 17799:
        y = (X - 12348) / 10000
        return math.floor((914.51 * y + 1400) * y)
    elif X <= 69878:
        y = (X - 17799) / 10000
        return math.floor((173.10 * y + 2397) * y + 1034.87)
    elif X <= 277825:
        return math.floor(0.42 * X - 11135.63)
    else:
        return math.floor(0.45 * X - 19470.38)

# Testfälle
test_zve = [
    ("A: Friseurin", 22875),
    ("B: Ingenieur", 55718),
    ("C: Chefarzt", 117719),
    ("Grundfreibetrag-Grenze", 12300),
    ("Median-Einkommen", 35000),
    ("Gutverdiener", 80000),
]

print(f"{'Szenario':<25} {'zvE':>8} {'2025-Tarif':>10} {'2026-Tarif':>10} {'Diff':>8} {'Diff%':>7}")
print("-" * 72)
for label, zve in test_zve:
    st25 = ekst_2025(zve)
    st26 = ekst_2026(zve)
    diff = st25 - st26
    pct = diff / max(1, st26) * 100
    print(f"{label:<25} {zve:>8,} {st25:>10,} {st26:>10,} {diff:>+8,} {pct:>+6.1f}%")

print()
print("Fazit: Nutzer zahlen mit dem 2025er Tarif systematisch zu viel EkSt.")
print("Abweichung steigt mit dem Einkommen (höherer Grundfreibetrag + angepasste Progressionszonen).")
