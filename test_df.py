import sys
import pandas as pd
from logic.engine import generate_trend_data
from logic.defaults import DEFAULT_PARAMS

print("Testing")
df = generate_trend_data(range(2026, 2035), DEFAULT_PARAMS)
print(df.columns)
