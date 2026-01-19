# Test Data Files for Project Scheduling Toolkit

This directory contains several test JSON files designed to verify different aspects of the Project Scheduling Toolkit's functionality.

## Test Files Overview

### 1. `test-data-basic.json`
**Purpose:** Simple baseline test with minimal, clean data
**What it tests:**
- Basic project display and navigation
- Simple filtering and sorting
- Mix of scheduled and unscheduled projects
- Different project stages (Signed, Frontier)
- Basic observations functionality

**Key Stats:**
- 3 projects (2 scheduled, 1 unscheduled)
- Low resource utilization (well under capacity)
- Capacity: 10 DS, 5 GS, 2 PM

**Expected Results:**
- ✅ Capacity indicator should show GREEN across all resources
- ✅ Timeline view should show 2 bars with no overlaps
- ✅ Forecast view should show low utilization in all scenarios

---

### 2. `test-data-overallocated.json`
**Purpose:** Stress test for resource overallocation detection
**What it tests:**
- Capacity indicator RED warnings
- Overlapping project scheduling
- Resource bottlenecks (especially PM capacity)
- Multiple projects competing for same resources
- Resource allocation charts showing overallocation

**Key Stats:**
- 5 projects (all scheduled)
- **INTENTIONALLY OVERALLOCATED** resources
- Capacity: 5 DS, 3 GS, 2 PM (very constrained)

**Expected Results:**
- ⚠️ Capacity indicator should show RED for DS and PM (weeks 5-12)
- ⚠️ Resource allocation charts should exceed capacity lines
- ⚠️ Multiple projects should overlap on timeline
- ✅ Warnings about resource conflicts in observations

**Test Focus Areas:**
- Week 7-12: DS should be at 7 (capacity is 5) = **140% overallocated**
- Week 6-15: PM should be at 3 (capacity is 2) = **150% overallocated**
- Week 8-12: GS should be at 4 (capacity is 3) = **133% overallocated**

---

### 3. `test-data-probability-scenarios.json`
**Purpose:** Test probability-weighted forecasting across all stages
**What it tests:**
- Four forecast scenarios (Committed, High Confidence, Expected, Full Pipeline)
- Probability adjustments from default values
- Mix of all four project stages
- Observation-based probability justification
- Capacity planning under different assumptions

**Key Stats:**
- 10 projects distributed across all stages:
  - 3 Signed (95%)
  - 2 Close to Signing (70%)
  - 2 Interested (40% and 50%)
  - 3 Frontier (10%, 15%, 25%)
- Capacity: 20 DS, 10 GS, 5 PM

**Expected Results:**
- ✅ **Committed Only:** Should show only 3 signed projects
- ✅ **High Confidence:** Should include 5 projects (Signed + Close to Signing)
- ✅ **Expected Case:** Should calculate probability-weighted totals
- ✅ **Full Pipeline:** Should show all 10 projects (100% assumption)
- ✅ Significant difference between scenarios demonstrates value of probability tracking

**Example Expected Calculations (Data Scientists):**
- Committed: (5×10) + (4×8) + (3×6) = 100 person-weeks
- Expected: (5×10×0.95) + (4×8×0.95) + (3×6×0.95) + (6×12×0.70) + (3×6×0.70) + (4×8×0.50) + (5×16×0.15) + (3×10×0.25) + (8×20×0.10) = ~229 person-weeks
- Full Pipeline: All projects at 100% = 386 person-weeks

---

### 4. `test-data-edge-cases.json`
**Purpose:** Test unusual scenarios and boundary conditions
**What it tests:**
- Extreme durations (1 week minimum, 52 weeks maximum)
- Zero resource projects
- Maximum resource projects
- Project dependencies
- Probability extremes (0% and 100%)
- Many observations (UI overflow handling)
- Late-year scheduling (week 50+)
- Multiple dependencies to same parent project

**Key Stats:**
- 12 projects with unusual characteristics
- Capacity: 12 DS, 6 GS, 3 PM

