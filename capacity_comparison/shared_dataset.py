"""
Shared Dataset for Capacity Planning Comparison
================================================
A single source-of-truth dataset representing an annual portfolio for a
~20-person technical team (data scientists, geoscientists, project managers)
working on 7 major projects over 12 months.

All five planning methods draw from this dataset. Each method's adapter
translates these structures into the format the method expects.
"""

# ---------------------------------------------------------------------------
# Team capacity (headcount available each month)
# ---------------------------------------------------------------------------
resource_capacities = {
    "data_scientists": 8,
    "geoscientists": 5,
    "project_managers": 4,
}

PLANNING_HORIZON_MONTHS = 12
WEEKS_PER_MONTH = 4.33  # average

# ---------------------------------------------------------------------------
# Historical duration data for Bayesian priors (weeks)
# ---------------------------------------------------------------------------
historical_durations = {
    "small":  [6, 8, 7, 9, 7, 8, 10, 6],
    "medium": [12, 15, 14, 16, 13, 15],
    "large":  [20, 24, 22, 26, 23, 28, 21],
}

# ---------------------------------------------------------------------------
# Project portfolio
# ---------------------------------------------------------------------------
projects = [
    # ------------------------------------------------------------------
    # 1. Seismic Reprocessing Platform  (large, mandatory, long lead)
    # ------------------------------------------------------------------
    {
        "name": "Seismic Reprocessing Platform",
        "type": "large",
        "value": 95,
        "mandatory": True,
        "dependencies": [],
        "duration_optimistic_weeks": 16,
        "duration_likely_weeks": 22,
        "duration_pessimistic_weeks": 32,
        "resource_profile": {
            "data_scientists":   [3, 4, 4, 3, 2, 2],
            "geoscientists":     [2, 2, 3, 2, 1, 0],
            "project_managers":  [1, 1, 1, 1, 1, 1],
        },
        "earliest_start_month": 0,
        "probability": 1.0,
        "tasks": [
            {"id": "S1", "name": "Requirements & Scoping",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": [],
             "resources": {"data_scientists": 1, "geoscientists": 2}},
            {"id": "S2", "name": "Data Ingestion Pipeline",
             "optimistic": 3, "likely": 5, "pessimistic": 8,
             "predecessors": ["S1"],
             "resources": {"data_scientists": 3}},
            {"id": "S3", "name": "Processing Algorithm Dev",
             "optimistic": 4, "likely": 6, "pessimistic": 10,
             "predecessors": ["S1"],
             "resources": {"data_scientists": 2, "geoscientists": 2}},
            {"id": "S4", "name": "Integration & Testing",
             "optimistic": 3, "likely": 4, "pessimistic": 6,
             "predecessors": ["S2", "S3"],
             "resources": {"data_scientists": 2, "geoscientists": 1}},
            {"id": "S5", "name": "Deployment & Handover",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["S4"],
             "resources": {"data_scientists": 1, "project_managers": 1}},
        ],
    },

    # ------------------------------------------------------------------
    # 2. Well-Log ML Predictor  (medium, mandatory)
    # ------------------------------------------------------------------
    {
        "name": "Well-Log ML Predictor",
        "type": "medium",
        "value": 80,
        "mandatory": True,
        "dependencies": [],
        "duration_optimistic_weeks": 10,
        "duration_likely_weeks": 14,
        "duration_pessimistic_weeks": 20,
        "resource_profile": {
            "data_scientists":   [2, 3, 3, 2],
            "geoscientists":     [1, 1, 1, 0],
            "project_managers":  [1, 1, 1, 1],
        },
        "earliest_start_month": 0,
        "probability": 1.0,
        "tasks": [
            {"id": "W1", "name": "Data Audit & Cleaning",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": [],
             "resources": {"data_scientists": 1, "geoscientists": 1}},
            {"id": "W2", "name": "Feature Engineering",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["W1"],
             "resources": {"data_scientists": 2}},
            {"id": "W3", "name": "Model Training & Tuning",
             "optimistic": 3, "likely": 4, "pessimistic": 6,
             "predecessors": ["W2"],
             "resources": {"data_scientists": 2}},
            {"id": "W4", "name": "Validation & Reporting",
             "optimistic": 2, "likely": 3, "pessimistic": 4,
             "predecessors": ["W3"],
             "resources": {"data_scientists": 1, "geoscientists": 1, "project_managers": 1}},
        ],
    },

    # ------------------------------------------------------------------
    # 3. Reservoir Simulation Dashboard  (large, mandatory, depends on #1)
    # ------------------------------------------------------------------
    {
        "name": "Reservoir Simulation Dashboard",
        "type": "large",
        "value": 90,
        "mandatory": True,
        "dependencies": ["Seismic Reprocessing Platform"],
        "duration_optimistic_weeks": 14,
        "duration_likely_weeks": 20,
        "duration_pessimistic_weeks": 28,
        "resource_profile": {
            "data_scientists":   [2, 3, 4, 3, 2],
            "geoscientists":     [2, 2, 2, 1, 1],
            "project_managers":  [1, 1, 1, 1, 1],
        },
        "earliest_start_month": 5,   # can't start until Seismic is well underway
        "probability": 1.0,
        "tasks": [
            {"id": "R1", "name": "Dashboard Architecture",
             "optimistic": 2, "likely": 3, "pessimistic": 4,
             "predecessors": [],
             "resources": {"data_scientists": 2, "project_managers": 1}},
            {"id": "R2", "name": "Simulation Engine Wrapper",
             "optimistic": 4, "likely": 6, "pessimistic": 9,
             "predecessors": ["R1"],
             "resources": {"data_scientists": 3, "geoscientists": 2}},
            {"id": "R3", "name": "Visualization Layer",
             "optimistic": 3, "likely": 4, "pessimistic": 6,
             "predecessors": ["R1"],
             "resources": {"data_scientists": 2}},
            {"id": "R4", "name": "User Testing & Polish",
             "optimistic": 3, "likely": 5, "pessimistic": 8,
             "predecessors": ["R2", "R3"],
             "resources": {"data_scientists": 1, "geoscientists": 1, "project_managers": 1}},
        ],
    },

    # ------------------------------------------------------------------
    # 4. Automated Core Analysis  (medium, optional, high value)
    # ------------------------------------------------------------------
    {
        "name": "Automated Core Analysis",
        "type": "medium",
        "value": 75,
        "mandatory": False,
        "dependencies": [],
        "duration_optimistic_weeks": 8,
        "duration_likely_weeks": 12,
        "duration_pessimistic_weeks": 18,
        "resource_profile": {
            "data_scientists":   [2, 2, 2],
            "geoscientists":     [2, 3, 2],
            "project_managers":  [1, 1, 0],
        },
        "earliest_start_month": 2,
        "probability": 0.85,
        "tasks": [
            {"id": "C1", "name": "Image Pipeline Setup",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": [],
             "resources": {"data_scientists": 1, "geoscientists": 1}},
            {"id": "C2", "name": "Classification Model",
             "optimistic": 3, "likely": 4, "pessimistic": 6,
             "predecessors": ["C1"],
             "resources": {"data_scientists": 2, "geoscientists": 1}},
            {"id": "C3", "name": "Integration & QA",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["C2"],
             "resources": {"data_scientists": 1, "geoscientists": 2}},
        ],
    },

    # ------------------------------------------------------------------
    # 5. Production Forecasting Upgrade  (small, mandatory)
    # ------------------------------------------------------------------
    {
        "name": "Production Forecasting Upgrade",
        "type": "small",
        "value": 65,
        "mandatory": True,
        "dependencies": [],
        "duration_optimistic_weeks": 5,
        "duration_likely_weeks": 8,
        "duration_pessimistic_weeks": 12,
        "resource_profile": {
            "data_scientists":   [2, 2],
            "geoscientists":     [1, 1],
            "project_managers":  [1, 1],
        },
        "earliest_start_month": 1,
        "probability": 1.0,
        "tasks": [
            {"id": "P1", "name": "Current Model Audit",
             "optimistic": 1, "likely": 2, "pessimistic": 3,
             "predecessors": [],
             "resources": {"data_scientists": 1, "geoscientists": 1}},
            {"id": "P2", "name": "Algorithm Improvements",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["P1"],
             "resources": {"data_scientists": 2}},
            {"id": "P3", "name": "Back-testing & Deploy",
             "optimistic": 1, "likely": 2, "pessimistic": 3,
             "predecessors": ["P2"],
             "resources": {"data_scientists": 1, "project_managers": 1}},
        ],
    },

    # ------------------------------------------------------------------
    # 6. Geospatial Data Lake  (large, optional, uncertain)
    # ------------------------------------------------------------------
    {
        "name": "Geospatial Data Lake",
        "type": "large",
        "value": 85,
        "mandatory": False,
        "dependencies": [],
        "duration_optimistic_weeks": 18,
        "duration_likely_weeks": 26,
        "duration_pessimistic_weeks": 36,
        "resource_profile": {
            "data_scientists":   [3, 4, 4, 3, 3, 2],
            "geoscientists":     [1, 1, 2, 2, 1, 1],
            "project_managers":  [1, 1, 1, 1, 1, 1],
        },
        "earliest_start_month": 0,
        "probability": 0.70,
        "tasks": [
            {"id": "G1", "name": "Cloud Architecture Design",
             "optimistic": 3, "likely": 4, "pessimistic": 7,
             "predecessors": [],
             "resources": {"data_scientists": 2, "project_managers": 1}},
            {"id": "G2", "name": "Data Migration",
             "optimistic": 4, "likely": 7, "pessimistic": 10,
             "predecessors": ["G1"],
             "resources": {"data_scientists": 3, "geoscientists": 1}},
            {"id": "G3", "name": "API & Access Layer",
             "optimistic": 3, "likely": 5, "pessimistic": 8,
             "predecessors": ["G1"],
             "resources": {"data_scientists": 2}},
            {"id": "G4", "name": "Spatial Indexing Engine",
             "optimistic": 3, "likely": 5, "pessimistic": 7,
             "predecessors": ["G2"],
             "resources": {"data_scientists": 2, "geoscientists": 2}},
            {"id": "G5", "name": "Testing & Documentation",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["G3", "G4"],
             "resources": {"data_scientists": 1, "geoscientists": 1, "project_managers": 1}},
        ],
    },

    # ------------------------------------------------------------------
    # 7. Environmental Compliance Tracker  (small, mandatory, depends on #2)
    # ------------------------------------------------------------------
    {
        "name": "Environmental Compliance Tracker",
        "type": "small",
        "value": 70,
        "mandatory": True,
        "dependencies": ["Well-Log ML Predictor"],
        "duration_optimistic_weeks": 4,
        "duration_likely_weeks": 6,
        "duration_pessimistic_weeks": 10,
        "resource_profile": {
            "data_scientists":   [1, 2],
            "geoscientists":     [1, 1],
            "project_managers":  [1, 1],
        },
        "earliest_start_month": 4,
        "probability": 1.0,
        "tasks": [
            {"id": "E1", "name": "Regulatory Data Mapping",
             "optimistic": 1, "likely": 2, "pessimistic": 3,
             "predecessors": [],
             "resources": {"data_scientists": 1, "geoscientists": 1}},
            {"id": "E2", "name": "Alert & Reporting Module",
             "optimistic": 2, "likely": 3, "pessimistic": 5,
             "predecessors": ["E1"],
             "resources": {"data_scientists": 2, "project_managers": 1}},
            {"id": "E3", "name": "Stakeholder Review",
             "optimistic": 1, "likely": 1, "pessimistic": 2,
             "predecessors": ["E2"],
             "resources": {"project_managers": 1}},
        ],
    },
]
