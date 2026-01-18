# Product Requirements Document: Project Scheduling Toolkit

## Overview

### Purpose
A single-page web application for scheduling and prioritizing projects across a technical team. The tool supports capacity planning, Bayesian probability tracking for project likelihood, and facilitates leadership team discussions about resource allocation and prioritization.

### Target User
Head of Innovation managing a team of ~20 data scientists, geoscientists, and project managers. Primary use is in leadership team working sessions to plan annual project portfolio.

### Technical Requirements
- **Deployment**: Standalone HTML file (single file with embedded CSS/JS)
- **Framework**: React (via CDN) with Tailwind CSS
- **Data Persistence**: JSON import/export (no backend required)
- **Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge)

---

## Data Model

### Capacity Configuration (Global Settings)
```json
{
  "capacity": {
    "dataScientists": 15,
    "geoscientists": 8,
    "projectManagers": 3
  },
  "defaultProbabilities": {
    "signed": 95,
    "closeToSigning": 70,
    "interested": 40,
    "frontier": 15
  }
}
```

### Project Schema
```json
{
  "id": "uuid",
  "name": "string",
  "sponsor": "string",
  "description": "string (brief)",
  "okr": "Revenue | Projects | Innovation",
  "source": "External | Internal",
  "stage": "Signed | Close to Signing | Interested | Frontier",
  "probability": "number (0-100, auto-set by stage, manually adjustable)",
  "impact": "Low | Medium | High",
  "effort": "S | M | L",
  "durationWeeks": "number",
  "resources": {
    "dataScientists": "number",
    "geoscientists": "number",
    "projectManagers": "number"
  },
  "startWeek": "number (week of year) | null",
  "dependencies": ["projectId", "projectId"],
  "observations": {
    "positive": [
      { "text": "string", "likelihood": "Low | Medium | High", "timestamp": "ISO date" }
    ],
    "negative": [
      { "text": "string", "likelihood": "Low | Medium | High", "timestamp": "ISO date" }
    ]
  },
  "createdAt": "ISO date",
  "updatedAt": "ISO date"
}
```

---

## Features

### 1. Global Settings Panel
**Location**: Accessible via settings icon in header

**Functionality**:
- Set total available capacity for each resource type:
  - Data Scientists (number)
  - Geoscientists (number)
  - Project Managers (number)
- Configure default probabilities for each stage:
  - Signed (default: 95%)
  - Close to Signing (default: 70%)
  - Interested (default: 40%)
  - Frontier (default: 15%)
- Settings persist in exported JSON

---

### 2. Capacity Indicator (Always Visible)
**Location**: Header bar, always visible across all views

**Display**:
```
DS: 12/15 used (80%) | GS: 5/8 used (63%) | PM: 2/3 used (67%)
```

**Behavior**:
- Shows **scheduled** projects only (those with a start date assigned)
- Color coding:
  - Green: < 70% utilized
  - Yellow: 70-90% utilized
  - Red: > 90% utilized
- Clicking opens detailed breakdown modal

---

### 3. View Tabs

#### Tab 1: Project List (Master Table)
**Purpose**: Complete inventory of all projects with full attributes

**Table Columns**:
| Column | Type | Sortable | Filterable |
|--------|------|----------|------------|
| Name | Text (link to detail) | Yes | Yes (search) |
| Sponsor | Text | Yes | Yes |
| OKR | Chip (Revenue/Projects/Innovation) | Yes | Yes |
| Source | Badge (External/Internal) | Yes | Yes |
| Stage | Dropdown | Yes | Yes |
| Probability | Number + slider | Yes | Yes (range) |
| Impact | Chip (L/M/H) | Yes | Yes |
| Effort | Chip (S/M/L) | Yes | Yes |
| Duration | Number (weeks) | Yes | Yes (range) |
| DS | Number | Yes | No |
| GS | Number | Yes | No |
| PM | Number | Yes | No |
| Start Week | Number or "Unscheduled" | Yes | Yes |
| Dependencies | Tags | No | Yes |