**Specific Edge Cases:**
| Project | Edge Case | What to Verify |
|---------|-----------|----------------|
| Tiny Sprint Project | 1-week duration | Displays correctly, doesn't break timeline |
| Marathon Year-Long | 52-week duration | Spans entire timeline correctly |
| Zero Resource | 0 DS, 0 GS, 0 PM | Doesn't affect capacity calculations |
| Resource Intensive | 10 DS, 5 GS, 3 PM | Nearly maxes all resource types |
| Late Year Start | Starts week 50 | Handles year-end correctly |
| Foundation Project | Has dependents | Dependency tracking works |
| Dependent Alpha/Beta | Lists dependencies | Shows dependency tags |
| Probability 0% | 0% probability | Doesn't contribute to Expected Case |
| Probability 100% | 100% probability | Contributes fully even if Frontier |
| Maximum Observations | 5 positive, 5 negative | "Show all" expansion works |
| All Resource Types | 3 of each | Tests balanced resource usage |

**Expected Results:**
- ✅ All edge cases display without errors
- ✅ Dependencies shown as tags in project detail
- ✅ Observations panel handles 10+ items with expansion
- ✅ 0% probability project doesn't affect Expected Case forecast
- ✅ 100% probability project contributes fully regardless of stage

---

### 5. `test-data-bayesian-updates.json`
**Purpose:** Demonstrate Bayesian probability updating in action
**What it tests:**
- Automatic probability updates when observations are added
- Likelihood ratio calculations (High, Medium, Low)
- Probability history tracking
- Multiple sequential updates
- Positive and negative evidence effects
- Edge cases approaching 1% and 99% bounds

**Key Stats:**
- 8 projects demonstrating different update scenarios
- Each project shows complete probability history
- Capacity: 15 DS, 8 GS, 3 PM

**Demonstration Scenarios:**

| Project | Scenario | Initial → Final | Key Learning |
|---------|----------|----------------|--------------|
| Single Positive Update Demo | One positive-high observation | 40% → 57% (+17%) | High likelihood doubles odds |
| Single Negative Update Demo | One negative-high observation | 70% → 54% (-16%) | High likelihood halves odds |
| Multiple Updates - Net Positive | Mixed observations, net positive | 40% → 58% (+18%) | Sequential updates compound |
| Multiple Updates - Net Negative | Mixed observations, net negative | 70% → 49% (-21%) | Negative signals can overwhelm |
| Frontier to Interested Progression | Stage change with updates | 15% → 47% (+32%) | Frontier projects can gain confidence |
| Extreme Case - Very Low | Multiple negatives → floor | 15% → 4% (near 1% floor) | Bounded at 1% minimum |
| Extreme Case - Very High | Multiple positives → ceiling | 70% → 93% (near 99% ceiling) | Bounded at 99% maximum |
| Mixed Signals - Oscillating | Many conflicting observations | 40% → 48% (+8%) | Conflicting evidence creates noise |

**Expected Results:**
- ✅ Probability History section visible in project detail modals
- ✅ Each history entry shows: probability, change amount, likelihood ratio, timestamp
- ✅ Green (+) for increases, red (-) for decreases
- ✅ Most recent updates appear at top of history
- ✅ Projects demonstrate proper Bayesian calculations

**Calculation Verification:**

Example from "Single Positive Update Demo":
```
Initial: 40% (Interested stage)
Observation: "Executive sponsor committed" (Positive, High)

Step 1: Convert to odds
  Odds = 0.40 / (1 - 0.40) = 0.40 / 0.60 = 0.667

Step 2: Apply likelihood ratio (Positive High = 2.0)
  New Odds = 0.667 × 2.0 = 1.333

Step 3: Convert back to probability
  P = 1.333 / (1 + 1.333) = 1.333 / 2.333 = 0.571 = 57%

Result: 40% → 57% (+17%)
✅ Matches project data
```

**How to Verify Bayesian Updates:**
1. Load this test file
2. Click any project name to open detail modal
3. Scroll to "Probability History" section
4. Verify each update shows:
   - Prior probability
   - Likelihood ratio (LR)
   - Posterior probability
   - Change amount with +/- indicator
5. Add a new observation to see live Bayesian update
6. Confirm prompt shows calculation before applying

---

## How to Use These Test Files

### Method 1: Via the Application UI
1. Open `project-scheduler-FIXED.html` in your browser
2. Click **"Import JSON"** button in the header
3. Select one of the test JSON files
4. Choose **"Replace all"** to load the test data
5. Explore different tabs to verify functionality

