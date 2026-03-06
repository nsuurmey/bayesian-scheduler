"""
RCPSP — Resource-Constrained Project Scheduling Problem
========================================================
Uses integer linear programming (via PuLP) to find an optimal schedule that
respects hard resource caps each month. Tasks are assigned to time slots and
the solver minimises the overall makespan (latest finish across all tasks).

Key outputs:
- Optimal start/finish month for every task
- Per-project scheduled start/end months
- Monthly resource utilisation under the optimal plan
- Total makespan
"""

import pulp
import numpy as np
from collections import defaultdict

# ── helpers ───────────────────────────────────────────────────────────────

def _pert_mean_weeks(o, m, p):
    return (o + 4 * m + p) / 6.0

WEEKS_PER_MONTH = 4.33


def _task_duration_months(task):
    """Convert a task's PERT mean duration from weeks to whole months (ceiling)."""
    weeks = _pert_mean_weeks(task["optimistic"], task["likely"], task["pessimistic"])
    return max(1, int(np.ceil(weeks / WEEKS_PER_MONTH)))


# ── adapter / public API ──────────────────────────────────────────────────

def run(projects, resource_capacities, planning_horizon_months=12):
    """
    Solve the RCPSP for the full project portfolio.

    Each task is modelled as occupying a contiguous block of months.
    Decision variables: start_month for each task (integer).
    Constraints:
        - Precedence within each project
        - Cross-project dependencies (earliest_start_month)
        - Resource capacity each month
    Objective: minimise makespan (latest task finish).

    Returns
    -------
    dict with keys:
        task_schedule : list of dicts {project, task_id, task_name, start, end}
        project_schedule : list of (name, start_month, end_month)
        monthly_utilisation : dict[resource] -> list[float] length horizon
        monthly_utilisation_pct : same, in %
        makespan : int (months)
    """
    horizon = planning_horizon_months
    all_tasks = []  # (project_name, task_dict, duration_months)
    task_id_global = {}  # (proj_name, task_id) -> index in all_tasks

    # Build a mapping from project name to its earliest start
    proj_earliest = {p["name"]: p["earliest_start_month"] for p in projects}

    for proj in projects:
        for task in proj["tasks"]:
            idx = len(all_tasks)
            dur = _task_duration_months(task)
            all_tasks.append((proj["name"], task, dur))
            task_id_global[(proj["name"], task["id"])] = idx

    n_tasks = len(all_tasks)

    # ── ILP formulation ───────────────────────────────────────────────
    prob = pulp.LpProblem("RCPSP", pulp.LpMinimize)

    # Decision variables: start month for each task
    starts = [
        pulp.LpVariable(f"s_{i}", lowBound=0, upBound=horizon - 1, cat="Integer")
        for i in range(n_tasks)
    ]

    # Makespan variable
    makespan = pulp.LpVariable("makespan", lowBound=0, cat="Integer")
    prob += makespan  # objective: minimise

    # Binary "active" indicators:  x[i][t] = 1 if task i is running in month t
    x = {}
    for i in range(n_tasks):
        dur = all_tasks[i][2]
        for t in range(horizon):
            x[i, t] = pulp.LpVariable(f"x_{i}_{t}", cat="Binary")

    for i in range(n_tasks):
        proj_name, task, dur = all_tasks[i]

        # Link x to starts: task i runs in months [starts[i], starts[i]+dur-1]
        for t in range(horizon):
            # x[i,t] = 1 iff starts[i] <= t <= starts[i]+dur-1
            # Linearise with big-M style constraints
            M = horizon + 1
            # x[i,t] <= 1 if t >= starts[i]  =>  starts[i] <= t + M*(1 - x[i,t])
            prob += starts[i] <= t + M * (1 - x[i, t])
            # x[i,t] <= 1 if t < starts[i] + dur  =>  t <= starts[i] + dur - 1 + M*(1-x[i,t])
            prob += t <= starts[i] + dur - 1 + M * (1 - x[i, t])

        # Exactly dur months active
        prob += pulp.lpSum(x[i, t] for t in range(horizon)) == dur

        # Makespan: finish of every task <= makespan
        prob += starts[i] + dur <= makespan

        # Earliest start from project-level constraint
        prob += starts[i] >= proj_earliest[proj_name]

        # Precedence within project
        for pred_id in task["predecessors"]:
            pred_idx = task_id_global[(proj_name, pred_id)]
            pred_dur = all_tasks[pred_idx][2]
            prob += starts[i] >= starts[pred_idx] + pred_dur

    # Resource capacity constraints per month
    resources = list(resource_capacities.keys())
    for t in range(horizon):
        for resource in resources:
            cap = resource_capacities[resource]
            demand = []
            for i in range(n_tasks):
                _, task, _ = all_tasks[i]
                need = task.get("resources", {}).get(resource, 0)
                if need > 0:
                    demand.append(need * x[i, t])
            if demand:
                prob += pulp.lpSum(demand) <= cap

    # ── Solve ─────────────────────────────────────────────────────────
    solver = pulp.PULP_CBC_CMD(msg=0, timeLimit=30)
    prob.solve(solver)

    if prob.status != 1:
        # If infeasible or timeout, relax by extending horizon
        return _fallback_heuristic(projects, resource_capacities, planning_horizon_months)

    # ── Extract results ───────────────────────────────────────────────
    task_schedule = []
    proj_spans = defaultdict(lambda: [horizon, 0])  # [min_start, max_end]

    for i in range(n_tasks):
        proj_name, task, dur = all_tasks[i]
        s = int(round(starts[i].varValue))
        e = s + dur
        task_schedule.append({
            "project": proj_name,
            "task_id": task["id"],
            "task_name": task["name"],
            "start": s,
            "end": e,
        })
        proj_spans[proj_name][0] = min(proj_spans[proj_name][0], s)
        proj_spans[proj_name][1] = max(proj_spans[proj_name][1], e)

    project_schedule = [
        (name, span[0], span[1]) for name, span in proj_spans.items()
    ]

    # Monthly resource utilisation
    monthly_util = {r: [0.0] * horizon for r in resources}
    for i in range(n_tasks):
        _, task, dur = all_tasks[i]
        s = int(round(starts[i].varValue))
        for t_off in range(dur):
            t = s + t_off
            if t < horizon:
                for resource in resources:
                    need = task.get("resources", {}).get(resource, 0)
                    monthly_util[resource][t] += need

    monthly_util_pct = {}
    for resource, months in monthly_util.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    ms = int(round(makespan.varValue))

    return {
        "task_schedule": task_schedule,
        "project_schedule": project_schedule,
        "monthly_utilisation": monthly_util,
        "monthly_utilisation_pct": monthly_util_pct,
        "makespan": ms,
    }


