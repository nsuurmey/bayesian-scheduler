#!/usr/bin/env python3
"""
Spreadsheet Loader for Capacity Planning
==========================================
Reads a portfolio_template.xlsx (or any .xlsx following the same schema)
and produces the same data structures as shared_dataset.py, so the
visualizer can consume either source interchangeably.

Supports:
  - .xlsx files (via openpyxl)
  - .csv files (reads Projects.csv, Tasks.csv, Config.csv from a directory)

Usage as a module:
    from load_spreadsheet import load
    data = load("portfolio_template.xlsx")
    # data.projects, data.resource_capacities, data.historical_durations, etc.

Usage from command line (generates dashboard from spreadsheet):
    python load_spreadsheet.py portfolio_template.xlsx
"""

import os
import sys
import math
from dataclasses import dataclass, field
import pandas as pd


@dataclass
class PortfolioData:
    """Mirror of shared_dataset.py's top-level objects."""
    projects: list = field(default_factory=list)
    resource_capacities: dict = field(default_factory=dict)
    historical_durations: dict = field(default_factory=dict)
    planning_horizon_months: int = 12


# ── Resource profile column mapping ──────────────────────────────────────
# Maps role name -> column prefix in the Projects sheet
ROLE_COLUMN_PREFIX = {
    "data_scientists": "ds_month_",
    "geoscientists": "geo_month_",
    "project_managers": "pm_month_",
}
MAX_PROFILE_MONTHS = 6  # columns ds_month_1 through ds_month_6


def _parse_comma_list(val):
    """Parse a comma-separated string into a list of stripped strings."""
    if pd.isna(val) or str(val).strip() == "":
        return []
    return [s.strip() for s in str(val).split(",") if s.strip()]


def _parse_bool(val):
    """Parse yes/no/true/false/1/0 into a bool."""
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in ("yes", "true", "1")


def _safe_int(val, default=0):
    if pd.isna(val) or str(val).strip() == "":
        return default
    return int(float(val))


def _safe_float(val, default=0.0):
    if pd.isna(val) or str(val).strip() == "":
        return default
    return float(val)


# ── Excel loader ─────────────────────────────────────────────────────────

