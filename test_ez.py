import sys
import pandas as pd
from logic.engine import generate_trend_data

p = {
    "aktuelles_jahr": 2026,
    "geburtsjahr": 1965,
    "rentenbeginn": 2030,
    "inflation_rate": 2.0,
    "einnahmen": [
        {"name": "Gehalt", "typ": "Gesetzlich", "start": 2026, "ende": 2030, "betrag": 5000},
        {"name": "Mein bAV", "typ": "bAV (Einmalzahlung)", "start": 2030, "ende": 2030, "betrag": 610000}
    ],
    "ausgaben_kategorien": [],
    "ausgaben_input": {},
    "assets": []
}

df = generate_trend_data(range(2028, 2032), p)
print("Dataframe columns:", df.columns.tolist())
if "Mein bAV" in df.columns:
    print("Values for 'Mein bAV':")
    for idx, row in df.iterrows():
        print(f"Jahr {row['Jahr']} Label {row['Label']}: {row['Mein bAV']}")
else:
    print("'Mein bAV' column not found!")
