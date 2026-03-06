#!/usr/bin/env python3
"""
Capacity Planning Comparison — Dashboard Builder
=================================================
Imports the shared dataset, runs all five planning methods, and produces
a single self-contained HTML dashboard (comparison_dashboard.html) with
four interactive panels built in Plotly.

Run:
    pip install numpy scipy pandas pulp plotly
    python visualizer.py
"""

import json
import os
import sys
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# ── Import shared dataset & methods ──────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from shared_dataset import (
    projects,
    resource_capacities,
    historical_durations,
    PLANNING_HORIZON_MONTHS,
)
from methods import pert, rcpsp, bayesian, portfolio_opt, scenario_planning

# ── Colour palette (modern, accessible) ──────────────────────────────────
COLORS = {
    "pert":       "#3B82F6",  # blue
    "rcpsp":      "#10B981",  # emerald
    "bayesian":   "#8B5CF6",  # violet
    "portfolio":  "#F59E0B",  # amber
    "scenario":   "#EF4444",  # red
}
METHOD_LABELS = {
    "pert":       "PERT",
    "rcpsp":      "RCPSP",
    "bayesian":   "Bayesian",
    "portfolio":  "Portfolio Opt",
    "scenario":   "Scenario Planning",
}
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

WEEKS_PER_MONTH = 4.33


# ══════════════════════════════════════════════════════════════════════════
# Step 1 — Run all methods
# ══════════════════════════════════════════════════════════════════════════

print("Running PERT analysis …")
pert_results = pert.run(projects, resource_capacities, PLANNING_HORIZON_MONTHS)

print("Running RCPSP optimisation …")
rcpsp_results = rcpsp.run(projects, resource_capacities, PLANNING_HORIZON_MONTHS)

print("Running Bayesian estimation …")
bayesian_results = bayesian.run(
    projects, resource_capacities, historical_durations, PLANNING_HORIZON_MONTHS
)

print("Running Portfolio optimisation …")
portfolio_results = portfolio_opt.run(
    projects, resource_capacities, PLANNING_HORIZON_MONTHS
)

print("Running Scenario planning …")
scenario_results = scenario_planning.run(
    projects, resource_capacities, PLANNING_HORIZON_MONTHS
)

print("All methods complete. Building dashboard …\n")

# ══════════════════════════════════════════════════════════════════════════
# Step 2 — Build Plotly figures
# ══════════════════════════════════════════════════════════════════════════