**Actions**:
- Add new project (opens modal form)
- Edit project inline or via modal
- Delete project (with confirmation)
- Bulk select and delete
- Quick-edit probability via inline slider

**Filters Bar**:
- Stage filter (multi-select)
- OKR filter (multi-select)
- Source filter (External/Internal)
- Scheduled/Unscheduled toggle
- Search by name/sponsor

---

#### Tab 2: Timeline / Gantt View
**Purpose**: Visual scheduling of projects over time

**Layout**:
- X-axis: Weeks (Week 1 through Week 52, with current week highlighted)
- Y-axis: Projects (grouped by stage or OKR, user toggle)
- Each project is a horizontal bar spanning its duration

**Bar Display**:
- Bar length = duration in weeks
- Bar color = stage (Signed=green, Close to Signing=blue, Interested=yellow, Frontier=gray)
- Bar opacity = probability (higher prob = more opaque)
- Bar label = project name + sponsor
- Resource badges on bar: "DS:3 GS:2 PM:1"

**Interactions**:
- **Drag horizontally**: Move project start date
- **Drag from unscheduled pool**: Assign start date
- **Click bar**: Open project detail modal
- **Hover**: Show tooltip with full project info

**Unscheduled Pool**:
- Left sidebar showing all projects without start dates
- Drag from pool onto timeline to schedule
- Shows count: "12 Unscheduled Projects"

**Grouping Toggle**:
- Group by: Stage | OKR | None
- Collapse/expand groups

**Zoom Controls**:
- Q1 / Q2 / Q3 / Q4 / Full Year views

---

#### Tab 3: Resource Allocation View
**Purpose**: See resource utilization over time

**Layout**:
- Three stacked area charts (one each for DS, GS, PM)
- X-axis: Weeks
- Y-axis: Resource count
- Horizontal line showing capacity limit

**Chart Layers** (stacked by stage):
- Signed projects (solid)
- Close to Signing (striped)
- Interested (dotted)
- Frontier (light/faded)

**Interactivity**:
- Hover on week: Show breakdown popup
  - "Week 14: DS allocation"
  - "Signed: 8, Close to Signing: 4, Interested: 2"
  - "Total: 14/15 (93%)"
- Click on overallocated week: Highlight conflicting projects
- Toggle: Show only scheduled vs. include probability-weighted unscheduled

**Alerts Panel**:
- List of weeks with overallocation
- "Week 14-18: DS overallocated by 3"
- Click to jump to that week in timeline view

---

#### Tab 4: Probability-Weighted Forecast
**Purpose**: Scenario planning showing capacity needs under different assumptions

**Scenarios Displayed**:

| Scenario | Description | Calculation |
|----------|-------------|-------------|
| Committed Only | Signed projects only | Sum resources where stage = Signed |
| High Confidence | Signed + Close to Signing | Sum resources where stage in (Signed, Close to Signing) |
| Expected Case | Probability-weighted all | Sum (resources × probability) for all projects |
| Full Pipeline | Everything happens | Sum all resources regardless of stage |

**Display Format**:
For each scenario, show:
```
┌─────────────────────────────────────────────────────────┐
│ COMMITTED ONLY                                          │
│ DS: 45 person-weeks (60% of annual capacity)            │
│ GS: 30 person-weeks (72% of annual capacity)            │
│ PM: 20 person-weeks (128% of annual capacity) ⚠️        │
│                                                         │
│ [View Projects in This Scenario]                        │
└─────────────────────────────────────────────────────────┘
```

**Comparison Chart**:
- Grouped bar chart comparing all 4 scenarios
- Grouped by resource type
- Capacity line overlaid

**What-If Analysis**:
- Slider to adjust "What if we only take projects with probability > X%?"
- Real-time update of capacity needs

---

### 4. Project Detail Modal
**Trigger**: Click project name anywhere in app

