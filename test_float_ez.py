import pandas as pd
from logic.engine import generate_trend_data

p = {
    'aktuelles_jahr': 2026,
    'geburtsjahr': 1965,
    'rentenbeginn': 2031.5,
    'inflation_rate': 2.0,
    'einnahmen': [{'name': 'Mein bAV', 'typ': 'bAV (Einmalzahlung)', 'start': 2031.5, 'ende': 2031.5, 'betrag': 610000}],
    'ausgaben_kategorien': [], 'ausgaben_input': {}, 'assets': []
}
df = generate_trend_data(range(2028, 2033), p)
print(df[['Jahr', 'Label', 'Mein bAV', 'Kapitalzuwachs_Sonder']])
