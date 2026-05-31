#!/usr/bin/env python3
"""Quick math verification for engine formulas."""

# 1. Annuitätenformel (engine.py Z.319)
K = 100000; r = 0.05; n = 20
rate = K * (r / (1 - (1+r)**(-n)))
ref = K * (r * (1+r)**n) / ((1+r)**n - 1)
print(f"Annuity K={K}, r={r}, n={n}: {rate:.2f}")
print(f"Reference: {ref:.2f}")
print(f"Match: {abs(rate - ref) < 0.01}")

# 2. Substanzerhalt-Formel (engine.py Z.592)
# yield = cap * (r / (1+r))
# Idee: Entnehme genau so viel, dass Kapital erhalten bleibt
# Aber die Formel berechnet cap * r / (1+r) = 4761.90
# Tatsächlicher Jahresgewinn = cap * r = 5000
# Differenz: 238.10 — das ist NICHT der volle Gewinn!
print()
yield_w = K * (r / (1.0 + r))
gewinn = K * r
print(f"Substanzerhalt-Entnahme: {yield_w:.2f}")
print(f"Tatsaechlicher Jahresgewinn: {gewinn:.2f}")
print(f"Differenz: {gewinn - yield_w:.2f}")

# Die Formel cap*r/(1+r) ist die vorschüssige Annuität für 1 Periode.
# Sie nimmt an, dass man am ANFANG des Jahres entnimmt.
# Aber die Engine entnimmt am ENDE (nach Verzinsung in Z.309).
# Also sollte man einfach den Gewinn entnehmen: cap * r (nach Steuern: cap*r - steuer)

# 3. Substanzerhalt NACH Steuern
print()
print("=== Nach Steuern (AbgSt) ===")
brutto_g = K * r  # 5000
steuer = brutto_g * 0.25 * 1.055  # AbgSt + Soli = 26.375%
netto_kapital = K + brutto_g - steuer
max_w = netto_kapital * (r / (1 + r))  # Formel nutzt BRUTTO-r auf NETTO-Kapital!
print(f"Brutto-Gewinn: {brutto_g:.2f}")
print(f"Steuer: {steuer:.2f}")
print(f"Netto-Kapital: {netto_kapital:.2f}")
print(f"Entnahme (Substanzerhalt): {max_w:.2f}")
print(f"Kapital danach: {netto_kapital - max_w:.2f}")
print(f"Abweichung vom Startkapital: {netto_kapital - max_w - K:.2f}")
# Korrekt wäre: gewinn - steuer = 5000 - 1318.75 = 3681.25
print(f"Korrekte Entnahme (nur Netto-Gewinn): {brutto_g - steuer:.2f}")

# 4. Doppelte Entnahme: Fixer Prozentsatz PLUS Defizit-Deckung
print()
print("=== 4%-Regel Entnahme ===")
# Fixer Prozentsatz entnimmt IMMER, auch bei Überschuss
# Das kann dazu führen, dass Assets zu schnell schrumpfen
# Aber: Die Entnahme wird zum Netto addiert (Z.575) -> erhöht Überschuss
# -> wird dann reinvestiert (Z.643) -> Loop!
print("WARNUNG: Fixe Prozentsatz-Entnahme bei Überschuss -> Reinvestitions-Loop möglich")
