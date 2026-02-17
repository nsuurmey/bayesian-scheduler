# PRD: Named People & Individual Capacity Tracking

**Feature Area**: Resource Management
**Depends On**: project-scheduler-prd.md (base data model)
**Status**: Draft

---

## Problem Statement

The current scheduler tracks resources as headcounts (`dataScientists: 3`) tied to a project. This answers *how many* people a project needs, but not *which* people are assigned. As a result, the Head of Innovation cannot:

- See at a glance who is on too many projects simultaneously
- Identify individuals with open capacity before assigning new work
- Have a name-level conversation in leadership sessions ("Alice is on three signed projects — who else can cover the ML Pipeline?")

---

## Goals

1. Maintain a named roster of people with their role
2. Assign specific people to projects at fractional allocations (0.25 increments)
3. Surface per-person utilization: how loaded is each individual, week by week
4. Identify who is over-allocated, at capacity, and has bandwidth
5. Remain additive — existing projects without named assignments continue to work

## Non-Goals

- Tracking hours worked (actuals vs. plan)
- Time-off / vacation calendars
- Sub-project or task-level assignments
- Authentication or per-user access control
- Changing the Bayesian probability model

---

## Data Model Changes

### New Top-Level Collection: `people`

Added alongside `projects` and `settings` in state and exported JSON.

```json
"people": [
  {
    "id": "uuid",
    "name": "Alice Chen",
    "role": "Data Scientist",
    "capacity": 1.0
  },
  {
    "id": "uuid",
    "name": "Marco Rivera",
    "role": "Geoscientist",
    "capacity": 0.75
  }
]
```

| Field | Type | Notes |
|---|---|---|
| `id` | uuid string | Stable across renames |
| `name` | string | Display name |
| `role` | enum | `"Data Scientist" \| "Geoscientist" \| "Project Manager"` — matches existing resource categories |
| `capacity` | number | Total available FTE. Default `1.0`. Supports 0.25 increments. Useful for part-time staff. |

---

### Project Schema Addition: `assignedPeople`

New optional array field on each project. Existing projects without it behave exactly as today.

```json
"assignedPeople": [
  { "personId": "uuid-alice",  "fraction": 0.50 },
  { "personId": "uuid-bob",    "fraction": 0.25 },
  { "personId": "uuid-marco",  "fraction": 1.00 }
]
```

| Field | Type | Notes |
|---|---|---|
| `personId` | uuid string | References `people[].id` |
| `fraction` | number | Allocation as share of full capacity. Constrained to `0.25 \| 0.50 \| 0.75 \| 1.00` |

**Allocation rules:**
- A person can appear on multiple projects simultaneously; their total fraction across active projects is their utilization.
- The time range of the assignment is inherited from the project's `startWeek` and `durationWeeks` — no separate date fields on the assignment itself.
- `fraction` must be one of the four allowed increments. The UI enforces this via a step selector, not a free-text input.
- A person should only appear once per project (one record per person per project).