### Method 2: Quick Switching Between Test Files
1. Load first test file using Import
2. Explore and verify functionality
3. Load next test file (it will replace the previous data)
4. Repeat for all test files

### Method 3: Keep Browser Console Open
1. Press F12 to open browser developer tools
2. Check Console tab for any JavaScript errors
3. Load each test file and verify no errors appear

---

## Verification Checklist

Use this checklist to verify the application works correctly with each test file:

### ✅ Basic Functionality (test with `test-data-basic.json`)
- [ ] All 3 projects appear in Project List tab
- [ ] Clicking project name opens detail modal
- [ ] Filtering by "Scheduled/Unscheduled" works
- [ ] Sorting columns works
- [ ] Timeline shows 2 scheduled projects
- [ ] Unscheduled projects appear in left sidebar
- [ ] All 4 tabs load without errors

### ⚠️ Capacity Warnings (test with `test-data-overallocated.json`)
- [ ] Capacity indicator shows RED for overallocated resources
- [ ] Resource Allocation charts show bars exceeding capacity line
- [ ] Timeline view shows overlapping projects
- [ ] Forecast view shows overallocation in scenarios

### 📊 Forecast Scenarios (test with `test-data-probability-scenarios.json`)
- [ ] Committed Only shows only Signed projects
- [ ] High Confidence includes Signed + Close to Signing
- [ ] Expected Case shows weighted values (smaller than Full Pipeline)
- [ ] Full Pipeline shows largest numbers
- [ ] Progress bars correctly indicate capacity utilization
- [ ] Red warning appears for overallocated scenarios

### 🔬 Edge Cases (test with `test-data-edge-cases.json`)
- [ ] 1-week project displays correctly
- [ ] 52-week project spans entire timeline
- [ ] Zero-resource project doesn't affect capacity
- [ ] Dependencies appear as tags in project detail
- [ ] Projects with 10 observations show "Show all" expansion
- [ ] 0% probability project visible but doesn't affect Expected Case
- [ ] 100% probability project contributes fully to Expected Case

---

## Expected Calculation Examples

### Capacity Indicator Calculation (Overallocated Test)
```
Week 7-12 Data Scientists:
- Overlapping Project 1: 4 DS (weeks 5-12)
- Overlapping Project 2: 3 DS (weeks 7-12)
Total: 7 DS (capacity is 5)
Display: "DS: 7/5 (140%)" in RED
```

### Forecast Scenario Calculation Example
```
Expected Case (Probability-Weighted):
Project A: 5 DS × 10 weeks × 95% = 47.5 person-weeks
Project B: 6 DS × 12 weeks × 70% = 50.4 person-weeks
Project C: 4 DS × 8 weeks × 40% = 12.8 person-weeks
Project D: 5 DS × 16 weeks × 15% = 12.0 person-weeks
Total Expected: 122.7 person-weeks

Full Pipeline (Everything at 100%):
Same projects = 5×10 + 6×12 + 4×8 + 5×16 = 234 person-weeks
```

---

## Troubleshooting

### If import fails:
1. Check browser console for errors
2. Verify JSON file is valid (paste into jsonlint.com)
3. Ensure you're using `project-scheduler-FIXED.html` (not the original)

### If charts don't display:
1. The fixed version uses custom charts (not Recharts)
2. Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)
3. Clear browser cache

### If data doesn't load:
1. Try "Replace all" option instead of "Merge"
2. Clear localStorage: Open console and run `localStorage.clear()`
3. Reload the page

---

## Creating Your Own Test Files

To create a custom test file:

1. Load any test file into the application
2. Modify projects using the UI
3. Click **"Export JSON"**
4. Save the file with a descriptive name
5. Use it for future testing

**Template structure:**
```json
{
  "settings": { ... },
  "projects": [ ... ],
  "ui": { ... }
}
```

Refer to any of the provided test files for the complete schema.

---

## Questions or Issues?

If you find issues with the test files or the application:
1. Check the browser console for JavaScript errors
2. Verify you're using the latest version (`project-scheduler-FIXED.html`)
3. Try each test file systematically
4. Note which specific feature or test case fails
