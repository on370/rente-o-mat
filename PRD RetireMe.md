# PRD: Ruhestands-Cockpit (Local Python Web-App)
## 1. Context & Objective
The goal is to build a highly precise, local web application for comprehensive retirement planning, specifically tailored to the German tax and pension system. The tool simulates different retirement ages, "Altersteilzeit" (ATZ) scenarios, and complex tax calculations, visualizing the cash flow via interactive Sankey diagrams and long-term trend charts.

## 2. Tech Stack
- Language: Python 3.10+
- Framework: Streamlit
- Data Handling: Pandas, NumPy
- Visualization: Plotly (graph_objects)

## 3. Core Modules & Features
### 3.1. Module: Haushaltsbuch & Liquiditätsbedarf
- Input Form: Monthly expenses by categories.
- Retirement Adjustment Factor: Percentage multiplier per category.
- **Dual View:** Comparison between current active phase and retirement scenario.

### 3.2. Module: Einnahmequelle Engine (Dynamic & Temporal)
- Dynamic addition of multiple streams (DRV, bAV, Private, etc.).
- Validity periods (Start/End Year) for each source.
- Automated tax classification (Nachgelagerte Besteuerung vs. Ertragsanteil).

### 3.3. Module: Timeline & Phase Simulation
- **Global Slider:** Navigation from 2026 to Age 95.
- **Phase Logic:** Automatic switching between "Aktiv", "ATZ", and "Rente" based on the selected year and milestones.

### 3.4. Module: Visualization (Sankey & Trends)
- **Sankey Diagrams:**
    - Visualizing flows from Gross -> Taxes -> Net -> Expenses.
    - **Logic:** Surplus (green) on the right, Underfunding (red) on the left as a source.
- **Trend Chart:**
    - Stacked Area Chart (Income vs. Liquidity Need).
    - **Milestone Markers:** Vertical dashed lines for ATZ start, retirement, and income events.

### 3.5. Module: Persistence (Upcoming)
- JSON Export/Import for saving and loading full planning scenarios.

## 4. Execution Plan (Status: End of Session)
- **Step 1: Base UI & Sankey Logic** (Completed)
- **Step 2: Dynamic Income Engine** (Completed)
- **Step 3: Timeline & Phase Simulation** (Completed)
- **Step 4: Trend Visualization & Milestones** (Completed)
- **Step 5: JSON Persistence** (Next Session)
- **Step 6: Refactoring & Modularization** (Next Session)
