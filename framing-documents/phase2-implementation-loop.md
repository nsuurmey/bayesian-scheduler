# Phase 2 Implementation Loop

**Model:** Claude Sonnet (claude-sonnet-4-5)
**Repo:** bayesian-scheduler
**Scope:** Resource Allocation tab enhancements (FR1, FR2, FR3 — see `bayesian-scheduler-feature2-prd.md`)

---

## How Each Loop Works

1. **Ticket selection** — State which ticket(s) to work on and paste any relevant code snippets.
2. **Implementation plan** — A brief, numbered plan is generated and shown for review.
3. **Prompts proposed** — Exact Claude Code prompts are proposed before execution.
4. **Execution + diff** — Code is written/edited and a unified diff is shown.
   - For single tickets: diff shown at completion.
   - For vertical slices: diff shown per ticket; execution continues automatically unless a risk was flagged in the plan.
5. **Verification** — Manual browser checklist confirms acceptance criteria.

---

## Template 1 — Implement a Single Ticket

```
## Ticket: [FR#] [Short Title]

### Context
- File: `project-scheduler-FIXED.html`
- PRD section: [e.g., FR1: Reversed Stack Order (Maturity)]
- Relevant line range(s): [e.g., L1499–L1700 (Resource Allocation component)]

### What already exists
[Paste the current implementation snippet or describe the current behavior]

### Acceptance criteria (from PRD)
- [ ] [Criterion 1 — exact quote or paraphrase from PRD]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### Implementation plan
1. [Step 1 — e.g., "Sort the series array so 'Assigned' is index 0 before passing to d3.stack()"]
2. [Step 2]
3. [Step 3]

### Constraints / do-not-touch
- Do not alter components outside the Resource Allocation tab
- Preserve all existing data structures and state shape
- Keep all code within the single HTML file

### Verification checklist (manual, browser-based)
- [ ] [Check 1]
- [ ] [Check 2]

### Prompt to execute
> In `project-scheduler-FIXED.html`, implement [FR#] as described above.
> Make only the changes listed in the implementation plan.
> Show a unified diff when done.
```

---

## Template 2 — Vertical Slice (Multiple Tickets)

```
## Vertical Slice: [Short Description, e.g., "Color + Stack + Legend"]

### Tickets included
| Ticket | Title | Priority |
|--------|-------|----------|
| FR1    | Reversed Stack Order | Must |
| FR2    | Dynamic Color Toggle | Must |
| FR3    | Enhanced Tooltips & Legend | Should |

### Shared context
- File: `project-scheduler-FIXED.html`
- Shared state shape changes: [e.g., add `colorBy: 'status' | 'project'` to component state]
- Shared helpers/utilities: [e.g., `getProjectColorScale()` used by FR2 and FR3]

### Sequencing rationale
[Explain why tickets are ordered this way — e.g., "FR1 is a prerequisite for FR2's coloring
to render correctly."]

### Per-ticket acceptance criteria
**FR1:** [criteria]
**FR2:** [criteria]
**FR3:** [criteria]

### Risk flags (pause here for approval if flagged)
- [ ] [Risk 1 — e.g., "FR2 state shape change may conflict with existing settings serialization"]
- [ ] [Risk 2]

### Integration seam
[Describe how the tickets connect — e.g., "The `colorBy` dropdown state introduced in FR2
must be read by both the bar renderer (FR2) and the legend renderer (FR3)."]

### Verification checklist (manual, browser-based)
- [ ] [Check covering FR1]
- [ ] [Check covering FR2]
- [ ] [Check covering FR3]
- [ ] [End-to-end scenario]

### Prompt to execute
> In `project-scheduler-FIXED.html`, implement [FR1, FR2, FR3] as a coherent vertical slice.
> Sequence changes in the order stated. Introduce only the shared state and helpers described above.
> Show a diff per ticket. Pause for explicit approval only at flagged risks; otherwise continue.
```

---

## Template 3 — Refactor / Integration Pass

```
## Refactor Pass: [Short Description, e.g., "Consolidate Resource Allocation rendering logic"]

### Trigger
[Why this pass is needed — e.g., "FR1–FR3 were implemented; color logic is now duplicated
in three places."]

### Files in scope
- `project-scheduler-FIXED.html` — lines [X–Y] (Resource Allocation component)

### Out of scope
- Other tabs (Gantt, Settings, etc.)
- Data loading / CSV parsing logic

### Goals
- [ ] [Goal 1 — e.g., "Extract `buildColorScale(colorBy, projects)` into a single function"]
- [ ] [Goal 2 — e.g., "Remove duplicated maturity-sort logic; call one `sortBySeries()` helper"]
- [ ] [Goal 3 — e.g., "Ensure legend and tooltip reference the same scale instance"]

### Non-goals (explicitly out of scope)
- No behavior changes — this pass must be functionally inert
- No new features

### Verification checklist (manual, browser-based)
- [ ] Stack order still shows Assigned at bottom, Frontier on top
- [ ] Color toggle switches correctly between palettes
- [ ] Tooltips show full project name + hours + status
- [ ] Legend scrolls when project count overflows
- [ ] All other tabs unaffected

### Prompt to execute
> Refactor the Resource Allocation component in `project-scheduler-FIXED.html`
> to achieve the goals listed above. Make no behavior changes.
> Show a unified diff and explicitly flag any line where behavior might have shifted.
```

---

## Adopted Defaults (Phase 2)

| Setting | Value |
|---------|-------|
| Diff review cadence | Per-ticket; auto-continue unless a risk was flagged in the plan |
| Testing approach | Manual browser checklist (no automated test suite) |
| File scope | `project-scheduler-FIXED.html` unless stated otherwise |
| Model | Claude Sonnet |
| Branch | `claude/switch-to-sonnet-sg3PD` |
