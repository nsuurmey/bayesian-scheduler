# PRD: Resource Allocation Enhancements

**Project:** Project Scheduling Toolkit

**Component:** Resource Allocation Tab

**Status:** Draft

## 1. Executive Summary

The goal of this update is to improve the decision-making utility of the Resource Allocation bar charts. By reversing the stacking order and adding dynamic coloring by Project Name, users will be able to better distinguish between committed work and speculative "Frontier" deals, while also identifying specific project distributions at a glance.

## 2. Feature Requirements

### FR1: Reversed Stack Order (Maturity)

* **Current State:** Bars are stacked by maturity (Assigned vs. Frontier), but the ordering is inconsistent or reversed.
* **Requirement:** The stacking logic must be explicitly set so that **Assigned** deals form the base of the bar (bottom), and **Frontier** deals are stacked on top.
* **User Value:** Provides a "firm ground" visual. If the "Assigned" section already nears capacity, the "Frontier" blocks visually signal an immediate need to prioritize or drop upcoming discussions.

### FR2: Dynamic Color Toggle (Project Name)

* **Requirement:** Add a dropdown selector to the UI that allows the user to toggle the bar color scheme between:
1. **Status/Maturity** (Default: e.g., Blue for Assigned, Orange for Frontier).
2. **Project Name** (Unique colors assigned per project).


* **Logic:** When "Project Name" is selected, the stacking order from FR1 must still be maintained, but individual segments within the stack should be colored by their respective project IDs.

### FR3: Enhanced Tooltips & Legend

* **Full Name Tooltips:** Hovering over any bar segment must display the **Full Project Name**, alongside its hours/resource impact and status.
* **Scrollable Legend:** * The legend at the bottom of the chart must support horizontal or vertical scrolling (depending on layout).
* It must accommodate long project names without clipping or breaking the chart container’s aspect ratio.



## 3. User Interface (UI) Considerations

* **The Dropdown:** Place the "Color By" dropdown in the top-right utility tray of the Resource Allocation tab.
* **Legend UX:** Ensure the scrollbar in the legend is thin and unobtrusive, appearing only when the number of projects or character count exceeds the container width.

---

## 4. Technical Notes

* **D3.js / Charting Lib:** Ensure the `stack` generator is passed a sorted array where "Assigned" occupies the 0-index of the series.
* **Color Palettes:** If "Project Name" is selected, use a high-contrast categorical palette (e.g., d3.schemeCategory10) to ensure distinct projects are easily viewable.

---

Would you like me to take a crack at the **JavaScript/HTML logic** for that stacking reversal, or perhaps draft the **CSS** for the scrollable legend?