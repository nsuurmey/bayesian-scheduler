# MVP0 Improvements Plan — Capacity Simulator

## Context
The source app is `capacity-simulator.jsx` — a single-file React component using Recharts,
with inline styles and a dark theme. It manages work items (projects/innovations/external)
with FTE and XIR budget tracking. The app currently uses ES module imports (`import { useState } from "react"`)
and `export default`, so it's meant for a bundled environment (e.g., Vite/Next.js).

We need to create this file in the repo at `mvp0/capacity-simulator.jsx` (matching the PRD's
referenced path) and apply the improvements.

---

## Step 1: Scaffold the MVP0 directory and place the source file

- Create `mvp0/capacity-simulator.jsx` with the provided source code
- No build system changes needed — this is a single component file

---

## Step 2: Remove "Scenario Insight" section (UI De-cluttering)

**What to remove:** The entire `<div>` block near the bottom of the component (lines ~280-295
in the source) that renders "Scenario Insight" — a dynamic text block that describes
pass-through vs budget-offset mode implications.

**Specific code to delete:**
```jsx
{/* Scenario Insight */}
<div style={{ ...sectionStyle, borderColor: COLORS.accent + "33", background: COLORS.accent + "08" }}>
  <div style={{ ...sectionTitle, color: COLORS.accent }}>Scenario Insight</div>
  ...entire block...
</div>
```

**Side effects:** None — this section is read-only display, no state dependencies flow from it.

---

## Step 3: Remove "External Revenue Pass-Through" toggle (UI De-cluttering)

**What to remove:**
1. The `passThrough` state variable: `const [passThrough, setPassThrough] = useState(false)`
2. The first `<Toggle>` component in the toggle section that controls `passThrough`
3. All logic branches that reference `passThrough`:
   - In `calcBudget` useMemo: the `if (passThrough && item.type === "external")` branch —
     default to always counting external XIR costs against budget (i.e., passThrough=false behavior)
   - In the work items table: the `{passThrough && item.type === "external" && (<span>PT</span>)}` indicator
   - In the XIR cost table cell: the conditional dimming `color: passThrough && item.type === "external" ? COLORS.textDim : COLORS.text`

**Default behavior after removal:** External XIR costs always count against budget
(the non-pass-through / "budget-offset" mode becomes the permanent default).

**Clean up the toggle container:** After removing the passThrough toggle, the section will only
contain the "Include Pipeline in Projections" toggle. Simplify the container `<div>` if needed,
or leave as-is since one toggle still remains.

---

## Step 4: Remove `extRevenue` field from AddItemModal and Inline Edit

Since the Revenue Pass-Through is removed and external revenue is a "noisy" field:
- Keep the `extRevenue` field in the data model (it's still shown in the table and KPI card)
- But the Toggle explanation references are already cleaned up in Step 3

**Decision:** Per the PRD, we only remove the toggle. The `extRevenue` data field, KPI card
("Ext Revenue"), and table column stay — they are core data, not configuration noise.
The PRD says "remove the toggle" not "remove external revenue tracking."

---

## Step 5: Add CSV Export ("Save Configuration")

**CSV Schema Design:**
```
version_id,1
setting,xirBudget,2000
setting,totalFte,19
setting,managementOverhead,4
setting,includePipeline,false
item,id,name,type,status,xirCost,fteLoad,startMonth,duration,extRevenue
item,1,Reservoir Characterization,project,committed,60,0.25,0,6,0
item,2,...
```

Using a "tagged row" format where the first column indicates the row type:
- `version_id` row: schema version for forward compatibility
- `setting` rows: global settings (key-value pairs)
- `item` header row: column names for work items
- `item` data rows: one per work item

**Implementation:**
1. Add a `CSV_VERSION = "1.0"` constant
2. Create `exportToCSV()` function:
   - Build CSV string with version, settings, and item rows
   - Use `Blob` + `URL.createObjectURL` + temporary `<a>` click to trigger download
   - Filename: `capacity-sim-YYYY-MM-DD.csv`
3. Add "Save Configuration" button in the header next to "Settings" and "+ Add Item"
4. Handle edge cases:
   - Item names containing commas → wrap all string fields in double quotes
   - Consistent number formatting (no locale-specific thousand separators)

---

## Step 6: Add CSV Import ("Import Configuration")

**Implementation:**
1. Create `importFromCSV(csvText)` function:
   - Parse CSV text into rows
   - Validate first row is `version_id` with a supported version
   - Extract settings rows and update `xirBudget`, `totalFte`, `managementOverhead`, `includePipeline`
   - Extract item rows by header mapping and rebuild items array
   - Return parsed state or throw with descriptive error message
2. Add hidden `<input type="file" accept=".csv">` element
3. Add "Import Configuration" button in the header that triggers the file input
4. On file select:
   - Read with `FileReader.readAsText()`
   - Call `importFromCSV()`
   - On success: `setItems()`, `setXirBudget()`, etc. — "hot reload" of all state
   - On error: show an inline error banner (not `alert()`) with the validation message
5. **Validation rules:**
   - version_id must be present and supported
   - All expected setting keys must be present
   - Item rows must have correct number of columns matching the header
   - Numeric fields must parse as valid numbers (reject "1,000.00" format — require plain numbers)
   - Type must be one of: project, innovation, external
   - Status must be one of: committed, pipeline, cut
   - startMonth must be 0-11, duration must be 1-12

---

## Step 7: Error handling UI for CSV import

Add a dismissible error/success banner component:
- Shows below the header after import attempt
- Green banner on success: "Configuration loaded: {N} items imported"
- Red banner on error: "Import failed: {specific error message}"
- Auto-dismiss after 5 seconds or manual close via × button

---

## Step 8: Final cleanup and testing considerations

- Verify the "Include Pipeline" toggle still works correctly in isolation
- Ensure `selectedItem` state is reset on CSV import (selected item ID may not exist in new data)
- Ensure `showAddModal` and `showSettings` are unaffected
- Confirm the chart, KPI cards, and table all re-render correctly after CSV import ("hot reload")

---

## File changes summary

| File | Action |
|------|--------|
| `mvp0/capacity-simulator.jsx` | CREATE — source with all modifications applied |

**No other files are modified.** This is a self-contained single-component change.

---

## Implementation order

1. Create `mvp0/capacity-simulator.jsx` with original source
2. Remove Scenario Insight section
3. Remove passThrough toggle + all references
4. Add CSV_VERSION constant and exportToCSV function
5. Add importFromCSV function with validation
6. Add Export/Import buttons to header
7. Add error/success banner component
8. Commit and push
