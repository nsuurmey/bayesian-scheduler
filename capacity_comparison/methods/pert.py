"""
PERT — Program Evaluation and Review Technique
===============================================
Three-point estimation (optimistic / likely / pessimistic) using a Beta-PERT
distribution for each task. The critical path is identified via a forward/
backward pass on the task dependency graph, then Monte Carlo simulation
produces probability distributions for project and portfolio completion.

Key outputs:
- Expected duration per project (PERT-weighted mean)
- Critical path through each project's task network
- P10 / P50 / P85 / P95 completion-date distributions
- Monthly resource utilisation profile
"""

import numpy as np
from scipy import stats

# ── helpers ───────────────────────────────────────────────────────────────

def _pert_mean(o, m, p):
    """PERT weighted mean: (O + 4M + P) / 6"""
    return (o + 4 * m + p) / 6.0


def _pert_var(o, p):
    """PERT variance: ((P - O) / 6)^2"""
    return ((p - o) / 6.0) ** 2


def _beta_pert_sample(o, m, p, size=1):
    """Draw samples from a Beta-PERT distribution."""
    mu = _pert_mean(o, m, p)
    if p == o:
        return np.full(size, mu)
    # shape parameters for the modified-PERT beta
    lam = 4  # standard PERT lambda
    alpha = 1 + lam * (m - o) / (p - o)
    beta = 1 + lam * (p - m) / (p - o)
    # scipy beta on [0,1] -> rescale to [o, p]
    samples = stats.beta.rvs(alpha, beta, size=size)
    return o + samples * (p - o)


def _forward_backward_pass(tasks):
    """
    Classic CPM forward + backward pass.
    Returns dict  task_id -> {ES, EF, LS, LF, slack, pert_mean}
    using PERT-weighted means as deterministic durations.
    """
    task_map = {t["id"]: t for t in tasks}
    info = {}
    for t in tasks:
        info[t["id"]] = {
            "duration": _pert_mean(t["optimistic"], t["likely"], t["pessimistic"]),
            "predecessors": t["predecessors"],
        }

    # Forward pass — earliest start / finish
    computed = set()
    while len(computed) < len(tasks):
        for tid, t in info.items():
            if tid in computed:
                continue
            preds = t["predecessors"]
            if all(p in computed for p in preds):
                es = max((info[p]["EF"] for p in preds), default=0)
                t["ES"] = es
                t["EF"] = es + t["duration"]
                computed.add(tid)

    project_ef = max(t["EF"] for t in info.values())

    # Backward pass — latest start / finish
    for t in info.values():
        t["LF"] = project_ef  # will be tightened below

    reverse_order = sorted(info.keys(), key=lambda tid: -info[tid]["EF"])
    # Build successors map
    successors = {tid: [] for tid in info}
    for tid, t in info.items():
        for p in t["predecessors"]:
            successors[p].append(tid)

    for tid in reverse_order:
        t = info[tid]
        if successors[tid]:
            t["LF"] = min(info[s]["LS"] for s in successors[tid])
        else:
            t["LF"] = project_ef
        t["LS"] = t["LF"] - t["duration"]
        t["slack"] = t["LS"] - t["ES"]

    # Identify critical path (slack ≈ 0)
    critical = [tid for tid, t in info.items() if abs(t["slack"]) < 1e-6]
    # Sort critical tasks by ES
    critical.sort(key=lambda tid: info[tid]["ES"])

    return info, critical, project_ef


def _monte_carlo_project(tasks, n_sim=5000):
    """
    Monte Carlo simulation of a single project's task network.
    Returns array of simulated project durations (weeks).
    """
    task_map = {t["id"]: t for t in tasks}
    durations = np.zeros((n_sim, len(tasks)))
    for i, t in enumerate(tasks):
        durations[:, i] = _beta_pert_sample(
            t["optimistic"], t["likely"], t["pessimistic"], size=n_sim
        )

    # Simulate forward pass for each trial
    finish_times = np.zeros((n_sim, len(tasks)))
    id_to_idx = {t["id"]: i for i, t in enumerate(tasks)}

    # Topological order (simple: iterate until all resolved)
    resolved = [False] * len(tasks)
    order = []
    while len(order) < len(tasks):
        for i, t in enumerate(tasks):
            if resolved[i]:
                continue
            preds = t["predecessors"]
            if all(resolved[id_to_idx[p]] for p in preds):
                order.append(i)
                resolved[i] = True

    for sim in range(n_sim):
        for i in order:
            t = tasks[i]
            pred_finish = [finish_times[sim, id_to_idx[p]] for p in t["predecessors"]]
            es = max(pred_finish) if pred_finish else 0
            finish_times[sim, i] = es + durations[sim, i]

    project_durations = finish_times.max(axis=1)
    return project_durations


# ── adapter / public API ──────────────────────────────────────────────────

def run(projects, resource_capacities, planning_horizon_months=12, n_sim=5000):
    """
    Run PERT analysis on the shared dataset.

    Returns
    -------
    dict with keys:
        project_results : list of per-project dicts
            Each contains: name, expected_weeks, critical_path,
            percentiles {P10, P50, P85, P95}, sim_durations (array)
        timeline : list of (project_name, start_month, duration_months, p10_dur, p90_dur)
        monthly_utilisation : dict[resource] -> list[float] length 12
    """
    weeks_per_month = 4.33
    results = []

    for proj in projects:
        tasks = proj["tasks"]

        # Deterministic CPM
        info, critical_path, expected_ef = _forward_backward_pass(tasks)

        # Monte Carlo
        sim_durations = _monte_carlo_project(tasks, n_sim=n_sim)
        pcts = np.percentile(sim_durations, [10, 50, 85, 95])

        results.append({
            "name": proj["name"],
            "expected_weeks": expected_ef,
            "critical_path": critical_path,
            "critical_path_names": [
                next(t["name"] for t in tasks if t["id"] == tid)
                for tid in critical_path
            ],
            "percentiles": {
                "P10": float(pcts[0]),
                "P50": float(pcts[1]),
                "P85": float(pcts[2]),
                "P95": float(pcts[3]),
            },
            "sim_durations": sim_durations,
        })

    # Build timeline: use earliest_start_month + PERT mean duration
    timeline = []
    for proj, res in zip(projects, results):
        start = proj["earliest_start_month"]
        dur_months = res["expected_weeks"] / weeks_per_month
        p10_dur = res["percentiles"]["P10"] / weeks_per_month
        p90_dur = res["percentiles"]["P95"] / weeks_per_month
        timeline.append((proj["name"], start, dur_months, p10_dur, p90_dur))

    # Monthly utilisation estimate (spread resource_profile across months)
    monthly_util = {r: [0.0] * planning_horizon_months for r in resource_capacities}
    for proj in projects:
        start = proj["earliest_start_month"]
        profile = proj["resource_profile"]
        for resource, monthly_needs in profile.items():
            for offset, need in enumerate(monthly_needs):
                month = start + offset
                if month < planning_horizon_months:
                    monthly_util[resource][month] += need

    # Convert to utilisation %
    monthly_util_pct = {}
    for resource, months in monthly_util.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    return {
        "project_results": results,
        "timeline": timeline,
        "monthly_utilisation": monthly_util,
        "monthly_utilisation_pct": monthly_util_pct,
    }
