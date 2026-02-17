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

**Location**: Dedicated 5th tab ("People"), positioned after the existing four tabs (List / Timeline / Resource Allocation / Forecast).

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

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | People roster location | **Dedicated 5th tab** ("People"), accessible at all times during planning sessions |
| 2 | Headcount vs. assignment reconciliation | **Warning system** — flag divergence between planned headcounts and named assignments (see below) |
| 3 | Role filtering in assignment picker | Soft-sort: matching roles first, a divider, then other roles below |
| 4 | Sample data | Ship sample roster + pre-populated assignments so the feature is immediately visible |

---

## Headcount Reconciliation Warning System

When a project has at least one named person assigned, the app compares `resources.*` (planned headcount) against the count of assigned people by role. Divergence is surfaced as a non-blocking warning — users can dismiss or ignore it.

### Warning triggers

| Condition | Severity | Message |
|---|---|---|
| Named DS count > `resources.dataScientists` | Yellow | "3 DS assigned, 2 planned — consider updating the planned headcount" |
| Named DS count < `resources.dataScientists` | Yellow | "1 DS assigned, 2 planned — 1 DS seat unfilled" |
| Named DS count matches exactly | None | No message |
| No named assignments at all | None | Silence — project is in planning-only mode |

**Severity is always yellow (informational), never red.** The two fields are intentionally independent, so divergence is a prompt for the user to reconcile, not an error.

### Where warnings appear

**1. Project Modal — Resources section**

After the existing DS / GS / PM number inputs, a reconciliation row appears if the named count differs:

```
Resources
─────────────────────────────────────────────────────
  Data Scientists  [ 2 ]    ⚠ 3 assigned (Marco, Alice, Bob)
  Geoscientists    [ 1 ]    ✓ 1 assigned (Jamie)
  Project Managers [ 1 ]    ○ No one assigned yet
─────────────────────────────────────────────────────
```

Icons:
- `⚠` yellow — mismatch (over or under)
- `✓` green — exact match
- `○` gray — no assignments (only shown when `resources.*` > 0, to prompt staffing)

Clicking the `⚠` or the names opens a small popover explaining the gap and offering a one-click "Update planned count to match" button.

**2. Project List Table**

A new "Staffing" column (optional, hideable) shows a compact status per project:

| Status | Display |
|---|---|
| Fully staffed, no mismatch | `✓ Staffed` (green) |
| Over-assigned | `⚠ +1 DS` (yellow) |
| Under-assigned | `⚠ −1 GS` (yellow) |
| No assignments | `○ Unassigned` (gray, only for scheduled projects) |
| Project unscheduled | blank — unscheduled projects not evaluated |

**3. People Tab — aggregate view**

A summary banner at the top of the People tab if any active (scheduled) projects have staffing mismatches:

```
⚠  3 scheduled projects have staffing gaps. Review →
```

Clicking "Review →" filters the Project List to only projects with reconciliation warnings.

### Acceptance Criteria additions

- [ ] Resource section in Project Modal shows reconciliation icons when named count ≠ planned count
- [ ] "Update planned count to match" one-click fix works for each role independently
- [ ] Project List "Staffing" column reflects current reconciliation state, updates live
- [ ] Unscheduled projects do not generate staffing warnings
- [ ] Projects with zero named assignments show `○` prompts (not warnings) for roles where `resources.*` > 0
- [ ] Summary banner in People tab appears when ≥ 1 scheduled project has a mismatch
- [ ] Warnings are purely informational — the user can save and export without resolving them

---

## Open Questions

1. **Role filtering in assignment picker**: Resolved — soft-sort (matching roles first, divider, others below).
2. **Sample data**: Resolved — include a sample roster and pre-populated assignments.

---

## Out of Scope for This Version

- Sub-project or phase-level assignments (person is 100% for phase 1, 25% for phase 2)
- Skill or specialty tracking beyond role
- Vacation / leave calendar
- Automatic suggestion of available people when adding resources
- Historical utilization tracking
