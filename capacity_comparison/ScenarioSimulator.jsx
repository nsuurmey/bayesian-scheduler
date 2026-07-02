import React, { useState, useMemo } from "react";

// ---- Planning window ----------------------------------------------------

// Rest of calendar year 2026. To use the full year instead, swap in:
// const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const MONTHS = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// ---- Seed data ----------------------------------------------------------

const SEED_PEOPLE = [
  {
    id: "ana",
    name: "Ana",
    role: "Sr Data Scientist",
    capacity: 1.0,
    timeOff: [
      { month: 1, availability: 0.0 }, // Aug — out
      { month: 5, availability: 0.5 }, // Dec — half
    ],
  },
  {
    id: "ben",
    name: "Ben",
    role: "Data Scientist",
    capacity: 1.0,
    timeOff: [],
  },
  {
    id: "carla",
    name: "Carla",
    role: "Geoscientist",
    capacity: 1.0,
    timeOff: [],
  },
  {
    id: "dan",
    name: "Dan",
    role: "Data Scientist",
    capacity: 1.0,
    timeOff: [
      { month: 0, availability: 0.5 }, // Jul — half
    ],
  },
  {
    id: "eve",
    name: "Eve",
    role: "Project Manager",
    capacity: 1.0,
    timeOff: [],
  },
];

const SEED_PROJECTS = [
  {
    id: "okr-a",
    name: "OKR Push A",
    status: "committed",
    startMonth: 0, // Jul
    endMonth: 3, // Oct
    allocations: [
      { personId: "ana", load: 0.6 },
      { personId: "ben", load: 0.5 },
    ],
  },
  {
    id: "okr-b",
    name: "OKR Push B",
    status: "committed",
    startMonth: 0, // Jul
    endMonth: 3, // Oct
    allocations: [
      { personId: "carla", load: 0.5 },
      { personId: "dan", load: 0.6 },
    ],
  },
  {
    id: "client-x",
    name: "External Client X",
    status: "likely",
    startMonth: 2, // Sep
    endMonth: 5, // Dec
    allocations: [
      { personId: "ana", load: 0.5 },
      { personId: "dan", load: 0.4 },
      { personId: "eve", load: 0.3 },
    ],
  },
  {
    id: "client-y",
    name: "External Client Y",
    status: "speculative",
    startMonth: 3, // Oct
    endMonth: 5, // Dec
    allocations: [
      { personId: "ben", load: 0.6 },
      { personId: "carla", load: 0.5 },
    ],
  },
  {
    id: "inbound",
    name: "New Inbound Lead",
    status: "speculative",
    startMonth: 4, // Nov
    endMonth: 5, // Dec
    allocations: [
      { personId: "ana", load: 0.4 },
      { personId: "eve", load: 0.5 },
    ],
  },
];

const STATUS_WEIGHT = {
  committed: 1.0,
  likely: 0.6,
  speculative: 0.3,
  off: 0,
};

const STATUS_OPTIONS = [
  { key: "committed", label: "Committed" },
  { key: "likely", label: "Likely" },
  { key: "speculative", label: "Speculative" },
  { key: "off", label: "Off" },
];

const STATUS_BADGE_CLASS = {
  committed: "bg-slate-900 text-white",
  likely: "bg-slate-500 text-white",
  speculative: "bg-slate-300 text-slate-700",
  off: "bg-slate-100 text-slate-400",
};

let idCounter = 1;
function makeId(prefix) {
  idCounter += 1;
  return `${prefix}-${Date.now().toString(36)}-${idCounter}`;
}

// ---- Helpers --------------------------------------------------------------

function fmt(n) {
  return (Math.round(n * 100) / 100).toString();
}

function clampLoad(n) {
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

function clampCapacity(n) {
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(2, n));
}