def _make_panel_a():
    """Panel A — Timeline / Gantt View comparing all methods."""
    fig = go.Figure()

    project_names = [p["name"] for p in projects]
    # We'll create swim-lanes: one row per (method, project) combo
    # Group by method, offset y position

    method_timelines = {}

    # PERT timeline
    method_timelines["pert"] = []
    for name, start, dur, p10_dur, p90_dur in pert_results["timeline"]:
        method_timelines["pert"].append((name, start, dur, p10_dur, p90_dur))

    # RCPSP timeline
    method_timelines["rcpsp"] = []
    for name, start_m, end_m in rcpsp_results["project_schedule"]:
        dur = end_m - start_m
        method_timelines["rcpsp"].append((name, start_m, dur, dur, dur))

    # Bayesian timeline
    method_timelines["bayesian"] = []
    for name, start, dur, ci_lo, ci_hi in bayesian_results["timeline"]:
        method_timelines["bayesian"].append((name, start, dur, ci_lo, ci_hi))

    # Portfolio timeline (only selected projects)
    method_timelines["portfolio"] = []
    for name, start_m, end_m in portfolio_results["project_schedule"]:
        dur = end_m - start_m
        method_timelines["portfolio"].append((name, start_m, dur, dur, dur))

    # Scenario (likely)
    method_timelines["scenario"] = []
    for name, start, dur in scenario_results["timeline"]:
        method_timelines["scenario"].append((name, start, dur, dur, dur))

    methods_order = ["pert", "rcpsp", "bayesian", "portfolio", "scenario"]
    n_methods = len(methods_order)

    # Build y-axis positions: projects on integer positions, methods offset within
    y_ticks = []
    y_labels = []

    for proj_idx, proj_name in enumerate(project_names):
        base_y = proj_idx * (n_methods + 1)
        for m_idx, method in enumerate(methods_order):
            y_pos = base_y + m_idx
            y_ticks.append(y_pos)

            # Find this project in the method's timeline
            entry = None
            for e in method_timelines[method]:
                if e[0] == proj_name:
                    entry = e
                    break

            if entry is None:
                continue

            name, start, dur, lo_dur, hi_dur = entry
            color = COLORS[method]

            # Uncertainty band (lighter)
            if abs(hi_dur - lo_dur) > 0.1:
                fig.add_trace(go.Bar(
                    y=[y_pos],
                    x=[hi_dur - lo_dur],
                    base=[start + lo_dur],
                    orientation="h",
                    marker=dict(color=color, opacity=0.2),
                    showlegend=False,
                    hoverinfo="skip",
                ))

            # Main bar
            fig.add_trace(go.Bar(
                y=[y_pos],
                x=[dur],
                base=[start],
                orientation="h",
                marker=dict(color=color, opacity=0.85),
                name=METHOD_LABELS[method],
                legendgroup=method,
                showlegend=(proj_idx == 0),
                hovertemplate=(
                    f"<b>{name}</b> ({METHOD_LABELS[method]})<br>"
                    f"Start: Month {start}<br>"
                    f"Duration: {dur:.1f} months<br>"
                    "<extra></extra>"
                ),
            ))

    # Y-axis labels: project names centered on their group
    ytick_positions = []
    ytick_labels = []
    for proj_idx, proj_name in enumerate(project_names):
        base_y = proj_idx * (n_methods + 1)
        center_y = base_y + (n_methods - 1) / 2
        ytick_positions.append(center_y)
        ytick_labels.append(proj_name)

    fig.update_layout(
        barmode="overlay",
        yaxis=dict(
            tickvals=ytick_positions,
            ticktext=ytick_labels,
            autorange="reversed",
        ),
        xaxis=dict(
            title="Month",
            tickvals=list(range(12)),
            ticktext=MONTH_LABELS,
            range=[-0.5, 13],
        ),
        height=120 + len(project_names) * 110,
        margin=dict(l=220, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#FAFAFA",
    )

    return fig


def _make_panel_b():
    """Panel B — Monthly Capacity Heatmap (methods × months)."""
    methods_order = ["pert", "rcpsp", "bayesian", "portfolio", "scenario"]

    # Build a matrix: rows = methods, cols = months, value = avg utilisation %
    matrix = []
    hover_text = []

    all_utils = {
        "pert": pert_results["monthly_utilisation_pct"],
        "rcpsp": rcpsp_results["monthly_utilisation_pct"],
        "bayesian": bayesian_results["monthly_utilisation_pct"],
        "portfolio": portfolio_results["monthly_utilisation_pct"],
        "scenario": scenario_results["monthly_utilisation_pct"],
    }

    for method in methods_order:
        util_pct = all_utils[method]
        # Average across resource types for the heatmap colour
        avg_row = []
        hover_row = []
        for m in range(PLANNING_HORIZON_MONTHS):
            vals = [util_pct[r][m] for r in resource_capacities]
            avg = np.mean(vals)
            avg_row.append(avg)
            # Build hover with per-resource detail
            detail = "<br>".join(
                f"  {r}: {util_pct[r][m]:.0f}%"
                for r in resource_capacities
            )
            hover_row.append(
                f"<b>{METHOD_LABELS[method]}</b> — {MONTH_LABELS[m]}<br>"
                f"Avg utilisation: {avg:.0f}%<br>{detail}"
            )
        matrix.append(avg_row)
        hover_text.append(hover_row)

    # Colour scale: green (low) → yellow → red (over capacity)
    colorscale = [
        [0.0,  "#E8F5E9"],
        [0.4,  "#A5D6A7"],
        [0.6,  "#FFF176"],
        [0.8,  "#FF8A65"],
        [1.0,  "#E53935"],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=MONTH_LABELS,
        y=[METHOD_LABELS[m] for m in methods_order],
        hovertext=hover_text,
        hoverinfo="text",
        colorscale=colorscale,
        zmin=0,
        zmax=150,
        colorbar=dict(title="Util %", ticksuffix="%"),
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=140, r=40, t=30, b=40),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="#FAFAFA",
    )

    return fig