**Sections**:

**Header**:
- Project name (editable)
- Stage dropdown
- Probability slider with numeric input

**Basic Info** (2-column layout):
- Sponsor (text input)
- OKR (dropdown: Revenue / Projects / Innovation)
- Source (toggle: External / Internal)
- Impact (button group: L / M / H)
- Effort (button group: S / M / L)
- Duration (number input, weeks)
- Start Week (number input or "Unscheduled")

**Resources** (inline number inputs):
- Data Scientists: [___]
- Geoscientists: [___]
- Project Managers: [___]

**Dependencies**:
- Multi-select dropdown of other project names
- Shows as tags
- Warning if circular dependency detected

**Description**:
- Text area (500 char max)

**Observations Panel** (side-by-side):
```
┌─────────────────────┬─────────────────────┐
│ ✅ POSITIVE         │ ⚠️ NEGATIVE         │
├─────────────────────┼─────────────────────┤
│ [+ Add observation] │ [+ Add observation] │
│                     │                     │
│ "Strong exec        │ "Budget concerns    │
│  sponsor support"   │  raised in Q4"      │
│  Likelihood: High   │  Likelihood: Medium │
│  Jan 15, 2025       │  Jan 10, 2025       │
│  [edit] [delete]    │  [edit] [delete]    │
│                     │                     │
│ "Aligns with their  │ "Key stakeholder    │
│  2025 strategy"     │  leaving in March"  │
│  Likelihood: Medium │  Likelihood: Low    │
│  Jan 12, 2025       │  Jan 8, 2025        │
│  [edit] [delete]    │  [edit] [delete]    │
└─────────────────────┴─────────────────────┘
```

**Observation Entry**:
- Text input (200 char max)
- Likelihood dropdown (Low / Medium / High)
- Auto-timestamps on save
- No limit on count, but UI shows top 3 by default with "Show all" expander

**Footer**:
- Created: [date] | Last updated: [date]
- [Delete Project] [Cancel] [Save]

---

### 5. Add Project Quick Form
**Trigger**: "+ Add Project" button (visible on all views)

**Minimal Fields** (required):
- Name
- Stage (defaults to "Frontier")
- OKR
- Source (defaults to "External")

**Optional Fields** (collapsible "More Details" section):
- All other fields with sensible defaults:
  - Probability: Auto-set by stage
  - Impact: Medium
  - Effort: M
  - Duration: 4 weeks
  - Resources: 1 DS, 0 GS, 0 PM
  - Start Week: Unscheduled

---

### 6. Data Management

**Export**:
- Button: "Export JSON"
- Downloads file: `project-schedule-YYYY-MM-DD.json`
- Includes: All projects, capacity settings, default probabilities

**Import**:
- Button: "Import JSON"
- File picker for .json files
- Validation with error messages
- Option: "Replace all" or "Merge with existing"
- Merge logic: Match by project ID, update if exists, add if new

**Auto-save to localStorage**:
- Save state every 30 seconds
- Save on any data change
- Warning on page close if unsaved changes
- "Restore previous session" prompt on load if localStorage has data

---

## UI/UX Requirements

### Design Principles
- Clean, professional aesthetic suitable for executive presentations
- High information density without feeling cluttered
- Obvious visual hierarchy
- Keyboard shortcuts for power users

