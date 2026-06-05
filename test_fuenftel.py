import sys
from logic.taxes import berechne_fuenftelregelung

m_ekst = berechne_fuenftelregelung(60000, 610000, 2030)
print(f"Tax: {m_ekst}")