def _make_panel_c():
    """Panel C — Risk / Uncertainty Comparison."""
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=[
            "PERT: Completion Date Distributions",
            "Bayesian: Posterior Duration Distributions",
            "Scenario: Monthly Utilisation Bands",
        ],
        horizontal_spacing=0.08,
    )

    project_names = [p["name"] for p in projects]
    short_names = [n.split()[0] + " " + n.split()[-1] if len(n.split()) > 2
                   else n for n in project_names]

    # --- Sub-panel 1: PERT percentile box plots ---
    for i, res in enumerate(pert_results["project_results"]):
        pcts = res["percentiles"]
        fig.add_trace(go.Box(
            y=res["sim_durations"],
            name=short_names[i],
            marker_color=COLORS["pert"],
            boxpoints=False,
            showlegend=False,
        ), row=1, col=1)

    fig.update_yaxes(title_text="Duration (weeks)", row=1, col=1)

    # --- Sub-panel 2: Bayesian posterior violin/box ---
    for i, res in enumerate(bayesian_results["project_results"]):
        fig.add_trace(go.Violin(
            y=res["samples"],
            name=short_names[i],
            marker_color=COLORS["bayesian"],
            box_visible=True,
            meanline_visible=True,
            showlegend=False,
        ), row=1, col=2)

    fig.update_yaxes(title_text="Duration (weeks)", row=1, col=2)

    # --- Sub-panel 3: Scenario utilisation bands ---
    scenarios_data = scenario_results["scenarios"]
    months = list(range(PLANNING_HORIZON_MONTHS))

    for sc_name, sc_color in [("optimistic", "#10B981"), ("likely", "#F59E0B"), ("pessimistic", "#EF4444")]:
        sc = scenarios_data[sc_name]
        fig.add_trace(go.Scatter(
            x=MONTH_LABELS,
            y=sc["monthly_util_pct_p90"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ), row=1, col=3)
        fig.add_trace(go.Scatter(
            x=MONTH_LABELS,
            y=sc["monthly_util_pct_p10"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor=f"rgba({int(sc_color[1:3],16)},{int(sc_color[3:5],16)},{int(sc_color[5:7],16)},0.2)",
            showlegend=False,
            hoverinfo="skip",
        ), row=1, col=3)
        fig.add_trace(go.Scatter(
            x=MONTH_LABELS,
            y=sc["monthly_util_pct_median"],
            mode="lines+markers",
            name=sc["label"],
            line=dict(color=sc_color, width=2),
            marker=dict(size=5),
        ), row=1, col=3)

    # Add 100% capacity line
    fig.add_hline(y=100, line_dash="dash", line_color="gray",
                  annotation_text="100% capacity", row=1, col=3)

    fig.update_yaxes(title_text="Utilisation %", row=1, col=3)

    fig.update_layout(
        height=450,
        margin=dict(l=60, r=40, t=60, b=40),
        plot_bgcolor="#FAFAFA",
        legend=dict(orientation="h", yanchor="bottom", y=1.08, xanchor="center", x=0.85),
    )

    return fig


def _make_panel_d():
    """Panel D — Summary Scorecard Table."""
    methods_order = ["pert", "rcpsp", "bayesian", "portfolio", "scenario"]

    rows = []
    for method in methods_order:
        label = METHOD_LABELS[method]

        if method == "pert":
            # Total duration: sum of expected weeks across projects
            total_weeks = sum(r["expected_weeks"] for r in pert_results["project_results"])
            # Peak utilisation
            peak = max(
                max(pert_results["monthly_utilisation_pct"][r])
                for r in resource_capacities
            )
            # Months over capacity
            over = sum(
                1 for m in range(PLANNING_HORIZON_MONTHS)
                if any(pert_results["monthly_utilisation_pct"][r][m] > 100
                       for r in resource_capacities)
            )
            # Key insight: critical path
            longest = max(pert_results["project_results"],
                          key=lambda r: r["expected_weeks"])
            cp = " → ".join(longest["critical_path_names"])
            insight = f"Critical path: {longest['name']} ({cp})"

        elif method == "rcpsp":
            total_weeks = rcpsp_results["makespan"] * WEEKS_PER_MONTH
            peak = max(
                max(rcpsp_results["monthly_utilisation_pct"][r])
                for r in resource_capacities
            )
            over = sum(
                1 for m in range(PLANNING_HORIZON_MONTHS)
                if any(rcpsp_results["monthly_utilisation_pct"][r][m] > 100
                       for r in resource_capacities)
            )
            insight = f"Optimal makespan: {rcpsp_results['makespan']} months (ILP-solved)"

        elif method == "bayesian":
            total_weeks = sum(r["posterior_mean"] for r in bayesian_results["project_results"])
            peak = max(
                max(bayesian_results["monthly_utilisation_pct"][r])
                for r in resource_capacities
            )
            over = sum(
                1 for m in range(PLANNING_HORIZON_MONTHS)
                if any(bayesian_results["monthly_utilisation_pct"][r][m] > 100
                       for r in resource_capacities)
            )
            widest = max(bayesian_results["project_results"],
                         key=lambda r: r["ci_90"][1] - r["ci_90"][0])
            spread = widest["ci_90"][1] - widest["ci_90"][0]
            insight = f"Highest uncertainty: {widest['name']} (90% CI width: {spread:.0f} wks)"

        elif method == "portfolio":
            n_sel = len(portfolio_results["selected_projects"])
            n_def = len(portfolio_results["deferred_projects"])
            total_weeks = sum(
                (e - s) * WEEKS_PER_MONTH
                for _, s, e in portfolio_results["project_schedule"]
            )
            peak = max(
                max(portfolio_results["monthly_utilisation_pct"][r])
                for r in resource_capacities
            )
            over = sum(
                1 for m in range(PLANNING_HORIZON_MONTHS)
                if any(portfolio_results["monthly_utilisation_pct"][r][m] > 100
                       for r in resource_capacities)
            )
            val = portfolio_results["value_achieved"]
            val_d = portfolio_results["value_deferred"]
            deferred_names = ", ".join(portfolio_results["deferred_projects"]) or "None"
            insight = (
                f"Selected {n_sel}/{n_sel + n_def} projects "
                f"(value: {val:.0f} achieved, {val_d:.0f} deferred). "
                f"Deferred: {deferred_names}"
            )

        elif method == "scenario":
            likely = scenario_results["scenarios"]["likely"]
            total_weeks = sum(
                dur * WEEKS_PER_MONTH for _, _, dur in scenario_results["timeline"]
            )
            peak = max(likely["monthly_util_pct_median"])
            over = sum(
                1 for m in range(PLANNING_HORIZON_MONTHS)
                if likely["monthly_util_pct_median"][m] > 100
            )
            # Find month with highest breach probability in pessimistic
            pess = scenario_results["scenarios"]["pessimistic"]
            worst_month = int(np.argmax(pess["breach_probability"]))
            breach_p = pess["breach_probability"][worst_month]
            insight = (
                f"Pessimistic: {breach_p*100:.0f}% breach risk in "
                f"{MONTH_LABELS[worst_month]}; "
                f"unplanned work adds 15-25% load"
            )

        rows.append({
            "Method": label,
            "Total Duration (wks)": f"{total_weeks:.0f}",
            "Peak Utilisation": f"{peak:.0f}%",
            "Months Over Cap": str(over),
            "Key Insight": insight,
        })

    df = pd.DataFrame(rows)

    # Create a Plotly table
    header_colors = "#2D3748"
    row_colors = ["#F7FAFC", "#EDF2F7"]

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{c}</b>" for c in df.columns],
            fill_color=header_colors,
            font=dict(color="white", size=13),
            align="left",
            height=35,
        ),
        cells=dict(
            values=[df[c] for c in df.columns],
            fill_color=[
                [row_colors[i % 2] for i in range(len(df))]
                for _ in df.columns
            ],
            font=dict(size=12),
            align="left",
            height=30,
        ),
    )])

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=10, b=10),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════════
# Step 3 — Assemble HTML dashboard
# ══════════════════════════════════════════════════════════════════════════

