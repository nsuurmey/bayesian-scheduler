import { useState, useMemo, useCallback, useRef, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

const CSV_VERSION = "1.0";
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const CURRENT_MONTH = 2; // March = index 2
const COLORS = {
  bg: "#0f1419",
  surface: "#1a2028",
  surfaceHover: "#222d38",
  border: "#2a3642",
  borderLight: "#3a4a58",
  text: "#e8edf2",
  textMuted: "#8899aa",
  textDim: "#5a6a7a",
  accent: "#22c9a0",
  accentDim: "#1a9a7a",
  warning: "#f0a030",
  warningDim: "#a07020",
  danger: "#e05050",
  dangerDim: "#a03030",
  project: "#4a9eff",
  innovation: "#c084fc",
  external: "#f59e0b",
  committed: "#22c9a0",
  pipeline: "#f0a030",
  cut: "#5a6a7a",
};

const VALID_TYPES = ["project", "innovation", "external"];
const VALID_STATUSES = ["committed", "pipeline", "cut"];

const initialItems = [
  { id: 1, name: "Reservoir Characterization", type: "project", status: "committed", xirCost: 60, fteLoad: 0.25, startMonth: 0, duration: 6, extRevenue: 0 },
  { id: 2, name: "Well Placement Optimization", type: "project", status: "committed", xirCost: 80, fteLoad: 0.5, startMonth: 1, duration: 6, extRevenue: 0 },
  { id: 3, name: "Seismic Reprocessing QC", type: "project", status: "committed", xirCost: 45, fteLoad: 0.25, startMonth: 0, duration: 4, extRevenue: 0 },
  { id: 4, name: "Basin Screening Tool", type: "innovation", status: "committed", xirCost: 70, fteLoad: 1.0, startMonth: 1, duration: 4, extRevenue: 0 },
  { id: 5, name: "GenAI Document Extraction", type: "innovation", status: "committed", xirCost: 55, fteLoad: 1.5, startMonth: 0, duration: 3, extRevenue: 0 },
  { id: 6, name: "LLM Benchmarking Suite", type: "innovation", status: "committed", xirCost: 40, fteLoad: 1.0, startMonth: 2, duration: 3, extRevenue: 0 },
  { id: 7, name: "Asset Team Delta - Framing", type: "project", status: "pipeline", xirCost: 70, fteLoad: 0.25, startMonth: 3, duration: 6, extRevenue: 0 },
  { id: 8, name: "Asset Team Echo - Framing", type: "project", status: "pipeline", xirCost: 65, fteLoad: 0.25, startMonth: 3, duration: 6, extRevenue: 0 },
  { id: 9, name: "Asset Team Foxtrot - Framing", type: "project", status: "pipeline", xirCost: 55, fteLoad: 0.25, startMonth: 4, duration: 6, extRevenue: 0 },
  { id: 10, name: "Predictive Maintenance POC", type: "innovation", status: "pipeline", xirCost: 50, fteLoad: 1.5, startMonth: 4, duration: 4, extRevenue: 0 },
  { id: 11, name: "CI Tool v5 (GenAI)", type: "innovation", status: "pipeline", xirCost: 35, fteLoad: 1.0, startMonth: 3, duration: 3, extRevenue: 0 },
  { id: 12, name: "External - NOC Benchmarking", type: "external", status: "pipeline", xirCost: 120, fteLoad: 2.0, startMonth: 4, duration: 5, extRevenue: 350 },
  { id: 13, name: "External - Midstream Analytics", type: "external", status: "pipeline", xirCost: 45, fteLoad: 0.5, startMonth: 5, duration: 4, extRevenue: 120 },
];

const typeLabels = { project: "Project", innovation: "Innovation", external: "External" };

function generateId() {
  return Date.now() + Math.floor(Math.random() * 1000);
}

function escapeCSVField(value) {
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return str;
}

function parseCSVRow(line) {
  const fields = [];
  let current = "";
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (inQuotes) {
      if (ch === '"') {
        if (i + 1 < line.length && line[i + 1] === '"') {
          current += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        current += ch;
      }
    } else {
      if (ch === '"') {
        inQuotes = true;
      } else if (ch === ",") {
        fields.push(current);
        current = "";
      } else {
        current += ch;
      }
    }
  }
  fields.push(current);
  return fields;
}

function exportToCSV(items, settings) {
  const lines = [];
  lines.push(`version_id,${CSV_VERSION}`);
  lines.push(`setting,xirBudget,${settings.xirBudget}`);
  lines.push(`setting,totalFte,${settings.totalFte}`);
  lines.push(`setting,managementOverhead,${settings.managementOverhead}`);
  lines.push(`setting,includePipeline,${settings.includePipeline}`);
  lines.push("item,id,name,type,status,xirCost,fteLoad,startMonth,duration,extRevenue");
  items.forEach(item => {
    lines.push([
      "item",
      item.id,
      escapeCSVField(item.name),
      item.type,
      item.status,
      item.xirCost,
      item.fteLoad,
      item.startMonth,
      item.duration,
      item.extRevenue,
    ].join(","));
  });
  return lines.join("\n");
}

function importFromCSV(csvText) {
  const lines = csvText.trim().split(/\r?\n/).filter(l => l.trim());
  if (lines.length < 2) throw new Error("File is empty or too short");

  const firstRow = parseCSVRow(lines[0]);
  if (firstRow[0] !== "version_id") throw new Error("Missing version_id header — not a valid config file");
  if (firstRow[1] !== CSV_VERSION) throw new Error(`Unsupported version "${firstRow[1]}" (expected ${CSV_VERSION})`);

  const settings = {};
  const items = [];
  let itemHeaderFound = false;

  for (let i = 1; i < lines.length; i++) {
    const fields = parseCSVRow(lines[i]);
    const rowType = fields[0];

    if (rowType === "setting") {
      if (fields.length < 3) throw new Error(`Invalid setting row at line ${i + 1}`);
      const key = fields[1];
      const val = fields[2];
      if (key === "includePipeline") {
        settings[key] = val === "true";
      } else {
        const num = Number(val);
        if (isNaN(num)) throw new Error(`Setting "${key}" has invalid value "${val}" at line ${i + 1}`);
        settings[key] = num;
      }
    } else if (rowType === "item") {
      if (!itemHeaderFound) {
        itemHeaderFound = true;
        continue; // skip header row
      }
      if (fields.length < 10) throw new Error(`Item row has ${fields.length} columns, expected 10 at line ${i + 1}`);

      const id = Number(fields[1]);
      const name = fields[2];
      const type = fields[3];
      const status = fields[4];
      const xirCost = Number(fields[5]);
      const fteLoad = Number(fields[6]);
      const startMonth = Number(fields[7]);
      const duration = Number(fields[8]);
      const extRevenue = Number(fields[9]);

      if (!name.trim()) throw new Error(`Item at line ${i + 1} has empty name`);
      if (!VALID_TYPES.includes(type)) throw new Error(`Invalid type "${type}" at line ${i + 1} (expected: ${VALID_TYPES.join(", ")})`);
      if (!VALID_STATUSES.includes(status)) throw new Error(`Invalid status "${status}" at line ${i + 1} (expected: ${VALID_STATUSES.join(", ")})`);
      if (isNaN(xirCost)) throw new Error(`Invalid xirCost at line ${i + 1}`);
      if (isNaN(fteLoad)) throw new Error(`Invalid fteLoad at line ${i + 1}`);
      if (isNaN(startMonth) || startMonth < 0 || startMonth > 11) throw new Error(`Invalid startMonth "${fields[7]}" at line ${i + 1} (expected 0-11)`);
      if (isNaN(duration) || duration < 1 || duration > 12) throw new Error(`Invalid duration "${fields[8]}" at line ${i + 1} (expected 1-12)`);
      if (isNaN(extRevenue)) throw new Error(`Invalid extRevenue at line ${i + 1}`);

      items.push({ id: id || generateId(), name, type, status, xirCost, fteLoad, startMonth, duration, extRevenue });
    }
  }

  const requiredSettings = ["xirBudget", "totalFte", "managementOverhead", "includePipeline"];
  for (const key of requiredSettings) {
    if (!(key in settings)) throw new Error(`Missing required setting: ${key}`);
  }

  if (items.length === 0) throw new Error("No work items found in file");

  return { settings, items };
}

function Badge({ color, children }) {
  return (
    <span style={{
      display: "inline-block",
      padding: "2px 8px",
      borderRadius: 4,
      fontSize: 11,
      fontWeight: 600,
      letterSpacing: "0.03em",
      background: color + "22",
      color: color,
      border: `1px solid ${color}44`,
      textTransform: "uppercase",
    }}>
      {children}
    </span>
  );
}

function MetricCard({ label, value, sub, color, warn }) {
  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${warn ? COLORS.danger + "66" : COLORS.border}`,
      borderRadius: 8,
      padding: "16px 20px",
      flex: 1,
      minWidth: 160,
    }}>
      <div style={{ fontSize: 12, color: COLORS.textMuted, marginBottom: 6, fontWeight: 500, letterSpacing: "0.04em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || COLORS.text, fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: COLORS.textDim, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function Toggle({ checked, onChange, label, sublabel }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => onChange(!checked)}>
      <div style={{
        width: 48, height: 26, borderRadius: 13,
        background: checked ? COLORS.accent : COLORS.borderLight,
        transition: "background 0.2s",
        position: "relative",
        flexShrink: 0,
      }}>
        <div style={{
          width: 20, height: 20, borderRadius: 10,
          background: "#fff",
          position: "absolute",
          top: 3,
          left: checked ? 25 : 3,
          transition: "left 0.2s",
          boxShadow: "0 1px 3px rgba(0,0,0,0.3)",
        }} />
      </div>
      <div>
        <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.text }}>{label}</div>
        {sublabel && <div style={{ fontSize: 12, color: COLORS.textMuted }}>{sublabel}</div>}
      </div>
    </div>
  );
}

function Banner({ type, message, onDismiss }) {
  const isError = type === "error";
  const color = isError ? COLORS.danger : COLORS.accent;

  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div style={{
      padding: "10px 16px",
      background: color + "15",
      border: `1px solid ${color}44`,
      borderRadius: 8,
      fontSize: 13,
      color: color,
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 16,
    }}>
      <span>{isError ? "Import failed: " : ""}{message}</span>
      <button onClick={onDismiss} style={{
        background: "transparent", border: "none", color: color,
        cursor: "pointer", fontSize: 16, padding: "0 4px", marginLeft: 12,
      }}>x</button>
    </div>
  );
}

function AddItemModal({ onAdd, onClose }) {
  const [form, setForm] = useState({
    name: "", type: "project", status: "pipeline",
    xirCost: 60, fteLoad: 0.5, startMonth: CURRENT_MONTH,
    duration: 4, extRevenue: 0,
  });
  const update = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const inputStyle = {
    width: "100%", padding: "8px 12px", borderRadius: 6,
    border: `1px solid ${COLORS.border}`, background: COLORS.bg,
    color: COLORS.text, fontSize: 14, boxSizing: "border-box",
    outline: "none",
  };
  const labelStyle = { fontSize: 12, color: COLORS.textMuted, marginBottom: 4, display: "block", fontWeight: 500 };
  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
    }} onClick={onClose}>
      <div style={{
        background: COLORS.surface, borderRadius: 12, padding: 28, width: 420,
        border: `1px solid ${COLORS.border}`, maxHeight: "90vh", overflowY: "auto",
      }} onClick={e => e.stopPropagation()}>
        <h3 style={{ margin: "0 0 20px", color: COLORS.text, fontSize: 18 }}>Add Work Item</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <label style={labelStyle}>Name</label>
            <input style={inputStyle} value={form.name} onChange={e => update("name", e.target.value)} placeholder="e.g. Deepwater Analytics" />
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Type</label>
              <select style={inputStyle} value={form.type} onChange={e => update("type", e.target.value)}>
                <option value="project">Project</option>
                <option value="innovation">Innovation</option>
                <option value="external">External</option>
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Status</label>
              <select style={inputStyle} value={form.status} onChange={e => update("status", e.target.value)}>
                <option value="committed">Committed</option>
                <option value="pipeline">Pipeline</option>
                <option value="cut">Cut</option>
              </select>
            </div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>XIR Cost ($K)</label>
              <input style={inputStyle} type="number" value={form.xirCost} onChange={e => update("xirCost", +e.target.value)} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>FTE Load</label>
              <input style={inputStyle} type="number" step="0.25" value={form.fteLoad} onChange={e => update("fteLoad", +e.target.value)} />
            </div>
          </div>
          <div style={{ display: "flex", gap: 12 }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Start Month</label>
              <select style={inputStyle} value={form.startMonth} onChange={e => update("startMonth", +e.target.value)}>
                {MONTHS.map((m, i) => <option key={i} value={i}>{m}</option>)}
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Duration (months)</label>
              <input style={inputStyle} type="number" min={1} max={12} value={form.duration} onChange={e => update("duration", +e.target.value)} />
            </div>
          </div>
          {form.type === "external" && (
            <div>
              <label style={labelStyle}>External Revenue ($K)</label>
              <input style={inputStyle} type="number" value={form.extRevenue} onChange={e => update("extRevenue", +e.target.value)} />
            </div>
          )}
        </div>
        <div style={{ display: "flex", gap: 10, marginTop: 24, justifyContent: "flex-end" }}>
          <button onClick={onClose} style={{
            padding: "8px 20px", borderRadius: 6, border: `1px solid ${COLORS.border}`,
            background: "transparent", color: COLORS.textMuted, cursor: "pointer", fontSize: 14,
          }}>Cancel</button>
          <button onClick={() => { if (form.name.trim()) { onAdd({ ...form, id: generateId() }); onClose(); } }} style={{
            padding: "8px 20px", borderRadius: 6, border: "none",
            background: COLORS.accent, color: COLORS.bg, cursor: "pointer", fontSize: 14, fontWeight: 600,
          }}>Add Item</button>
        </div>
      </div>
    </div>
  );
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div style={{
      background: COLORS.surface, border: `1px solid ${COLORS.border}`,
      borderRadius: 8, padding: "12px 16px", fontSize: 13,
    }}>
      <div style={{ fontWeight: 600, color: COLORS.text, marginBottom: 6 }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.fill || p.color, marginBottom: 2 }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(1) : p.value}
        </div>
      ))}
      {d.fteCapacity && (
        <div style={{ color: COLORS.textDim, marginTop: 4, borderTop: `1px solid ${COLORS.border}`, paddingTop: 4 }}>
          Capacity: {d.fteCapacity} FTEs
        </div>
      )}
    </div>
  );
}

export default function CapacitySimulator() {
  const [items, setItems] = useState(initialItems);
  const [xirBudget, setXirBudget] = useState(2000);
  const [totalFte, setTotalFte] = useState(19);
  const [managementOverhead, setManagementOverhead] = useState(4);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [includePipeline, setIncludePipeline] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [banner, setBanner] = useState(null);
  const fileInputRef = useRef(null);

  const availableFte = totalFte - managementOverhead;

  const updateItem = useCallback((id, updates) => {
    setItems(prev => prev.map(item => item.id === id ? { ...item, ...updates } : item));
  }, []);

  const removeItem = useCallback((id) => {
    setItems(prev => prev.filter(item => item.id !== id));
    if (selectedItem === id) setSelectedItem(null);
  }, [selectedItem]);

  const handleExport = useCallback(() => {
    const csv = exportToCSV(items, { xirBudget, totalFte, managementOverhead, includePipeline });
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    const date = new Date().toISOString().slice(0, 10);
    a.href = url;
    a.download = `capacity-sim-${date}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [items, xirBudget, totalFte, managementOverhead, includePipeline]);

  const handleImport = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const result = importFromCSV(evt.target.result);
        setItems(result.items);
        setXirBudget(result.settings.xirBudget);
        setTotalFte(result.settings.totalFte);
        setManagementOverhead(result.settings.managementOverhead);
        setIncludePipeline(result.settings.includePipeline);
        setSelectedItem(null);
        setBanner({ type: "success", message: `Configuration loaded: ${result.items.length} items imported` });
      } catch (err) {
        setBanner({ type: "error", message: err.message });
      }
    };
    reader.readAsText(file);
    e.target.value = "";
  }, []);

  const activeItems = useMemo(() => items.filter(i => i.status !== "cut"), [items]);
  const committedItems = useMemo(() => items.filter(i => i.status === "committed"), [items]);

  const calcBudget = useMemo(() => {
    const viewItems = includePipeline ? activeItems : committedItems;
    let totalXir = 0;
    let totalExtRev = 0;
    viewItems.forEach(item => {
      totalXir += item.xirCost;
      if (item.type === "external") totalExtRev += item.extRevenue;
    });
    const remaining = xirBudget - totalXir;
    const pct = ((totalXir / xirBudget) * 100);
    return { totalXir, remaining, pct, totalExtRev };
  }, [activeItems, committedItems, includePipeline, xirBudget]);

  const monthlyData = useMemo(() => {
    const viewItems = includePipeline ? activeItems : committedItems;
    return MONTHS.map((month, i) => {
      let projectFte = 0, innovationFte = 0, externalFte = 0;
      viewItems.forEach(item => {
        const end = item.startMonth + item.duration;
        if (i >= item.startMonth && i < end) {
          if (item.type === "project") projectFte += item.fteLoad;
          else if (item.type === "innovation") innovationFte += item.fteLoad;
          else externalFte += item.fteLoad;
        }
      });
      return {
        month, idx: i,
        projectFte: Math.round(projectFte * 100) / 100,
        innovationFte: Math.round(innovationFte * 100) / 100,
        externalFte: Math.round(externalFte * 100) / 100,
        totalFte: Math.round((projectFte + innovationFte + externalFte) * 100) / 100,
        fteCapacity: availableFte,
        isPast: i < CURRENT_MONTH,
      };
    });
  }, [activeItems, committedItems, includePipeline, availableFte]);

  const okrStatus = useMemo(() => {
    const committedProjects = items.filter(i => i.type === "project" && i.status === "committed").length;
    const pipelineProjects = items.filter(i => i.type === "project" && i.status === "pipeline").length;
    const committedInnovations = items.filter(i => i.type === "innovation" && i.status === "committed").length;
    const pipelineInnovations = items.filter(i => i.type === "innovation" && i.status === "pipeline").length;
    const extRev = items.filter(i => i.type === "external" && i.status !== "cut")
      .reduce((s, i) => s + i.extRevenue, 0);
    return {
      committedProjects, pipelineProjects, totalProjects: committedProjects + pipelineProjects,
      committedInnovations, pipelineInnovations, totalInnovations: committedInnovations + pipelineInnovations,
      extRev,
    };
  }, [items]);

  const typeColor = { project: COLORS.project, innovation: COLORS.innovation, external: COLORS.external };
  const statusColor = { committed: COLORS.committed, pipeline: COLORS.pipeline, cut: COLORS.cut };

  const sectionStyle = {
    background: COLORS.surface,
    border: `1px solid ${COLORS.border}`,
    borderRadius: 10,
    padding: 24,
    marginBottom: 20,
  };

  const sectionTitle = {
    fontSize: 13, fontWeight: 600, color: COLORS.textMuted,
    textTransform: "uppercase", letterSpacing: "0.06em",
    marginBottom: 16,
  };

  const headerBtnStyle = {
    padding: "8px 16px", borderRadius: 6, border: `1px solid ${COLORS.border}`,
    background: "transparent", color: COLORS.textMuted, cursor: "pointer", fontSize: 13,
  };

  return (
    <div style={{
      background: COLORS.bg, color: COLORS.text, minHeight: "100vh",
      fontFamily: "'Segoe UI', -apple-system, sans-serif",
      padding: "24px 32px",
      maxWidth: 1100, margin: "0 auto",
    }}>
      {/* Hidden file input for CSV import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        style={{ display: "none" }}
        onChange={handleImport}
      />

      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: COLORS.text, letterSpacing: "-0.02em" }}>
              Capacity Simulator
            </h1>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: COLORS.textDim }}>
              FY 2026 · {MONTHS[CURRENT_MONTH]} onwards · {totalFte} total FTEs ({availableFte} deployable)
            </p>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button onClick={() => fileInputRef.current?.click()} style={headerBtnStyle}>Import</button>
            <button onClick={handleExport} style={headerBtnStyle}>Export</button>
            <button onClick={() => setShowSettings(!showSettings)} style={{
              ...headerBtnStyle,
              background: showSettings ? COLORS.surfaceHover : "transparent",
            }}>Settings</button>
            <button onClick={() => setShowAddModal(true)} style={{
              padding: "8px 16px", borderRadius: 6, border: "none",
              background: COLORS.accent, color: COLORS.bg, cursor: "pointer",
              fontSize: 13, fontWeight: 600,
            }}>+ Add Item</button>
          </div>
        </div>
      </div>

      {/* Import/Export Banner */}
      {banner && (
        <Banner
          type={banner.type}
          message={banner.message}
          onDismiss={() => setBanner(null)}
        />
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div style={{ ...sectionStyle, background: COLORS.bg, border: `1px solid ${COLORS.borderLight}` }}>
          <div style={sectionTitle}>Global Settings</div>
          <div style={{ display: "flex", gap: 24, flexWrap: "wrap", alignItems: "flex-end" }}>
            {[
              { label: "XIR Budget ($K)", value: xirBudget, onChange: setXirBudget },
              { label: "Total FTEs", value: totalFte, onChange: setTotalFte },
              { label: "Mgmt / Overhead FTEs", value: managementOverhead, onChange: setManagementOverhead },
            ].map(({ label, value, onChange }) => (
              <div key={label}>
                <label style={{ fontSize: 12, color: COLORS.textMuted, display: "block", marginBottom: 4 }}>{label}</label>
                <input type="number" value={value} onChange={e => onChange(+e.target.value)} style={{
                  width: 120, padding: "6px 10px", borderRadius: 6,
                  border: `1px solid ${COLORS.border}`, background: COLORS.surface,
                  color: COLORS.text, fontSize: 14,
                }} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* View Toggle */}
      <div style={{ ...sectionStyle, display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 16 }}>
        <Toggle
          checked={includePipeline}
          onChange={setIncludePipeline}
          label="Include Pipeline in Projections"
          sublabel={includePipeline ? "Showing committed + pipeline items" : "Showing committed only"}
        />
      </div>

      {/* KPI Cards */}
      <div style={{ display: "flex", gap: 14, marginBottom: 20, flexWrap: "wrap" }}>
        <MetricCard
          label="XIR Remaining"
          value={`$${calcBudget.remaining.toLocaleString()}K`}
          sub={`${(100 - calcBudget.pct).toFixed(0)}% of $${xirBudget.toLocaleString()}K`}
          color={calcBudget.remaining < 300 ? COLORS.danger : calcBudget.remaining < 600 ? COLORS.warning : COLORS.accent}
          warn={calcBudget.remaining < 300}
        />
        <MetricCard
          label="Projects"
          value={`${okrStatus.committedProjects} / 25`}
          sub={`+${okrStatus.pipelineProjects} in pipeline`}
          color={COLORS.project}
        />
        <MetricCard
          label="Innovations"
          value={`${okrStatus.committedInnovations} / 6`}
          sub={`+${okrStatus.pipelineInnovations} in pipeline`}
          color={COLORS.innovation}
        />
        <MetricCard
          label="Ext Revenue"
          value={`$${okrStatus.extRev}K`}
          sub={`Target: $2,500K`}
          color={COLORS.external}
        />
      </div>

      {/* Monthly FTE Chart */}
      <div style={sectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div style={sectionTitle}>Monthly FTE Utilization</div>
          <div style={{ display: "flex", gap: 16, fontSize: 12 }}>
            {[["Projects", COLORS.project], ["Innovations", COLORS.innovation], ["External", COLORS.external]].map(([l, c]) => (
              <div key={l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                <div style={{ width: 10, height: 10, borderRadius: 2, background: c }} />
                <span style={{ color: COLORS.textMuted }}>{l}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ height: 260 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={monthlyData} margin={{ top: 10, right: 10, bottom: 0, left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={COLORS.border} vertical={false} />
              <XAxis dataKey="month" tick={{ fill: COLORS.textMuted, fontSize: 12 }} axisLine={{ stroke: COLORS.border }} tickLine={false} />
              <YAxis tick={{ fill: COLORS.textMuted, fontSize: 12 }} axisLine={false} tickLine={false} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={availableFte} stroke={COLORS.danger} strokeDasharray="6 3" label={{ value: `Capacity: ${availableFte}`, fill: COLORS.danger, fontSize: 11, position: "right" }} />
              <Bar dataKey="projectFte" stackId="a" fill={COLORS.project} name="Projects" radius={[0, 0, 0, 0]} />
              <Bar dataKey="innovationFte" stackId="a" fill={COLORS.innovation} name="Innovations" radius={[0, 0, 0, 0]} />
              <Bar dataKey="externalFte" stackId="a" fill={COLORS.external} name="External" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {monthlyData.some(d => d.totalFte > availableFte) && (
          <div style={{ marginTop: 10, padding: "8px 14px", background: COLORS.danger + "15", border: `1px solid ${COLORS.danger}33`, borderRadius: 6, fontSize: 13, color: COLORS.danger }}>
            Over-capacity detected in {monthlyData.filter(d => d.totalFte > availableFte).map(d => d.month).join(", ")}
          </div>
        )}
      </div>

      {/* Work Items Table */}
      <div style={sectionStyle}>
        <div style={sectionTitle}>Work Items</div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                {["Name", "Type", "Status", "XIR ($K)", "FTEs", "Start", "Duration", "Ext Rev ($K)", ""].map(h => (
                  <th key={h} style={{ textAlign: "left", padding: "8px 10px", color: COLORS.textDim, fontWeight: 500, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id}
                  style={{
                    borderBottom: `1px solid ${COLORS.border}22`,
                    opacity: item.status === "cut" ? 0.4 : 1,
                    background: selectedItem === item.id ? COLORS.surfaceHover : "transparent",
                    cursor: "pointer",
                    transition: "background 0.15s",
                  }}
                  onClick={() => setSelectedItem(selectedItem === item.id ? null : item.id)}
                  onMouseEnter={e => { if (selectedItem !== item.id) e.currentTarget.style.background = COLORS.surfaceHover + "88"; }}
                  onMouseLeave={e => { if (selectedItem !== item.id) e.currentTarget.style.background = "transparent"; }}
                >
                  <td style={{ padding: "10px 10px", fontWeight: 500, color: COLORS.text, maxWidth: 220 }}>{item.name}</td>
                  <td style={{ padding: "10px 10px" }}><Badge color={typeColor[item.type]}>{typeLabels[item.type]}</Badge></td>
                  <td style={{ padding: "10px 10px" }}>
                    <select
                      value={item.status}
                      onChange={e => { e.stopPropagation(); updateItem(item.id, { status: e.target.value }); }}
                      onClick={e => e.stopPropagation()}
                      style={{
                        background: "transparent", border: `1px solid ${statusColor[item.status]}44`,
                        color: statusColor[item.status], borderRadius: 4, padding: "3px 6px",
                        fontSize: 12, cursor: "pointer", fontWeight: 600, outline: "none",
                      }}
                    >
                      <option value="committed" style={{ background: COLORS.surface }}>Committed</option>
                      <option value="pipeline" style={{ background: COLORS.surface }}>Pipeline</option>
                      <option value="cut" style={{ background: COLORS.surface }}>Cut</option>
                    </select>
                  </td>
                  <td style={{ padding: "10px 10px", fontFamily: "monospace" }}>{item.xirCost}</td>
                  <td style={{ padding: "10px 10px", fontFamily: "monospace" }}>{item.fteLoad}</td>
                  <td style={{ padding: "10px 10px", color: COLORS.textMuted }}>{MONTHS[item.startMonth]}</td>
                  <td style={{ padding: "10px 10px", fontFamily: "monospace", color: COLORS.textMuted }}>{item.duration}mo</td>
                  <td style={{ padding: "10px 10px", fontFamily: "monospace", color: item.extRevenue ? COLORS.external : COLORS.textDim }}>
                    {item.extRevenue || "\u2014"}
                  </td>
                  <td style={{ padding: "10px 10px" }}>
                    <button
                      onClick={e => { e.stopPropagation(); removeItem(item.id); }}
                      style={{
                        background: "transparent", border: "none", color: COLORS.textDim,
                        cursor: "pointer", fontSize: 16, padding: "2px 6px", borderRadius: 4,
                      }}
                      onMouseEnter={e => e.target.style.color = COLORS.danger}
                      onMouseLeave={e => e.target.style.color = COLORS.textDim}
                    >x</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Inline Edit for Selected Item */}
      {selectedItem && (() => {
        const item = items.find(i => i.id === selectedItem);
        if (!item) return null;
        const inputStyle = {
          width: "100%", padding: "6px 10px", borderRadius: 6,
          border: `1px solid ${COLORS.border}`, background: COLORS.bg,
          color: COLORS.text, fontSize: 13, boxSizing: "border-box", outline: "none",
        };
        const lblStyle = { fontSize: 11, color: COLORS.textDim, marginBottom: 3, display: "block", textTransform: "uppercase" };
        return (
          <div style={{ ...sectionStyle, borderColor: COLORS.accent + "44" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <div style={{ ...sectionTitle, margin: 0 }}>Edit: {item.name}</div>
              <button onClick={() => setSelectedItem(null)} style={{ background: "transparent", border: "none", color: COLORS.textMuted, cursor: "pointer", fontSize: 18 }}>x</button>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr 1fr", gap: 12, alignItems: "end" }}>
              <div style={{ gridColumn: "span 2" }}>
                <label style={lblStyle}>Name</label>
                <input style={inputStyle} value={item.name} onChange={e => updateItem(item.id, { name: e.target.value })} />
              </div>
              <div>
                <label style={lblStyle}>XIR ($K)</label>
                <input style={inputStyle} type="number" value={item.xirCost} onChange={e => updateItem(item.id, { xirCost: +e.target.value })} />
              </div>
              <div>
                <label style={lblStyle}>FTE Load</label>
                <input style={inputStyle} type="number" step="0.25" value={item.fteLoad} onChange={e => updateItem(item.id, { fteLoad: +e.target.value })} />
              </div>
              <div>
                <label style={lblStyle}>Start</label>
                <select style={inputStyle} value={item.startMonth} onChange={e => updateItem(item.id, { startMonth: +e.target.value })}>
                  {MONTHS.map((m, i) => <option key={i} value={i}>{m}</option>)}
                </select>
              </div>
              <div>
                <label style={lblStyle}>Duration</label>
                <input style={inputStyle} type="number" min={1} max={12} value={item.duration} onChange={e => updateItem(item.id, { duration: +e.target.value })} />
              </div>
              {item.type === "external" && (
                <div>
                  <label style={lblStyle}>Ext Revenue ($K)</label>
                  <input style={inputStyle} type="number" value={item.extRevenue} onChange={e => updateItem(item.id, { extRevenue: +e.target.value })} />
                </div>
              )}
            </div>
          </div>
        );
      })()}

      {showAddModal && <AddItemModal onAdd={(item) => setItems(prev => [...prev, item])} onClose={() => setShowAddModal(false)} />}
    </div>
  );
}
