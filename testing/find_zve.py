#!/usr/bin/env python3
import math
from logic.taxes import berechne_einkommensteuer

# Find what zvE gives exactly 1867 € Tax per month (22404 € per year)
target_tax = 1867 * 12

for zve in range(60000, 100000, 100):
    tax = berechne_einkommensteuer(zve, 2026)
    if abs(tax - target_tax) < 100:
        print(f"zvE {zve} -> Tax {tax/12:.2f} €/mtl")