def load(path):
    """
    Load portfolio data from an Excel workbook.

    Expects three sheets:
        Projects  — one row per project
        Tasks     — one row per task, linked by project_name
        Config    — team capacity and historical durations

    Returns a PortfolioData instance.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Spreadsheet not found: {path}")

    df_proj = pd.read_excel(path, sheet_name="Projects")
    df_tasks = pd.read_excel(path, sheet_name="Tasks")
    df_config = pd.read_excel(path, sheet_name="Config", header=None)

    data = PortfolioData()

    # ── Parse Config sheet ────────────────────────────────────────────
    config_values = {}
    section = None
    for _, row in df_config.iterrows():
        cell_0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        cell_1 = row.iloc[1] if len(row) > 1 else None

        if cell_0 == "TEAM CAPACITY":
            section = "capacity"
            continue
        elif cell_0 == "PLANNING":
            section = "planning"
            continue
        elif cell_0 == "HISTORICAL DURATIONS (weeks)":
            section = "historical"
            continue
        elif cell_0 in ("Role", "Category", ""):
            continue

        if section == "capacity" and cell_0:
            data.resource_capacities[cell_0] = _safe_int(cell_1, 1)
        elif section == "planning" and cell_0 == "horizon_months":
            data.planning_horizon_months = _safe_int(cell_1, 12)
        elif section == "historical" and cell_0:
            durations = [float(x) for x in str(cell_1).split(",") if x.strip()]
            data.historical_durations[cell_0] = durations

    # Fallback defaults if Config sheet is sparse
    if not data.resource_capacities:
        data.resource_capacities = {
            "data_scientists": 8, "geoscientists": 5, "project_managers": 4
        }

    # ── Parse Tasks sheet ─────────────────────────────────────────────
    # Group tasks by project_name
    tasks_by_project = {}
    for _, row in df_tasks.iterrows():
        proj_name = str(row["project_name"]).strip()
        if not proj_name or proj_name == "nan":
            continue

        resources = {}
        for role in data.resource_capacities:
            if role in df_tasks.columns:
                val = _safe_int(row.get(role, 0))
                if val > 0:
                    resources[role] = val

        task = {
            "id": str(row["task_id"]).strip(),
            "name": str(row["task_name"]).strip(),
            "optimistic": _safe_float(row["optimistic_weeks"]),
            "likely": _safe_float(row["likely_weeks"]),
            "pessimistic": _safe_float(row["pessimistic_weeks"]),
            "predecessors": _parse_comma_list(row.get("predecessors", "")),
            "resources": resources,
        }

        tasks_by_project.setdefault(proj_name, []).append(task)

    # ── Parse Projects sheet ──────────────────────────────────────────
    for _, row in df_proj.iterrows():
        name = str(row["project_name"]).strip()
        if not name or name == "nan":
            continue

        # Build resource profile from ds_month_1..6, geo_month_1..6, pm_month_1..6
        resource_profile = {}
        for role, prefix in ROLE_COLUMN_PREFIX.items():
            monthly = []
            for m in range(1, MAX_PROFILE_MONTHS + 1):
                col = f"{prefix}{m}"
                if col in df_proj.columns:
                    val = _safe_int(row.get(col, 0))
                    if val > 0 or monthly:  # keep trailing zeros within the profile
                        monthly.append(val)
                    elif not monthly and val == 0:
                        # Only start the list once we see nonzero or the project has started
                        pass
                else:
                    break
            # Trim trailing zeros
            while monthly and monthly[-1] == 0:
                monthly.pop()
            if monthly:
                resource_profile[role] = monthly

        # Ensure all roles present in resource_capacities appear
        for role in data.resource_capacities:
            if role not in resource_profile:
                resource_profile[role] = []

        project = {
            "name": name,
            "type": str(row.get("type", "medium")).strip().lower(),
            "value": _safe_float(row.get("value", 50)),
            "mandatory": _parse_bool(row.get("mandatory", True)),
            "dependencies": _parse_comma_list(row.get("dependencies", "")),
            "duration_optimistic_weeks": _safe_float(row["optimistic_weeks"]),
            "duration_likely_weeks": _safe_float(row["likely_weeks"]),
            "duration_pessimistic_weeks": _safe_float(row["pessimistic_weeks"]),
            "resource_profile": resource_profile,
            "earliest_start_month": _safe_int(row.get("earliest_start_month", 0)),
            "probability": _safe_float(row.get("probability", 1.0)),
            "tasks": tasks_by_project.get(name, []),
        }

        # Validate: project needs at least one task
        if not project["tasks"]:
            print(f"  Warning: '{name}' has no tasks in the Tasks sheet — "
                  f"auto-generating a single task from project-level estimates.")
            project["tasks"] = [{
                "id": name[:2].upper() + "1",
                "name": name,
                "optimistic": project["duration_optimistic_weeks"],
                "likely": project["duration_likely_weeks"],
                "pessimistic": project["duration_pessimistic_weeks"],
                "predecessors": [],
                "resources": {
                    role: max(vals) if vals else 0
                    for role, vals in resource_profile.items()
                },
            }]

        data.projects.append(project)

    print(f"Loaded {len(data.projects)} projects with "
          f"{sum(len(p['tasks']) for p in data.projects)} tasks total.")
    return data


# ── CLI: load spreadsheet → run visualizer ────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python load_spreadsheet.py <path-to-xlsx>")
        print("       Loads the spreadsheet and runs the comparison dashboard.")
        sys.exit(1)

    xlsx_path = sys.argv[1]
    portfolio = load(xlsx_path)

    # Monkey-patch shared_dataset so visualizer picks up the loaded data
    import shared_dataset
    shared_dataset.projects = portfolio.projects
    shared_dataset.resource_capacities = portfolio.resource_capacities
    shared_dataset.historical_durations = portfolio.historical_durations
    shared_dataset.PLANNING_HORIZON_MONTHS = portfolio.planning_horizon_months

    # Run the visualizer
    from visualizer import build_dashboard
    build_dashboard()
