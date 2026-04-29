# 🛡️ Rente-O-Mat: Das Ruhestands-Cockpit

**Rente-O-Mat** ist eine präzise, lokale Web-Applikation zur umfassenden Ruhestandsplanung, die speziell auf das deutsche Steuer- und Rentensystem zugeschnitten ist. Mit interaktiven Visualisierungen hilft das Tool dabei, den Weg vom Brutto-Einkommen zur Netto-Liquidität über verschiedene Lebensphasen (Aktiv, ATZ, Rente) hinweg zu verstehen.

## 🚀 Kernfunktionen

*   **Duale Sankey-Analyse:** Visualisierung des Cashflows für den aktuellen Status Quo und zukünftige Szenarien mit intelligenter Defizit-Logik.
*   **Dynamische Einnahme-Engine:** Hinzufügen/Editieren verschiedener Quellen (DRV, bAV, privat) mit individueller zeitlicher Gültigkeit.
*   **Zeitstrahl-Simulation:** Globaler Slider von 2026 bis Alter 95 mit automatischer Phasen-Erkennung (Aktiv, ATZ(A/P), Ruhestand).
*   **Persistenz:** Export und Import der Planungsszenarien als JSON (Prefix: `R-O-M_`).
*   **Zeitliche Entwicklung:** Detailliertes, gestapeltes Balkendiagramm aller Einkommensquellen vs. Bedarf über die gesamte Lebensspanne.
*   **Steuer-Analyse:** Visualisierung des effektiven Steuersatzes über die Zeit.

## 🛠️ Tech-Stack

*   **Sprache:** Python 3.12+
*   **Framework:** [Streamlit](https://streamlit.io/)
*   **Visualisierung:** [Plotly](https://plotly.com/python/)
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

---
Erstellt mit ❤️ für eine sichere Finanzplanung.
