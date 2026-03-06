"""
Portfolio Optimization
=======================
Selects and sequences projects to maximise total business value under
resource constraints. Uses integer linear programming (PuLP) where:

- Binary decision: include each project or not
- Mandatory projects are forced in
- Monthly resource demand must not exceed capacity
- Objective: maximise Σ(value × selected)

Key outputs:
- Which projects are selected vs. deferred
- Scheduled timeline for selected projects
- Total portfolio value achieved vs. value left on table
- Monthly resource utilisation
"""

import pulp
import numpy as np
from collections import defaultdict

WEEKS_PER_MONTH = 4.33


def _pert_mean_weeks(o, m, p):
    return (o + 4 * m + p) / 6.0


# ── adapter / public API ──────────────────────────────────────────────────

def run(projects, resource_capacities, planning_horizon_months=12):
    """
    Run portfolio optimisation on the shared dataset.

    Decision variables:
        y[j] ∈ {0, 1}  — whether project j is selected
        s[j] ∈ Z+      — start month for project j (if selected)

    Constraints:
        - Mandatory projects: y[j] = 1
        - Dependencies: s[j] >= s[dep] + dur[dep]  (if both selected)
        - Monthly resource cap
        - All tasks finish within the planning horizon

    Returns
    -------
    dict with keys:
        selected_projects : list of project names chosen
        deferred_projects : list of project names left out
        value_achieved : float
        value_deferred : float
        project_schedule : list of (name, start_month, end_month)
        monthly_utilisation / monthly_utilisation_pct
    """
    horizon = planning_horizon_months
    n_proj = len(projects)
    resources = list(resource_capacities.keys())

    # Pre-compute project durations in months from the resource profile length
    proj_dur = []
    for p in projects:
        max_len = max(len(v) for v in p["resource_profile"].values())
        proj_dur.append(max_len)

    # ── ILP ───────────────────────────────────────────────────────────
    prob = pulp.LpProblem("PortfolioOpt", pulp.LpMaximize)

    # Binary: select project j?
    y = [pulp.LpVariable(f"y_{j}", cat="Binary") for j in range(n_proj)]

    # Start month for each project
    s = [
        pulp.LpVariable(f"s_{j}", lowBound=0, upBound=horizon - 1, cat="Integer")
        for j in range(n_proj)
    ]

    # Objective: maximise value of selected projects, weighted by probability
    prob += pulp.lpSum(
        projects[j]["value"] * projects[j]["probability"] * y[j]
        for j in range(n_proj)
    )

    proj_name_to_idx = {p["name"]: i for i, p in enumerate(projects)}

    for j in range(n_proj):
        p = projects[j]

        # Mandatory projects must be selected
        if p["mandatory"]:
            prob += y[j] == 1

        # Earliest start
        prob += s[j] >= p["earliest_start_month"]

        # Must finish within horizon (if selected)
        # s[j] + dur <= horizon  OR  y[j] = 0
        M = horizon + 1
        prob += s[j] + proj_dur[j] <= horizon + M * (1 - y[j])

        # Dependency constraints
        for dep_name in p["dependencies"]:
            if dep_name in proj_name_to_idx:
                dep_j = proj_name_to_idx[dep_name]
                # If both selected, enforce ordering
                prob += s[j] >= s[dep_j] + proj_dur[dep_j] - M * (2 - y[j] - y[dep_j])

    # Resource capacity per month using indicator variables
    # z[j,t] = 1 if project j is active in month t (and selected)
    z = {}
    for j in range(n_proj):
        for t in range(horizon):
            z[j, t] = pulp.LpVariable(f"z_{j}_{t}", cat="Binary")

    for j in range(n_proj):
        dur = proj_dur[j]
        for t in range(horizon):
            M = horizon + 1
            # z[j,t] can only be 1 if y[j] = 1
            prob += z[j, t] <= y[j]
            # z[j,t] = 1 only if s[j] <= t <= s[j]+dur-1
            prob += s[j] <= t + M * (1 - z[j, t])
            prob += t <= s[j] + dur - 1 + M * (1 - z[j, t])
        # If selected, exactly dur months active
        prob += pulp.lpSum(z[j, t] for t in range(horizon)) >= dur * y[j] - 0.5
        prob += pulp.lpSum(z[j, t] for t in range(horizon)) <= dur * y[j] + 0.5

    # Resource constraints
    for t in range(horizon):
        for resource in resources:
            demand = []
            for j in range(n_proj):
                p = projects[j]
                profile = p["resource_profile"].get(resource, [])
                # When active in month t, the demand depends on which month
                # of the project we're in. We approximate with the average demand.
                avg_demand = np.mean(profile) if profile else 0
                if avg_demand > 0:
                    demand.append(avg_demand * z[j, t])
            if demand:
                prob += pulp.lpSum(demand) <= resource_capacities[resource]

    # ── Solve ─────────────────────────────────────────────────────────
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
    prob.solve(solver)

    # ── Extract results ───────────────────────────────────────────────
    selected = []
    deferred = []
    project_schedule = []
    value_achieved = 0
    value_deferred = 0

    for j in range(n_proj):
        p = projects[j]
        if prob.status == 1 and y[j].varValue and y[j].varValue > 0.5:
            selected.append(p["name"])
            start_m = int(round(s[j].varValue))
            end_m = start_m + proj_dur[j]
            project_schedule.append((p["name"], start_m, end_m))
            value_achieved += p["value"] * p["probability"]
        else:
            deferred.append(p["name"])
            value_deferred += p["value"] * p["probability"]

    # If solver failed, use a greedy fallback
    if prob.status != 1:
        return _greedy_fallback(projects, resource_capacities, horizon)

    # Monthly utilisation
    monthly_util = {r: [0.0] * horizon for r in resources}
    for name, start_m, end_m in project_schedule:
        p = next(pp for pp in projects if pp["name"] == name)
        profile = p["resource_profile"]
        for resource, monthly_needs in profile.items():
            for offset, need in enumerate(monthly_needs):
                month = start_m + offset
                if 0 <= month < horizon:
                    monthly_util[resource][month] += need

    monthly_util_pct = {}
    for resource, months in monthly_util.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    return {
        "selected_projects": selected,
        "deferred_projects": deferred,
        "value_achieved": value_achieved,
        "value_deferred": value_deferred,
        "project_schedule": project_schedule,
        "monthly_utilisation": monthly_util,
        "monthly_utilisation_pct": monthly_util_pct,
    }