function loadColor(load, capacity) {
  const ratio = capacity > 0 ? load / capacity : load > 0 ? Infinity : 0;
  if (ratio > 1.2) return { bar: "bg-red-500", text: "text-red-700", chip: "bg-red-50 text-red-700 border-red-200" };
  if (ratio > 1.0) return { bar: "bg-amber-500", text: "text-amber-700", chip: "bg-amber-50 text-amber-700 border-amber-200" };
  return { bar: "bg-emerald-500", text: "text-emerald-700", chip: "bg-emerald-50 text-emerald-700 border-emerald-200" };
}

// cell-shade version of the same thresholds, for the month grid
function cellColorClasses(load, capacity) {
  const ratio = capacity > 0 ? load / capacity : load > 0 ? Infinity : 0;
  if (ratio > 1.2) return "bg-red-100 text-red-800 border-red-200";
  if (ratio > 1.0) return "bg-amber-100 text-amber-800 border-amber-200";
  if (load === 0) return "bg-slate-50 text-slate-300 border-slate-100";
  return "bg-emerald-50 text-emerald-800 border-emerald-100";
}

function getAvailability(person, month) {
  const entry = person.timeOff?.find((t) => t.month === month);
  return entry ? entry.availability : 1.0;
}

// ---- Component --------------------------------------------------------------