def _fallback_heuristic(projects, resource_capacities, horizon):
    """
    Simple priority-based heuristic if the ILP is infeasible or times out.
    Schedule tasks greedily in topological order, respecting resource caps.
    """
    WEEKS_PER_M = 4.33
    resources = list(resource_capacities.keys())
    monthly_load = {r: [0.0] * (horizon + 12) for r in resources}  # extra buffer

    proj_earliest = {p["name"]: p["earliest_start_month"] for p in projects}
    task_schedule = []
    proj_spans = defaultdict(lambda: [horizon + 12, 0])
    task_finish = {}  # (proj_name, task_id) -> finish month

    # Sort projects by value descending (mandatory first)
    sorted_projects = sorted(projects, key=lambda p: (-p["mandatory"], -p["value"]))

    for proj in sorted_projects:
        proj_name = proj["name"]
        earliest = proj_earliest[proj_name]

        # Topological sort of tasks within project
        tasks = proj["tasks"]
        task_map = {t["id"]: t for t in tasks}
        resolved = set()
        order = []
        while len(order) < len(tasks):
            for t in tasks:
                if t["id"] in resolved:
                    continue
                if all(p in resolved for p in t["predecessors"]):
                    order.append(t)
                    resolved.add(t["id"])

        for task in order:
            dur = max(1, int(np.ceil(
                _pert_mean_weeks(task["optimistic"], task["likely"], task["pessimistic"]) / WEEKS_PER_M
            )))
            # Earliest start: max of project earliest, predecessor finishes
            es = earliest
            for pred_id in task["predecessors"]:
                es = max(es, task_finish.get((proj_name, pred_id), es))

            # Find first feasible start where resources fit
            for candidate in range(es, horizon + 6):
                feasible = True
                for t_off in range(dur):
                    t = candidate + t_off
                    for resource in resources:
                        need = task.get("resources", {}).get(resource, 0)
                        if monthly_load[resource][t] + need > resource_capacities[resource]:
                            feasible = False
                            break
                    if not feasible:
                        break
                if feasible:
                    # Place task
                    for t_off in range(dur):
                        t = candidate + t_off
                        for resource in resources:
                            need = task.get("resources", {}).get(resource, 0)
                            monthly_load[resource][t] += need
                    task_finish[(proj_name, task["id"])] = candidate + dur
                    task_schedule.append({
                        "project": proj_name,
                        "task_id": task["id"],
                        "task_name": task["name"],
                        "start": candidate,
                        "end": candidate + dur,
                    })
                    proj_spans[proj_name][0] = min(proj_spans[proj_name][0], candidate)
                    proj_spans[proj_name][1] = max(proj_spans[proj_name][1], candidate + dur)
                    break

    project_schedule = [(name, span[0], span[1]) for name, span in proj_spans.items()]

    # Trim utilisation to horizon
    monthly_util = {r: months[:horizon] for r, months in monthly_load.items()}
    monthly_util_pct = {}
    for resource, months in monthly_util.items():
        cap = resource_capacities[resource]
        monthly_util_pct[resource] = [m / cap * 100 for m in months]

    makespan = max((span[1] for span in proj_spans.values()), default=0)

    return {
        "task_schedule": task_schedule,
        "project_schedule": project_schedule,
        "monthly_utilisation": monthly_util,
        "monthly_utilisation_pct": monthly_util_pct,
        "makespan": makespan,
    }