**Relationship to existing `resources` headcounts:**
- `resources.dataScientists: 2` remains the *planning target* (how many DS you intend to use).
- `assignedPeople` is the *operational reality* (who you've actually allocated).
- The two are intentionally independent so you can plan before you've named people, or name people before finalizing the headcount estimate.
- A future validation warning may flag when the two diverge (e.g., 3 DS planned but only 2 DS assigned), but this is out of scope for this version.

---

## Updated State Shape

```javascript
const initialState = {
  settings: { ... },           // unchanged
  projects: [ ... ],           // unchanged + optional assignedPeople[]
  people: [],                  // NEW
  ui: { ... }                  // unchanged + new people modal flag
};
```

---

## UI Surfaces

### 1. People Roster Management

**Location**: New "People" tab, or accessible via Settings modal — TBD based on how often it's edited. Recommend a dedicated tab since it's referenced frequently during planning sessions.

**Layout**: Simple table

| Name | Role | Capacity | Assigned Projects | Current Utilization | Actions |
|---|---|---|---|---|---|
| Alice Chen | Data Scientist | 1.0 | Alpha Basin, ML Pipeline | 0.75 (75%) | Edit \| Remove |
| Marco Rivera | Geoscientist | 0.75 | Alpha Basin | 1.00 (133%) ⚠️ | Edit \| Remove |

**Add / Edit form fields:**
- Name (text, required)
- Role (dropdown: Data Scientist / Geoscientist / Project Manager)
- Capacity (step selector: 0.25 / 0.50 / 0.75 / 1.00, default 1.00)

**Behaviors:**
- Removing a person does not delete their assignments from projects — it orphans them. The UI flags orphaned assignments as unresolved (person name shown in italics with "Unknown Person" label) so the user can clean them up.
- Sorting: by name (default), by role, by current utilization
- Role filter pills at top of table to narrow list by discipline

---

### 2. Assignment UI in Project Modal

**Location**: Inside the existing Project Detail Modal, below the `Resources` section. New section header: **"Assigned People"**.

**Layout:**

```
Assigned People
─────────────────────────────────────────────────
  Alice Chen        Data Scientist   [ 0.50 ▾ ]  [×]
  Bob Okafor        Data Scientist   [ 0.25 ▾ ]  [×]
  Marco Rivera      Geoscientist     [ 1.00 ▾ ]  [×]

  [ + Add Person ]
─────────────────────────────────────────────────
```

**Add Person interaction:**
- Clicking `+ Add Person` opens an inline dropdown/search
- List is filtered to show people whose **role matches** the project's resource needs (e.g., if the project has `geoscientists: 2`, GS are shown first)
- All roles still available — user can override the filter
- People already assigned to this project are excluded from the picker

**Fraction selector:**
- Segmented button or dropdown with exactly four options: `0.25` / `0.50` / `0.75` / `1.00`
- Default: `1.00` on add, then user adjusts

**Utilization warning inline:**
If adding this assignment would push the person's total weekly utilization above 1.0 (their capacity) during the project's active weeks, show a yellow warning badge next to their name:

```
  Alice Chen   Data Scientist   [ 0.50 ▾ ]  [×]  ⚠ 125% in Wk 14–18
```

Clicking the badge shows a tooltip listing the other projects causing the conflict.

---

### 3. Person-Level Resource View (New Sub-View in Resource Allocation Tab)

**Location**: Toggle within Tab 3 (Resource Allocation). Add a view toggle:
```
[ By Role ]  [ By Person ]
```

**By Person layout:**

Each person gets a row. Each cell is a week. Color intensity = utilization that week.

```
              Wk 1  Wk 2  Wk 3  ...  Wk 20  ...  Wk 52
Alice Chen    ████  ████  ████       ░░░░░
Bob Okafor    ░░░░  ████  ████       ████
Marco Rivera  ████  ████  ████  ...  ████   ...  (over)
```

Color scale (relative to each person's own `capacity`):
- `< 50%` — light green
- `50–99%` — medium green
- `= 100%` — dark green (fully utilized)
- `> 100%` — red (over-allocated)
- Empty — gray/white

**Hover tooltip on a cell:**
```
Alice Chen — Week 14
─────────────────────
Alpha Basin:      0.50
ML Pipeline:      0.25
─────────────────────
Total: 0.75 / 1.00  (75%)
```

**Grouping:** Rows grouped by role (Data Scientists, then Geoscientists, then Project Managers) with collapsible group headers. Group header shows aggregate utilization for that discipline.

**Clicking a cell:** Highlights all projects active for that person in that week in the Timeline tab (cross-view navigation).

---

### 4. Capacity Indicator Updates (Header Bar)

The existing header capacity indicator:
```
DS: 12/15 used (80%) | GS: 5/8 used (63%) | PM: 2/3 used (67%)
```

Remains unchanged. This is headcount-based and reflects aggregate planning.

**Clicking the indicator** opens the existing breakdown modal. Add a new section to that modal:

```
─────────────────────────────────────
Individuals Over Capacity This Week
─────────────────────────────────────
Marco Rivera (GS)  1.25 / 0.75  ⚠ 167%
Alice Chen   (DS)  1.00 / 1.00     100%
─────────────────────────────────────
```

Only shows people with named assignments. People without assignments are not shown here.

---

## Backward Compatibility

| Scenario | Behavior |
|---|---|
| Project with no `assignedPeople` | Works exactly as today; resource allocation uses headcounts only |
| People roster is empty | All assignment UI sections are present but empty; no warnings |
| Import of old JSON without `people` key | `people` defaults to `[]`; no error |
| Export | `people` array always included in JSON (may be empty) |

---

## Acceptance Criteria

### Roster Management
- [ ] Can add a person with name, role, and capacity
- [ ] Can edit a person's name, role, or capacity
- [ ] Can remove a person; their orphaned assignments are flagged in affected projects
- [ ] Roster persists in exported JSON and is restored on import

### Assignment
- [ ] Can assign any person in the roster to a project with a fraction (0.25 / 0.50 / 0.75 / 1.00)
- [ ] Can change a person's fraction on a project
- [ ] Can remove a person from a project
- [ ] Fraction is always one of the four allowed values (no free-form entry)
- [ ] Over-allocation warning appears inline when an assignment would push a person above 100% capacity in any week of the project

### Person-Level Resource View
- [ ] "By Person" toggle in Resource Allocation tab renders a row per person
- [ ] Cell color reflects utilization relative to individual capacity
- [ ] Over-allocated cells are red
- [ ] Hover tooltip shows project breakdown for that person/week
- [ ] Rows are grouped by role
- [ ] Weeks with no assignment are shown as empty/gray

### Capacity Modal
- [ ] Shows individuals over capacity in the current week
- [ ] Only shows people with at least one named assignment

### Data Integrity
- [ ] Export → import → export produces identical JSON
- [ ] Deleting a project removes its entries from any person's "Assigned Projects" display
- [ ] Deleting a person flags orphaned assignments; does not silently corrupt data

---

## Open Questions

1. **People tab vs. Settings**: Should the People roster live in a dedicated 5th tab, or inside the Settings modal? Recommend tab (easier to access mid-session) but worth confirming with users.

2. **Headcount vs. named assignment reconciliation**: Should the app warn when `resources.dataScientists` doesn't match the count of assigned DS people? If yes, at what threshold (any mismatch, or only when named > planned)?

3. **Role filtering in assignment picker**: Should the picker hard-filter to matching roles, or soft-sort (matching roles first, others below a divider)?

4. **Sample data update**: Should the existing sample projects ship with pre-populated `assignedPeople` using a sample roster, so new users immediately see the feature working?

---

## Out of Scope for This Version

- Sub-project or phase-level assignments (person is 100% for phase 1, 25% for phase 2)
- Skill or specialty tracking beyond role
- Vacation / leave calendar
- Automatic suggestion of available people when adding resources
- Historical utilization tracking