def build_dashboard():
    """Combine all panels into a single self-contained HTML file."""

    panel_a = _make_panel_a()
    panel_b = _make_panel_b()
    panel_c = _make_panel_c()
    panel_d = _make_panel_d()

    # Convert each figure to an HTML div (no full HTML wrapper)
    div_a = panel_a.to_html(full_html=False, include_plotlyjs=False)
    div_b = panel_b.to_html(full_html=False, include_plotlyjs=False)
    div_c = panel_c.to_html(full_html=False, include_plotlyjs=False)
    div_d = panel_d.to_html(full_html=False, include_plotlyjs=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capacity Planning — Method Comparison Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #F0F4F8;
            color: #2D3748;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #1A365D 0%, #2B6CB0 100%);
            color: white;
            padding: 2rem 3rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
        .header p {{ font-size: 1rem; opacity: 0.85; max-width: 700px; margin: 0 auto; }}
        .container {{ max-width: 1400px; margin: 0 auto; padding: 1.5rem; }}
        .panel {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}
        .panel-header {{
            padding: 1.2rem 1.5rem 0.6rem;
            border-bottom: 1px solid #E2E8F0;
        }}
        .panel-header h2 {{
            font-size: 1.15rem;
            font-weight: 600;
            color: #1A365D;
            margin-bottom: 0.3rem;
        }}
        .panel-header p {{
            font-size: 0.88rem;
            color: #718096;
        }}
        .panel-body {{ padding: 0.5rem; }}
        .legend-bar {{
            display: flex;
            gap: 1.5rem;
            padding: 0.8rem 1.5rem;
            background: #F7FAFC;
            border-bottom: 1px solid #E2E8F0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.85rem;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 3px;
        }}
        .footer {{
            text-align: center;
            padding: 1.5rem;
            font-size: 0.8rem;
            color: #A0AEC0;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>Capacity Planning — Method Comparison Dashboard</h1>
    <p>
        Comparing five planning approaches for a 12-month portfolio of 7 projects
        across a ~20-person technical team. Each panel shows how different methods
        interpret the same underlying data.
    </p>
</div>

<div class="container">

    <!-- Legend -->
    <div class="panel">
        <div class="legend-bar">
            <div class="legend-item"><div class="legend-dot" style="background:#3B82F6"></div> PERT</div>
            <div class="legend-item"><div class="legend-dot" style="background:#10B981"></div> RCPSP</div>
            <div class="legend-item"><div class="legend-dot" style="background:#8B5CF6"></div> Bayesian</div>
            <div class="legend-item"><div class="legend-dot" style="background:#F59E0B"></div> Portfolio Opt</div>
            <div class="legend-item"><div class="legend-dot" style="background:#EF4444"></div> Scenario Planning</div>
        </div>
    </div>

    <!-- Panel A -->
    <div class="panel">
        <div class="panel-header">
            <h2>A. Timeline View (Gantt-Style)</h2>
            <p>
                Each project shows five horizontal bars — one per method — illustrating
                when the method thinks the project starts and how long it runs. Faded
                extensions indicate uncertainty ranges (P10–P90 for PERT, 90% credible
                interval for Bayesian). Compare how the optimiser (RCPSP) may shift
                projects later to respect resource caps, while PERT simply stacks them
                at their earliest dates.
            </p>
        </div>
        <div class="panel-body">{div_a}</div>
    </div>

    <!-- Panel B -->
    <div class="panel">
        <div class="panel-header">
            <h2>B. Monthly Capacity Heatmap</h2>
            <p>
                How heavily is the team loaded each month, according to each method?
                Cells are coloured by average utilisation across all resource types
                (data scientists, geoscientists, PMs). Green means comfortable headroom;
                yellow is tight; red means the method predicts over-capacity. Hover for
                per-role breakdowns.
            </p>
        </div>
        <div class="panel-body">{div_b}</div>
    </div>

    <!-- Panel C -->
    <div class="panel">
        <div class="panel-header">
            <h2>C. Risk &amp; Uncertainty Comparison</h2>
            <p>
                Each method quantifies uncertainty differently. <strong>PERT</strong>
                produces Monte Carlo duration distributions (box plots). <strong>Bayesian</strong>
                shows posterior-predictive distributions that incorporate historical data
                (violin plots). <strong>Scenario Planning</strong> shows utilisation bands
                (P10–P90) across three scenarios, with the dashed line marking 100% capacity.
            </p>
        </div>
        <div class="panel-body">{div_c}</div>
    </div>

    <!-- Panel D -->
    <div class="panel">
        <div class="panel-header">
            <h2>D. Summary Scorecard</h2>
            <p>
                A quick-reference table for leadership. Total duration is the sum of
                expected project weeks (not calendar time). Peak utilisation is the
                highest single-resource month. "Months Over Cap" counts months where
                at least one resource type exceeds 100%.
            </p>
        </div>
        <div class="panel-body">{div_d}</div>
    </div>

</div>

<div class="footer">
    Generated by <strong>visualizer.py</strong> · Data: shared_dataset.py · Methods: PERT, RCPSP, Bayesian, Portfolio Opt, Scenario Planning
</div>

</body>
</html>"""

    output_path = os.path.join(os.path.dirname(__file__), "comparison_dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard written to: {output_path}")
    print(f"File size: {os.path.getsize(output_path) / 1024:.0f} KB")
    return output_path


if __name__ == "__main__":
    build_dashboard()