### Color Scheme
- **Signed**: Green (#22c55e)
- **Close to Signing**: Blue (#3b82f6)
- **Interested**: Yellow/Amber (#f59e0b)
- **Frontier**: Gray (#6b7280)
- **Overallocated**: Red (#ef4444)
- **Internal projects**: Subtle purple accent border

### Responsive Behavior
- Primary target: Desktop/laptop (1280px+ width)
- Functional at 1024px minimum
- Timeline view may require horizontal scroll on smaller screens

### Keyboard Shortcuts
- `N`: New project
- `S`: Save/Export
- `1-4`: Switch tabs
- `Esc`: Close modals
- `/`: Focus search

---

## Implementation Notes

### Technology Stack
- React 18 (via CDN: https://unpkg.com/react@18/umd/react.production.min.js)
- ReactDOM (via CDN)
- Tailwind CSS (via CDN)
- Lucide React for icons
- Recharts for charts (Resource Allocation, Forecast views)
- Native drag-and-drop API for timeline

### File Structure
Single HTML file containing:
1. HTML skeleton
2. Tailwind config (if customization needed)
3. React components (in script tag with type="text/babel" or pre-compiled)
4. Application state management (React Context or useReducer)
5. localStorage utilities
6. JSON import/export utilities

### State Management
```javascript
const initialState = {
  settings: {
    capacity: { dataScientists: 15, geoscientists: 8, projectManagers: 3 },
    defaultProbabilities: { signed: 95, closeToSigning: 70, interested: 40, frontier: 15 }
  },
  projects: [],
  ui: {
    activeTab: 'list',
    filters: {},
    selectedProjectId: null,
    modalOpen: null
  }
};
```

### Key Components
1. `App` - Root component, state provider
2. `Header` - Title, capacity indicator, settings button, data management
3. `TabNav` - Tab switching
4. `ProjectList` - Table view with sorting/filtering
5. `Timeline` - Gantt chart with drag-drop
6. `ResourceChart` - Stacked area charts
7. `ForecastView` - Scenario comparison
8. `ProjectModal` - Detail/edit form
9. `SettingsModal` - Capacity and defaults configuration
10. `ObservationPanel` - Positive/negative observations UI

---

## Success Criteria

1. **Functional**: All four views render correctly with sample data
2. **Data Integrity**: Export → close → import returns identical state
3. **Usability**: Can add a new project in < 30 seconds
4. **Visual Clarity**: Overallocation is immediately obvious
5. **Performance**: Handles 50+ projects without lag
6. **Deployable**: Single HTML file opens in browser with no build step

---

## Sample Data for Testing

Include 10-15 sample projects on first load (or via "Load Sample Data" button):

| Name | Stage | OKR | Duration | DS | GS | PM |
|------|-------|-----|----------|----|----|-----|
| Alpha Basin Analysis | Signed | Projects | 8 | 2 | 3 | 1 |
| ML Pipeline Upgrade | Signed | Innovation | 6 | 4 | 0 | 1 |
| Client X Prospect Study | Close to Signing | Revenue | 12 | 3 | 2 | 1 |
| Internal Tool Modernization | Interested | Innovation | 4 | 2 | 0 | 0 |
| New Market Exploration | Frontier | Revenue | 16 | 2 | 4 | 1 |
| ... | ... | ... | ... | ... | ... | ... |

---

## Out of Scope (Future Versions)

- Multi-user collaboration / real-time sync
- Backend database
- User authentication
- Email notifications
- Integration with external project management tools
- Mobile-optimized views
- Historical tracking / version comparison
- Actual calendar date scheduling (vs. week numbers)

---

## Appendix: Bayesian Probability Guidance

The probability field represents the likelihood a project will actually happen. It should be updated as new information emerges.

**Default Probabilities by Stage**:
- **Signed** (95%): SOW executed, work will proceed barring exceptional circumstances
- **Close to Signing** (70%): Scope defined, sponsor committed, awaiting final approval
- **Interested** (40%): Sponsor engaged, scope being defined, mutual interest established
- **Frontier** (15%): Early BD conversations, concept stage, high uncertainty

**Adjusting Probability**:
- Use observations to justify probability adjustments
- Positive observations with High likelihood → increase probability
- Negative observations with High likelihood → decrease probability
- Always capture the *reason* for adjustment in observations

**In Leadership Discussions**:
- Glass-half-full perspective: Focus on positive observations
- Glass-half-empty perspective: Focus on negative observations
- Both are valid inputs that inform the probability
- The tool captures both perspectives for balanced decision-making
