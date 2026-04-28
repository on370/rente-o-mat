# 🛡️ RetireMe: Das Ruhestands-Cockpit

**RetireMe** ist eine präzise, lokale Web-Applikation zur umfassenden Ruhestandsplanung, die speziell auf das deutsche Steuer- und Rentensystem zugeschnitten ist. Mit interaktiven Visualisierungen hilft das Tool dabei, den Weg vom Brutto-Einkommen zur Netto-Liquidität über verschiedene Lebensphasen (Aktiv, ATZ, Rente) hinweg zu verstehen.

## 🚀 Kernfunktionen

*   **Duale Sankey-Analyse:** Visualisierung des Cashflows für den aktuellen Status Quo und zukünftige Szenarien.
*   **Dynamische Einnahme-Engine:** Hinzufügen verschiedener Quellen (Gesetzliche Rente, Betriebsrente (bAV), private Renten, Lebensversicherungen) mit individuellen Start- und Endzeitpunkten.
*   **Zeitstrahl-Simulation:** Ein globaler Slider ermöglicht das "Durchwandern" der Jahre von 2026 bis zum Alter von 95 Jahren.
*   **Altersteilzeit (ATZ) Simulator:** Berechnung von Netto-Effekten unter Berücksichtigung des Progressionsvorbehalts.
*   **Präzise Steuer-Logik:** Implementierung der Einkommensteuer nach EStG § 32a und Berücksichtigung des Rentenfreibetrags (Kohortenprinzip).
*   **Langfrist-Trend:** Ein gestapeltes Flächendiagramm zeigt die Entwicklung von Einkommen vs. Liquiditätsbedarf über die gesamte Lebensspanne.

## 🛠️ Tech-Stack

*   **Sprache:** Python 3.10+
*   **Framework:** [Streamlit](https://streamlit.io/) (UI)
*   **Visualisierung:** [Plotly](https://plotly.com/python/) (Sankey & Trends)
*   **Datenverarbeitung:** Pandas, NumPy

## 📦 Installation & Start

1.  **Repository klonen:**
    ```bash
    git clone https://github.com/DEIN_NUTZERNAME/RetireMe.git
    cd RetireMe
    ```

2.  **Abhängigkeiten installieren:**
    ```bash
    pip install streamlit pandas plotly
    ```

3.  **App starten:**
    ```bash
    streamlit run app.py
    ```

## 📈 Roadmap

- [ ] **Persistenz:** Export und Import der Planungsszenarien als JSON.
- [ ] **Detaillierte Sozialabgaben:** Unterscheidung zwischen KVdR und freiwilliger gesetzlicher Versicherung.
- [ ] **Szenarienvergleich:** Gegenüberstellung verschiedener Renteneintritts-Szenarien.
- [ ] **Modularisierung:** Refactoring des Codes in saubere Logik- und UI-Module.

## ⚠️ Disclaimer

Dieses Tool dient der Planung und Orientierung. Die berechneten Werte (insbesondere Steuern und Sozialabgaben) sind Näherungswerte und ersetzen keine professionelle Renten- oder Steuerberatung.

---
Erstellt mit ❤️ für eine sichere Finanzplanung.
