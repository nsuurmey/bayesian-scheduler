# Capacity Planning — Method Comparison Tool

Compare five different approaches to estimating and scheduling project capacity over a 12-month planning horizon for a ~20-person technical team.

## Methods

| Method | Approach | Solver |
|--------|----------|--------|
| **PERT** | Three-point estimation + Monte Carlo simulation over Beta-PERT distributions | NumPy/SciPy |
| **RCPSP** | Integer linear programming to optimally schedule tasks under hard resource caps | PuLP (CBC) |
| **Bayesian** | Conjugate Normal-Inverse-Gamma priors updated with project estimates; posterior predictive distributions | SciPy |
| **Portfolio Optimisation** | Selects and sequences projects to maximise total business value under constraints | PuLP (CBC) |
| **Scenario Planning** | Monte Carlo under optimistic/likely/pessimistic assumptions with unplanned work injection | NumPy |

## Quick Start

```bash
pip install numpy scipy pandas pulp plotly openpyxl
cd capacity_comparison
python visualizer.py
# → creates comparison_dashboard.html
```

Open `comparison_dashboard.html` in a browser. The dashboard is self-contained (no server needed).

### Using your own data (spreadsheet)

```bash
# 1. Generate a pre-filled Excel template
python create_template.py
# → creates portfolio_template.xlsx

# 2. Edit portfolio_template.xlsx in Excel/Google Sheets/LibreOffice
#    - Projects sheet: one row per project (durations, resource profiles, etc.)
#    - Tasks sheet: one row per task, linked to projects by name
#    - Config sheet: team headcount and historical duration data

# 3. Run the dashboard from your spreadsheet
python load_spreadsheet.py portfolio_template.xlsx
# → creates comparison_dashboard.html from your data
```

## File Structure

```
capacity_comparison/
├── shared_dataset.py          # Single source-of-truth: 7 projects, team capacity, historical data
├── create_template.py         # Generates portfolio_template.xlsx with sample data
├── load_spreadsheet.py        # Loads .xlsx → runs visualizer with custom data
├── portfolio_template.xlsx    # Excel template (generated, edit this)
├── methods/
│   ├── __init__.py
│   ├── pert.py                # PERT with critical path + Monte Carlo
│   ├── rcpsp.py               # Resource-constrained scheduling (ILP)
│   ├── bayesian.py            # Bayesian duration estimation (NIG conjugate)
│   ├── portfolio_opt.py       # Portfolio selection + scheduling (ILP)
│   └── scenario_planning.py   # What-if analysis with unplanned work
├── visualizer.py              # Runs all methods, builds Plotly dashboard
├── comparison_dashboard.html  # Output: interactive HTML dashboard
└── README.md
```

## Dashboard Panels

- **Panel A — Timeline View**: Gantt-style comparison showing when each method schedules each project, with uncertainty bands where applicable.
- **Panel B — Capacity Heatmap**: 12-month × 5-method grid coloured by utilisation percentage. Red = over capacity.
- **Panel C — Risk & Uncertainty**: PERT duration distributions (box plots), Bayesian posteriors (violin plots), and scenario utilisation bands with P10–P90 ranges.
- **Panel D — Summary Scorecard**: One row per method with total duration, peak utilisation, months over capacity, and an auto-generated key insight.

## Requirements

- Python 3.10+
- numpy, scipy, pandas, pulp, plotly, openpyxl
