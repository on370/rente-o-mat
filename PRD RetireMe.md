# PRD: Rente-O-Mat (Local Python Web-App)
## 1. Context & Objective
The goal is to build a highly precise, local web application for comprehensive retirement planning, specifically tailored to the German tax and pension system.
 The tool simulates different retirement ages, "Altersteilzeit" (ATZ) scenarios, and complex tax calculations, visualizing the cash flow via interactive Sankey diagrams and long-term trend charts.

## 2. Tech Stack
- Language: Python 3.12+
- Framework: Streamlit
- Data Handling: Pandas, NumPy
- Visualization: Plotly (graph_objects, subplots)
- Architecture: Modular (Logic, UI, Data separation)

## 3. Core Modules & Features
### 3.1. Module: Profile & Expenses
- Input Form: User name and monthly expenses by categories.
- Retirement Adjustment Factor: Percentage multiplier per category.
- **Dual View:** Comparison between current active phase and retirement scenario.

### 3.2. Module: Einnahmequelle Engine (Dynamic & Temporal)
- Dynamic addition of multiple streams (DRV, bAV, Private, etc.).
- Validity periods (Start/End Year) for each source.
- Automated tax classification (Nachgelagerte Besteuerung vs. Ertragsanteil).

### 3.3. Module: Timeline & Phase Simulation
- **Global Slider:** Navigation from 2026 to Age 95.
- **Phase Logic:** Automatic switching between "Aktiv", "ATZ(A)" (Active), "ATZ(P)" (Passive), and "Ruhestand".
- **Plausibility:** ATZ is calculated backwards from retirement start (50/50 split).

### 3.4. Module: Visualization (Sankey & Trends)
- **Sankey Diagrams:**
    - Visualizing flows from Gross -> Taxes -> Net -> Expenses.
    - **Logic:** Surplus (green) on the right, Underfunding (red) on the left as a source.
- **Temporal Development (Trend):**
    - **Stacked Bar Chart:** Discrete annual bars showing the breakdown of all income sources.
    - **Lines:** Liquidity need (Net) and optional effective tax rate (%) on a secondary axis.
    - **Milestone Markers:** Vertical dashed lines for ATZ(A), ATZ(P), retirement, and income events.

### 3.5. Module: Persistence
- JSON Export/Import for saving and loading full planning scenarios (Upcoming).

## 4. Execution Plan
- **Step 1: Base UI & Sankey Logic** (Completed)
- **Step 2: Dynamic Income Engine** (Completed)
- **Step 3: Timeline & Phase Simulation** (Completed)
- **Step 4: Refactoring & Modularization** (Completed)
- **Step 5: Advanced Trend Visualization** (Completed)
- **Step 6: JSON Persistence** (Next Task)
- **Step 7: Advanced Tax & SV Engine** (Planned)