export default function ScenarioSimulator() {
  const [people, setPeople] = useState(SEED_PEOPLE);
  const [projects, setProjects] = useState(SEED_PROJECTS);
  const [showAddPerson, setShowAddPerson] = useState(false);
  const [showAddProject, setShowAddProject] = useState(false);

  // ---- Person mutations ----
  function addPerson({ name, role, capacity }) {
    const trimmed = name.trim();
    if (!trimmed) return;
    setPeople((prev) => [
      ...prev,
      {
        id: makeId("person"),
        name: trimmed,
        role: role.trim() || "Team Member",
        capacity: clampCapacity(capacity),
        timeOff: [],
      },
    ]);
    setShowAddPerson(false);
  }

  function updatePerson(personId, field, value) {
    setPeople((prev) =>
      prev.map((p) => (p.id === personId ? { ...p, [field]: value } : p))
    );
  }

  function removePerson(personId) {
    setPeople((prev) => prev.filter((p) => p.id !== personId));
    setProjects((prev) =>
      prev.map((proj) => ({
        ...proj,
        allocations: proj.allocations.filter((a) => a.personId !== personId),
      }))
    );
  }

  // ---- Project mutations ----
  function addProject({ name, status }) {
    const trimmed = name.trim();
    if (!trimmed) return;
    setProjects((prev) => [
      ...prev,
      {
        id: makeId("project"),
        name: trimmed,
        status: status || "speculative",
        startMonth: 0,
        endMonth: MONTHS.length - 1,
        allocations: [],
      },
    ]);
    setShowAddProject(false);
  }

  function removeProject(projectId) {
    setProjects((prev) => prev.filter((p) => p.id !== projectId));
  }

  function updateProjectField(projectId, field, value) {
    setProjects((prev) =>
      prev.map((p) => (p.id === projectId ? { ...p, [field]: value } : p))
    );
  }

  function updateProjectSpan(projectId, newStart, newEnd) {
    setProjects((prev) =>
      prev.map((p) =>
        p.id === projectId ? { ...p, startMonth: newStart, endMonth: newEnd } : p
      )
    );
  }

  function addAllocation(projectId, personId, load) {
    if (!personId) return;
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== projectId) return proj;
        const exists = proj.allocations.some((a) => a.personId === personId);
        if (exists) {
          return {
            ...proj,
            allocations: proj.allocations.map((a) =>
              a.personId === personId ? { ...a, load: clampLoad(load) } : a
            ),
          };
        }
        return {
          ...proj,
          allocations: [...proj.allocations, { personId, load: clampLoad(load) }],
        };
      })
    );
  }

  function updateAllocationLoad(projectId, personId, load) {
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== projectId) return proj;
        return {
          ...proj,
          allocations: proj.allocations.map((a) =>
            a.personId === personId ? { ...a, load: clampLoad(load) } : a
          ),
        };
      })
    );
  }

  function removeAllocation(projectId, personId) {
    setProjects((prev) =>
      prev.map((proj) => {
        if (proj.id !== projectId) return proj;
        return {
          ...proj,
          allocations: proj.allocations.filter((a) => a.personId !== personId),
        };
      })
    );
  }

  const personNameById = useMemo(() => {
    const m = {};
    people.forEach((p) => (m[p.id] = p));
    return m;
  }, [people]);

  // ---- Per-month load & capacity grids ----
  const loadGrid = useMemo(() => {
    const grid = {};
    people.forEach((p) => {
      grid[p.id] = {};
      MONTHS.forEach((_, m) => (grid[p.id][m] = 0));
    });
    projects.forEach((proj) => {
      const weight = STATUS_WEIGHT[proj.status] ?? 0;
      if (weight === 0) return;
      for (let m = proj.startMonth; m <= proj.endMonth; m++) {
        proj.allocations.forEach((a) => {
          if (grid[a.personId] === undefined) return;
          grid[a.personId][m] += a.load * weight;
        });
      }
    });
    return grid;
  }, [people, projects]);

  const capacityGrid = useMemo(() => {
    const grid = {};
    people.forEach((p) => {
      grid[p.id] = {};
      MONTHS.forEach((_, m) => {
        grid[p.id][m] = p.capacity * getAvailability(p, m);
      });
    });
    return grid;
  }, [people]);

  // ---- Month-level rollups & the tightest month ----
  const monthStats = useMemo(() => {
    return MONTHS.map((_, m) => {
      let demand = 0;
      let capacityTotal = 0;
      let overCount = 0;
      people.forEach((p) => {
        const load = loadGrid[p.id]?.[m] ?? 0;
        const cap = capacityGrid[p.id]?.[m] ?? 0;
        demand += load;
        capacityTotal += cap;
        if (load > cap) overCount += 1;
      });
      return { month: m, demand, capacityTotal, overCount };
    });
  }, [people, loadGrid, capacityGrid]);

  const worstMonth = useMemo(() => {
    if (monthStats.length === 0) return null;
    return monthStats.reduce((best, cur) =>
      cur.overCount > best.overCount ? cur : best
    );
  }, [monthStats]);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 p-4 sm:p-6 lg:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-slate-900">
            Scenario Simulator
          </h1>
          <p className="mt-1 text-sm text-slate-500 max-w-2xl">
            Toggle project commitment and duration to see expected staffing
            load month by month, not just worst case. Weighting: Committed
            ×1.0, Likely ×0.6, Speculative ×0.3, Off ×0. Planning window:{" "}
            {MONTHS[0]}–{MONTHS[MONTHS.length - 1]} 2026.
          </p>
        </div>

        {/* Summary strip */}
        <SummaryStrip
          peopleCount={people.length}
          monthStats={monthStats}
          worstMonth={worstMonth}
        />

        {/* Two-column layout */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: project cards */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Projects
              </h2>
              <button
                type="button"
                onClick={() => setShowAddProject((v) => !v)}
                className="text-xs font-medium px-2.5 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-100 hover:border-slate-400 transition-colors"
              >
                {showAddProject ? "Cancel" : "+ Add project"}
              </button>
            </div>

            {showAddProject && (
              <AddProjectForm onAdd={addProject} onCancel={() => setShowAddProject(false)} />
            )}

            <div className="space-y-3">
              {projects.map((proj) => (
                <ProjectCard
                  key={proj.id}
                  project={proj}
                  people={people}
                  personNameById={personNameById}
                  onStatusChange={(status) => updateProjectField(proj.id, "status", status)}
                  onNameChange={(name) => updateProjectField(proj.id, "name", name)}
                  onSpanChange={(start, end) => updateProjectSpan(proj.id, start, end)}
                  onRemoveProject={() => removeProject(proj.id)}
                  onAddAllocation={(personId, load) => addAllocation(proj.id, personId, load)}
                  onUpdateAllocation={(personId, load) => updateAllocationLoad(proj.id, personId, load)}
                  onRemoveAllocation={(personId) => removeAllocation(proj.id, personId)}
                />
              ))}
              {projects.length === 0 && (
                <div className="text-sm text-slate-400 border border-dashed border-slate-300 rounded-lg p-4 text-center">
                  No projects yet. Add one to get started.
                </div>
              )}
            </div>
          </div>

          {/* Right: capacity readout */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Capacity Readout
              </h2>
              <button
                type="button"
                onClick={() => setShowAddPerson((v) => !v)}
                className="text-xs font-medium px-2.5 py-1 rounded-md border border-slate-300 text-slate-600 hover:bg-slate-100 hover:border-slate-400 transition-colors"
              >
                {showAddPerson ? "Cancel" : "+ Add person"}
              </button>
            </div>

            {showAddPerson && (
              <AddPersonForm onAdd={addPerson} onCancel={() => setShowAddPerson(false)} />
            )}

            <CapacityGrid
              people={people}
              loadGrid={loadGrid}
              capacityGrid={capacityGrid}
              onUpdatePerson={updatePerson}
              onRemovePerson={removePerson}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// ---- Subcomponents --------------------------------------------------------------

function SummaryStrip({ peopleCount, monthStats, worstMonth }) {
  const hasData = peopleCount > 0 && worstMonth;
  const flagText = !hasData
    ? "Add people to see staffing signal."
    : worstMonth.overCount === 0
    ? "Everyone is within capacity across the whole window."
    : `Tightest month: ${MONTHS[worstMonth.month]} — ${worstMonth.overCount} ${
        worstMonth.overCount === 1 ? "person is" : "people are"
      } over capacity — hire or deprioritize.`;

  const flagClass =
    !hasData || worstMonth.overCount === 0
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : "bg-red-50 text-red-800 border-red-200";

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <StatCard
          label="Tightest month"
          value={hasData ? MONTHS[worstMonth.month] : "—"}
        />
        <StatCard
          label="Overallocated that month"
          value={hasData ? `${worstMonth.overCount} / ${peopleCount}` : "—"}
        />
        <div
          className={`rounded-lg border px-4 py-3 flex items-center text-sm font-medium ${flagClass}`}
        >
          {flagText}
        </div>
      </div>

      {/* per-month at-a-glance strip */}
      {peopleCount > 0 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {monthStats.map((ms) => {
            const isWorst = worstMonth && ms.month === worstMonth.month;
            const tone =
              ms.overCount === 0
                ? "bg-white border-slate-200 text-slate-500"
                : "bg-red-50 border-red-200 text-red-700";
            return (
              <div
                key={ms.month}
                className={`shrink-0 rounded-md border px-2.5 py-1.5 text-xs ${tone} ${
                  isWorst ? "ring-2 ring-red-300" : ""
                }`}
                title={`${fmt(ms.demand)} / ${fmt(ms.capacityTotal)} FTE demand`}
              >
                <div className="font-semibold">{MONTHS[ms.month]}</div>
                <div className="tabular-nums">{ms.overCount} over</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-slate-400">
        {label}
      </div>
      <div className="mt-1 text-lg font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function AddPersonForm({ onAdd, onCancel }) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("");
  const [capacity, setCapacity] = useState("1.0");

  function submit(e) {
    e.preventDefault();
    onAdd({ name, role, capacity: parseFloat(capacity) });
    setName("");
    setRole("");
    setCapacity("1.0");
  }

  return (
    <form
      onSubmit={submit}
      className="mb-3 bg-white border border-slate-200 rounded-lg p-3 flex flex-col sm:flex-row gap-2 sm:items-end"
    >
      <div className="flex-1">
        <label className="block text-[11px] font-medium text-slate-500 mb-0.5">
          Name
        </label>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Farid"
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>
      <div className="flex-1">
        <label className="block text-[11px] font-medium text-slate-500 mb-0.5">
          Role
        </label>
        <input
          value={role}
          onChange={(e) => setRole(e.target.value)}
          placeholder="e.g. Data Scientist"
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>
      <div className="w-24">
        <label className="block text-[11px] font-medium text-slate-500 mb-0.5">
          Capacity
        </label>
        <input
          type="number"
          step="0.1"
          min="0"
          max="2"
          value={capacity}
          onChange={(e) => setCapacity(e.target.value)}
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!name.trim()}
          className="text-sm font-medium px-3 py-1.5 rounded-md bg-slate-900 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors"
        >
          Add
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm font-medium px-3 py-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-100 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function AddProjectForm({ onAdd, onCancel }) {
  const [name, setName] = useState("");
  const [status, setStatus] = useState("speculative");

  function submit(e) {
    e.preventDefault();
    onAdd({ name, status });
    setName("");
    setStatus("speculative");
  }

  return (
    <form
      onSubmit={submit}
      className="mb-3 bg-white border border-slate-200 rounded-lg p-3 flex flex-col sm:flex-row gap-2 sm:items-end"
    >
      <div className="flex-1">
        <label className="block text-[11px] font-medium text-slate-500 mb-0.5">
          Project name
        </label>
        <input
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Genesis Mission Pilot"
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-400"
        />
      </div>
      <div className="w-40">
        <label className="block text-[11px] font-medium text-slate-500 mb-0.5">
          Status
        </label>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-full text-sm border border-slate-300 rounded px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-slate-400 bg-white"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.key} value={opt.key}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!name.trim()}
          className="text-sm font-medium px-3 py-1.5 rounded-md bg-slate-900 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors"
        >
          Add
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="text-sm font-medium px-3 py-1.5 rounded-md border border-slate-300 text-slate-500 hover:bg-slate-100 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

function ProjectCard({
  project,
  people,
  personNameById,
  onStatusChange,
  onNameChange,
  onSpanChange,
  onRemoveProject,
  onAddAllocation,
  onUpdateAllocation,
  onRemoveAllocation,
}) {
  const weight = STATUS_WEIGHT[project.status];
  const allocatedIds = new Set(project.allocations.map((a) => a.personId));
  const availablePeople = people.filter((p) => !allocatedIds.has(p.id));

  const [pendingPersonId, setPendingPersonId] = useState("");
  const [pendingLoad, setPendingLoad] = useState("0.5");

  function handleAddAllocation() {
    if (!pendingPersonId) return;
    onAddAllocation(pendingPersonId, parseFloat(pendingLoad));
    setPendingPersonId("");
    setPendingLoad("0.5");
  }

  function handleStartChange(e) {
    const newStart = parseInt(e.target.value, 10);
    const newEnd = Math.max(project.endMonth, newStart);
    onSpanChange(newStart, newEnd);
  }

  function handleEndChange(e) {
    const newEnd = parseInt(e.target.value, 10);
    const newStart = Math.min(project.startMonth, newEnd);
    onSpanChange(newStart, newEnd);
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <input
            value={project.name}
            onChange={(e) => onNameChange(e.target.value)}
            className="font-medium text-slate-900 w-full bg-transparent border-b border-transparent hover:border-slate-200 focus:border-slate-400 focus:outline-none px-0 py-0.5 -ml-0.5"
          />
          <div className="flex items-center flex-wrap gap-1.5 mt-1">
            <div
              className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded ${STATUS_BADGE_CLASS[project.status]}`}
            >
              {STATUS_OPTIONS.find((s) => s.key === project.status)?.label}
              {weight > 0 && <span className="ml-1 opacity-70">×{weight}</span>}
            </div>
            <div className="inline-block text-[11px] font-medium px-2 py-0.5 rounded bg-slate-50 text-slate-500 border border-slate-200">
              {MONTHS[project.startMonth]}–{MONTHS[project.endMonth]}
            </div>
          </div>
        </div>
        <button
          type="button"
          onClick={onRemoveProject}
          title="Remove project"
          className="text-slate-300 hover:text-red-500 transition-colors text-lg leading-none px-1"
        >
          ×
        </button>
      </div>

      {/* Segmented control */}
      <div className="mt-3 inline-flex rounded-md border border-slate-200 bg-slate-50 p-0.5 text-xs">
        {STATUS_OPTIONS.map((opt) => {
          const active = project.status === opt.key;
          return (
            <button
              key={opt.key}
              type="button"
              onClick={() => onStatusChange(opt.key)}
              className={`px-2.5 py-1 rounded transition-colors ${
                active
                  ? "bg-white text-slate-900 shadow-sm font-medium"
                  : "text-slate-500 hover:text-slate-800"
              }`}
              aria-pressed={active}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Duration control */}
      <div className="mt-2.5 flex items-center gap-2">
        <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wide">
          Span
        </span>
        <select
          value={project.startMonth}
          onChange={handleStartChange}
          className="text-xs border border-slate-300 rounded px-1.5 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i}>
              {m}
            </option>
          ))}
        </select>
        <span className="text-slate-400 text-xs">–</span>
        <select
          value={project.endMonth}
          onChange={handleEndChange}
          className="text-xs border border-slate-300 rounded px-1.5 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
        >
          {MONTHS.map((m, i) => (
            <option key={m} value={i}>
              {m}
            </option>
          ))}
        </select>
      </div>

      {/* Allocations */}
      <ul className="mt-3 space-y-1.5">
        {project.allocations.map((a) => {
          const person = personNameById[a.personId];
          const effective = a.load * weight;
          return (
            <li
              key={a.personId}
              className="flex items-center gap-2 text-sm text-slate-600 group"
            >
              <span className="flex-1 truncate">
                {person ? person.name : "Unknown"}
              </span>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={a.load}
                onChange={(e) =>
                  onUpdateAllocation(a.personId, parseFloat(e.target.value))
                }
                className="w-16 text-sm border border-slate-200 rounded px-1.5 py-0.5 text-right tabular-nums focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
              {weight < 1 && (
                <span className="text-xs text-slate-400 w-14 tabular-nums">
                  → {fmt(effective)}
                </span>
              )}
              {weight === 1 && <span className="w-14" />}
              <button
                type="button"
                onClick={() => onRemoveAllocation(a.personId)}
                title="Remove allocation"
                className="text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 px-1"
              >
                ×
              </button>
            </li>
          );
        })}
        {project.allocations.length === 0 && (
          <li className="text-xs text-slate-400 italic">No one staffed yet.</li>
        )}
      </ul>

      {/* Add allocation row */}
      {availablePeople.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2">
          <select
            value={pendingPersonId}
            onChange={(e) => setPendingPersonId(e.target.value)}
            className="flex-1 text-sm border border-slate-300 rounded px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-slate-400"
          >
            <option value="">Add person…</option>
            {availablePeople.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
          <input
            type="number"
            step="0.1"
            min="0"
            max="1"
            value={pendingLoad}
            onChange={(e) => setPendingLoad(e.target.value)}
            className="w-16 text-sm border border-slate-300 rounded px-1.5 py-1 text-right tabular-nums focus:outline-none focus:ring-2 focus:ring-slate-400"
          />
          <button
            type="button"
            onClick={handleAddAllocation}
            disabled={!pendingPersonId}
            className="text-sm font-medium px-2.5 py-1 rounded-md bg-slate-900 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-800 transition-colors"
          >
            Add
          </button>
        </div>
      )}
    </div>
  );
}

function CapacityGrid({ people, loadGrid, capacityGrid, onUpdatePerson, onRemovePerson }) {
  if (people.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm text-slate-400 text-center">
        No people yet. Add someone to start staffing.
      </div>
    );
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-slate-200">
            <th className="text-left font-medium text-slate-500 text-xs uppercase tracking-wide px-3 py-2 sticky left-0 bg-white">
              Person
            </th>
            {MONTHS.map((m) => (
              <th
                key={m}
                className="text-center font-medium text-slate-500 text-xs uppercase tracking-wide px-1.5 py-2 min-w-[52px]"
              >
                {m}
              </th>
            ))}
            <th className="px-2 py-2" />
          </tr>
        </thead>
        <tbody>
          {people.map((person) => (
            <tr key={person.id} className="border-b border-slate-100 last:border-b-0 group">
              <td className="px-3 py-2 sticky left-0 bg-white align-top">
                <input
                  value={person.name}
                  onChange={(e) => onUpdatePerson(person.id, "name", e.target.value)}
                  className="font-medium text-slate-900 text-sm bg-transparent border-b border-transparent hover:border-slate-200 focus:border-slate-400 focus:outline-none w-24"
                />
                <div className="flex items-center gap-1.5 mt-0.5">
                  <input
                    value={person.role}
                    onChange={(e) => onUpdatePerson(person.id, "role", e.target.value)}
                    className="text-slate-400 text-xs bg-transparent border-b border-transparent hover:border-slate-200 focus:border-slate-400 focus:outline-none w-24"
                  />
                </div>
                <div className="flex items-center gap-1 mt-1">
                  <span className="text-[10px] text-slate-400">cap</span>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={person.capacity}
                    onChange={(e) =>
                      onUpdatePerson(person.id, "capacity", clampCapacity(parseFloat(e.target.value)))
                    }
                    className="w-12 text-[11px] font-semibold border border-slate-200 rounded px-1 py-0.5 text-right tabular-nums focus:outline-none focus:ring-2 focus:ring-slate-400"
                  />
                </div>
              </td>
              {MONTHS.map((_, m) => {
                const load = loadGrid[person.id]?.[m] ?? 0;
                const capacity = capacityGrid[person.id]?.[m] ?? 0;
                const availability = getAvailability(person, m);
                return (
                  <MonthCell
                    key={m}
                    load={load}
                    capacity={capacity}
                    availability={availability}
                  />
                );
              })}
              <td className="px-2 py-2 align-top">
                <button
                  type="button"
                  onClick={() => onRemovePerson(person.id)}
                  title="Remove person"
                  className="text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100 text-lg leading-none px-1"
                >
                  ×
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-3 py-2 text-[11px] text-slate-400 border-t border-slate-100">
        Hatched cells mark reduced availability (PTO / partial). Numbers are
        weighted monthly load vs. that month's effective capacity.
      </div>
    </div>
  );
}

function MonthCell({ load, capacity, availability }) {
  const isOff = availability < 1;
  const toneClass = isOff
    ? "bg-slate-100 text-slate-500 border-slate-200"
    : cellColorClasses(load, capacity);

  const style = isOff
    ? {
        backgroundImage:
          "repeating-linear-gradient(45deg, rgba(100,116,139,0.15), rgba(100,116,139,0.15) 4px, transparent 4px, transparent 8px)",
      }
    : undefined;

  return (
    <td className="px-1 py-2 align-top">
      <div
        className={`rounded border text-center py-1.5 ${toneClass}`}
        style={style}
        title={`${fmt(load)} / ${fmt(capacity)} FTE`}
      >
        <div className="text-xs font-semibold tabular-nums">{fmt(load)}</div>
        {isOff && (
          <div className="text-[9px] uppercase tracking-wide leading-none mt-0.5">
            {availability === 0 ? "PTO" : `${Math.round(availability * 100)}%`}
          </div>
        )}
      </div>
    </td>
  );
}