def _greedy_fallback(projects, resource_capacities, horizon):
    """Greedy selection: mandatory first, then by value/duration ratio."""
    resources = list(resource_capacities.keys())
    monthly_load = {r: [0.0] * horizon for r in resources}

    sorted_projects = sorted(
        projects,
        key=lambda p: (-p["mandatory"], -p["value"] * p["probability"])
    )

    selected = []
    deferred = []
    project_schedule = []
    value_achieved = 0
    value_deferred = 0

    for p in sorted_projects:
        dur = max(len(v) for v in p["resource_profile"].values())
        start = p["earliest_start_month"]

        # Check if it fits
        fits = True
        if start + dur > horizon:
            fits = False
        else:
            for resource, monthly_needs in p["resource_profile"].items():
                for offset, need in enumerate(monthly_needs):
                    month = start + offset
                    if month < horizon:
                        if monthly_load[resource][month] + need > resource_capacities[resource]:
                            fits = False
                            break
                if not fits:
                    break

        if fits:
            selected.append(p["name"])
            project_schedule.append((p["name"], start, start + dur))
            value_achieved += p["value"] * p["probability"]
            for resource, monthly_needs in p["resource_profile"].items():
                for offset, need in enumerate(monthly_needs):
                    month = start + offset
                    if month < horizon:
                        monthly_load[resource][month] += need
        else:
            deferred.append(p["name"])
            value_deferred += p["value"] * p["probability"]

    monthly_util_pct = {}
    for resource, months in monthly_load.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    return {
        "selected_projects": selected,
        "deferred_projects": deferred,
        "value_achieved": value_achieved,
        "value_deferred": value_deferred,
        "project_schedule": project_schedule,
        "monthly_utilisation": monthly_load,
        "monthly_utilisation_pct": monthly_util_pct,
    }
