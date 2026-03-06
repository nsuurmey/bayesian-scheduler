"""
Scenario Planning / What-If Analysis
======================================
Runs Monte Carlo simulations under three scenarios (optimistic / likely /
pessimistic), each with different assumptions about:
- Task duration multipliers
- Unplanned work injection (% of capacity consumed by ad-hoc requests)
- Probability that uncertain projects actually happen

Also models "unplanned work" as a random drain on capacity each month,
which is a reality most planning methods ignore.

Key outputs:
- Utilisation bands (P10-P90) for each scenario
- Probability of capacity breach per month
- Comparison of optimistic / likely / pessimistic total portfolio duration
- Monthly utilisation profiles for each scenario
"""

import numpy as np
from scipy import stats

WEEKS_PER_MONTH = 4.33

# ── Scenario definitions ─────────────────────────────────────────────────

SCENARIOS = {
    "optimistic": {
        "duration_key": "duration_optimistic_weeks",
        "unplanned_work_pct": 0.05,   # 5% capacity eaten by unplanned work
        "probability_threshold": 0.5,  # include projects with P >= 50%
        "label": "Optimistic",
    },
    "likely": {
        "duration_key": "duration_likely_weeks",
        "unplanned_work_pct": 0.15,    # 15% capacity eaten by unplanned work
        "probability_threshold": 0.75,  # include projects with P >= 75%
        "label": "Likely",
    },
    "pessimistic": {
        "duration_key": "duration_pessimistic_weeks",
        "unplanned_work_pct": 0.25,    # 25% capacity eaten by unplanned work
        "probability_threshold": 0.0,   # include ALL projects
        "label": "Pessimistic",
    },
}


def _simulate_scenario(projects, resource_capacities, scenario_cfg,
                        horizon=12, n_sim=3000):
    """
    Monte Carlo simulation for one scenario.

    For each simulation run:
    1. Decide which uncertain projects materialise (Bernoulli on probability).
    2. Sample project durations from a triangular distribution around the
       scenario's target duration.
    3. Add random unplanned work each month.
    4. Compute monthly utilisation.

    Returns per-month utilisation arrays (n_sim × horizon) per resource.
    """
    resources = list(resource_capacities.keys())
    dur_key = scenario_cfg["duration_key"]
    unplanned_pct = scenario_cfg["unplanned_work_pct"]
    p_threshold = scenario_cfg["probability_threshold"]

    # Pre-filter projects by probability threshold
    eligible = [p for p in projects if p["probability"] >= p_threshold]

    # Result array: utilisation per resource per month per sim
    util = {r: np.zeros((n_sim, horizon)) for r in resources}

    for sim in range(n_sim):
        for proj in eligible:
            # Bernoulli: does this uncertain project actually happen?
            if proj["probability"] < 1.0:
                if np.random.random() > proj["probability"]:
                    continue

            # Sample duration (triangular around the scenario target)
            target_weeks = proj[dur_key]
            lo = target_weeks * 0.85
            hi = target_weeks * 1.15
            sampled_weeks = np.random.triangular(lo, target_weeks, hi)
            sampled_months = max(1, int(np.ceil(sampled_weeks / WEEKS_PER_MONTH)))

            start = proj["earliest_start_month"]
            profile = proj["resource_profile"]

            # Scale profile to sampled duration
            original_months = max(len(v) for v in profile.values())
            if original_months == 0:
                continue
            scale = sampled_months / original_months

            for resource, monthly_needs in profile.items():
                for offset, need in enumerate(monthly_needs):
                    scaled_offset = int(round(offset * scale))
                    month = start + scaled_offset
                    if 0 <= month < horizon:
                        util[resource][sim, month] += need

        # Add unplanned work (random, each month independently)
        for resource in resources:
            cap = resource_capacities[resource]
            unplanned = np.random.uniform(
                unplanned_pct * 0.5 * cap,
                unplanned_pct * 1.5 * cap,
                size=horizon
            )
            util[resource][sim, :] += unplanned

    return util


# ── adapter / public API ──────────────────────────────────────────────────

def run(projects, resource_capacities, planning_horizon_months=12, n_sim=3000):
    """
    Run scenario planning / what-if analysis.

    Returns
    -------
    dict with keys per scenario (optimistic/likely/pessimistic), each containing:
        label, monthly_util_median, monthly_util_p10, monthly_util_p90,
        monthly_util_pct (median), breach_probability (per month),
        timeline (project-level)

    Also top-level:
        scenarios : dict of the above
        timeline_likely : list of (name, start, duration_months) for the likely scenario
        monthly_utilisation / monthly_utilisation_pct : for the likely scenario
    """
    results = {}

    for scenario_name, cfg in SCENARIOS.items():
        util = _simulate_scenario(
            projects, resource_capacities, cfg,
            horizon=planning_horizon_months, n_sim=n_sim
        )

        resources = list(resource_capacities.keys())

        # Aggregate across resources: total headcount utilisation
        total_util = np.zeros((n_sim, planning_horizon_months))
        total_cap = sum(resource_capacities.values())
        for r in resources:
            total_util += util[r]

        # Percentiles
        median = np.median(total_util, axis=0)
        p10 = np.percentile(total_util, 10, axis=0)
        p90 = np.percentile(total_util, 90, axis=0)

        # As percentage of total capacity
        median_pct = median / total_cap * 100
        p10_pct = p10 / total_cap * 100
        p90_pct = p90 / total_cap * 100

        # Breach probability: fraction of sims where utilisation > total_cap
        breach_prob = (total_util > total_cap).mean(axis=0)

        # Per-resource utilisation (median)
        resource_util = {}
        resource_util_pct = {}
        for r in resources:
            med_r = np.median(util[r], axis=0)
            resource_util[r] = med_r.tolist()
            resource_util_pct[r] = (med_r / resource_capacities[r] * 100).tolist()

        # Scenario-level timeline (deterministic for display)
        dur_key = cfg["duration_key"]
        p_threshold = cfg["probability_threshold"]
        timeline = []
        for proj in projects:
            if proj["probability"] >= p_threshold:
                dur_weeks = proj[dur_key]
                dur_months = dur_weeks / WEEKS_PER_MONTH
                timeline.append((proj["name"], proj["earliest_start_month"], dur_months))

        results[scenario_name] = {
            "label": cfg["label"],
            "monthly_util_median": median.tolist(),
            "monthly_util_p10": p10.tolist(),
            "monthly_util_p90": p90.tolist(),
            "monthly_util_pct_median": median_pct.tolist(),
            "monthly_util_pct_p10": p10_pct.tolist(),
            "monthly_util_pct_p90": p90_pct.tolist(),
            "breach_probability": breach_prob.tolist(),
            "resource_util": resource_util,
            "resource_util_pct": resource_util_pct,
            "timeline": timeline,
        }

    # For the unified comparison interface, expose the "likely" scenario
    likely = results["likely"]
    return {
        "scenarios": results,
        "timeline": likely["timeline"],
        "monthly_utilisation": likely["resource_util"],
        "monthly_utilisation_pct": likely["resource_util_pct"],
    }
