import { useState, useEffect, useCallback } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

// ─── API CONFIG ────────────────────────────────────────────────
const API_BASE = "http://localhost:8000/api/v1";

// ─── MOCK DATA (fallback khi API chưa sẵn sàng) ────────────────
const MOCK = {
  summary: {
    total_records: 36450,
    total_platforms: 3,
    total_labeled: 10000,
    total_models: 3,
    platform_stats: [
      { platform: "tiktok",   total_records: 12450, vietnamese_records: 11200 },
      { platform: "threads",  total_records: 8320,  vietnamese_records: 7890 },
      { platform: "facebook", total_records: 15680, vietnamese_records: 14900 },
    ],
    crawl_timeline: [
      { month: "01/24", tiktok: 1200, threads: 0,    facebook: 1800 },
      { month: "02/24", tiktok: 2100, threads: 1200,  facebook: 2400 },
      { month: "03/24", tiktok: 2800, threads: 1800,  facebook: 3100 },
      { month: "04/24", tiktok: 2500, threads: 2100,  facebook: 3500 },
      { month: "05/24", tiktok: 2400, threads: 1980,  facebook: 3200 },
      { month: "06/24", tiktok: 1450, threads: 1240,  facebook: 1680 },
    ],
  },
  dataset: {
    total_labeled: 10000,
    data: [
      { split_set: "train", total_records: 8000, ratio: 0.80,
        platforms: { tiktok: 3000, threads: 2000, facebook: 3000 },
        labels: { normal: 4500, hate_speech: 2100, offensive: 1400 } },
      { split_set: "test",  total_records: 2000, ratio: 0.20,
        platforms: { tiktok: 740, threads: 480, facebook: 780 },
        labels: { normal: 1130, hate_speech: 540, offensive: 330 } },
    ],
  },
  models: [
    {
      model_id: "model-001", model_display_name: "TF-IDF + SVM",
      model_type: "traditional", version: "v1.0",
      accuracy: 0.7823, macro_f1: 0.7615, weighted_f1: 0.7702,
      macro_precision: 0.7798, macro_recall: 0.7750,
      target_hate_f1: 0.7221, target_offensive_f1: 0.6805, target_normal_f1: 0.8122,
      confusion_matrix: [[1254,178,88],[52,228,32],[28,24,116]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
    },
    {
      model_id: "model-002", model_display_name: "TF-IDF + LR",
      model_type: "traditional", version: "v1.0",
      accuracy: 0.8015, macro_f1: 0.7832, weighted_f1: 0.7910,
      macro_precision: 0.8034, macro_recall: 0.7978,
      target_hate_f1: 0.7370, target_offensive_f1: 0.6973, target_normal_f1: 0.8344,
      confusion_matrix: [[1252,180,88],[45,234,33],[22,30,116]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
    },
    {
      model_id: "model-003", model_display_name: "PhoBERT",
      model_type: "deep_learning", version: "v1.0",
      accuracy: 0.8934, macro_f1: 0.8823, weighted_f1: 0.8876,
      macro_precision: 0.8945, macro_recall: 0.8890,
      target_hate_f1: 0.8732, target_offensive_f1: 0.8612, target_normal_f1: 0.9122,
      confusion_matrix: [[1370,98,52],[22,276,14],[12,14,142]],
      train_ratio: 0.80, test_ratio: 0.20, total_samples: 10000,
    },
  ],
};

// ─── DESIGN TOKENS ─────────────────────────────────────────────
const PLATFORM_COLORS = { tiktok: "#00f2ea", threads: "#a78bfa", facebook: "#60a5fa" };
const PLATFORM_ICONS  = { tiktok: "𝕋", threads: "@", facebook: "𝐟" };
const LABEL_COLORS    = { normal: "#34d399", hate_speech: "#f87171", offensive: "#fb923c" };
const MODEL_COLORS    = ["#38bdf8", "#a78bfa", "#f472b6"];
const CONF_COLORS     = ["#1e293b","#1e3a5f","#1e4d2f","#1e293b"];

// ─── UTILITY ───────────────────────────────────────────────────
const pct = (v) => `${(v * 100).toFixed(1)}%`;
const fmt = (n) => n?.toLocaleString("vi-VN") ?? "—";

async function fetchAPI(path) {
  try {
    const r = await fetch(`${API_BASE}${path}`);
    if (!r.ok) throw new Error(r.statusText);
    const j = await r.json();
    return j.data ?? j;
  } catch {
    return null;
  }
}

// ─── STAT CARD ─────────────────────────────────────────────────
function StatCard({ label, value, sub, accent = "#38bdf8", icon }) {
  return (
    <div style={{
      background: "linear-gradient(135deg,#0f172a 60%,#1e293b)",
      border: `1px solid ${accent}30`,
      borderRadius: 16, padding: "22px 26px",
      boxShadow: `0 0 24px ${accent}18`,
      display: "flex", flexDirection: "column", gap: 6,
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <span style={{ fontSize: 13, color: "#64748b", letterSpacing: "0.08em", textTransform: "uppercase" }}>
          {label}
        </span>
        <span style={{ fontSize: 22 }}>{icon}</span>
      </div>
      <span style={{ fontSize: 36, fontWeight: 800, color: accent, fontVariantNumeric: "tabular-nums" }}>
        {value}
      </span>
      {sub && <span style={{ fontSize: 12, color: "#475569" }}>{sub}</span>}
    </div>
  );
}

// ─── SECTION HEADER ────────────────────────────────────────────
function SectionHeader({ title, badge }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
      <div style={{ width: 4, height: 22, background: "linear-gradient(#38bdf8,#a78bfa)", borderRadius: 4 }} />
      <h2 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: "#f1f5f9" }}>{title}</h2>
      {badge && (
        <span style={{
          background: "#38bdf820", color: "#38bdf8", border: "1px solid #38bdf840",
          borderRadius: 20, fontSize: 11, padding: "2px 10px", fontWeight: 600,
        }}>{badge}</span>
      )}
    </div>
  );
}

// ─── CUSTOM TOOLTIP ────────────────────────────────────────────
function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "#0f172a", border: "1px solid #334155", borderRadius: 10, padding: "10px 14px" }}>
      <p style={{ margin: "0 0 6px", color: "#94a3b8", fontSize: 12 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ margin: 0, color: p.color, fontSize: 13, fontWeight: 600 }}>
          {p.name}: {fmt(p.value)}
        </p>
      ))}
    </div>
  );
}

// ─── CONFUSION MATRIX ──────────────────────────────────────────
function ConfusionMatrix({ matrix, modelName }) {
  const labels = ["Normal", "Hate", "Offensive"];
  if (!matrix?.length) return null;
  const max = Math.max(...matrix.flat());
  return (
    <div>
      <p style={{ margin: "0 0 10px", fontSize: 12, color: "#64748b", textAlign: "center" }}>
        Confusion Matrix — {modelName}
      </p>
      <div style={{ display: "grid", gridTemplateColumns: `60px repeat(3,1fr)`, gap: 3 }}>
        <div />
        {labels.map(l => (
          <div key={l} style={{ textAlign: "center", fontSize: 10, color: "#38bdf8", fontWeight: 700, padding: "4px 0" }}>
            {l}
          </div>
        ))}
        {matrix.map((row, ri) => [
          <div key={`r${ri}`} style={{
            fontSize: 10, color: "#a78bfa", fontWeight: 700,
            display: "flex", alignItems: "center", justifyContent: "flex-end",
            paddingRight: 8,
          }}>{labels[ri]}</div>,
          ...row.map((val, ci) => {
            const intensity = val / max;
            const isCorrect = ri === ci;
            return (
              <div key={`${ri}-${ci}`} style={{
                background: isCorrect
                  ? `rgba(56,189,248,${0.15 + intensity * 0.5})`
                  : `rgba(248,113,113,${0.05 + intensity * 0.3})`,
                border: isCorrect ? "1px solid #38bdf840" : "1px solid #f8717120",
                borderRadius: 6, padding: "8px 4px",
                textAlign: "center", fontSize: 12, fontWeight: 700,
                color: isCorrect ? "#e0f2fe" : "#fca5a5",
              }}>
                {fmt(val)}
              </div>
            );
          })
        ])}
      </div>
    </div>
  );
}

// ─── METRIC BADGE ──────────────────────────────────────────────
function MetricBadge({ label, value, best, color = "#38bdf8" }) {
  return (
    <div style={{
      background: best ? `${color}18` : "#1e293b",
      border: `1px solid ${best ? color : "#334155"}`,
      borderRadius: 10, padding: "10px 14px",
      position: "relative", overflow: "hidden",
    }}>
      {best && (
        <span style={{
          position: "absolute", top: 4, right: 6, fontSize: 9,
          color, fontWeight: 800, letterSpacing: "0.1em",
        }}>BEST</span>
      )}
      <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 800, color: best ? color : "#94a3b8" }}>
        {pct(value)}
      </div>
    </div>
  );
}

// ─── DASHBOARD PAGE ────────────────────────────────────────────
function DashboardPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const data = await fetchAPI("/dashboard/summary");
      setSummary(data ?? MOCK.summary);
      setLoading(false);
    })();
  }, []);

  if (loading) return <Loader />;
  const { platform_stats, crawl_timeline } = summary;

  const pieData = platform_stats.map(p => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    value: p.total_records,
    fill: PLATFORM_COLORS[p.platform],
  }));

  const barData = platform_stats.map(p => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    "Tổng bài viết": p.total_records,
    "Tiếng Việt": p.vietnamese_records,
    fill: PLATFORM_COLORS[p.platform],
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 16 }}>
        <StatCard label="Tổng bài viết" value={fmt(summary.total_records)}
          sub="Từ 3 nền tảng" accent="#38bdf8" icon="📊" />
        <StatCard label="Đã gán nhãn" value={fmt(summary.total_labeled)}
          sub={`${pct(summary.total_labeled / summary.total_records)} tổng dữ liệu`} accent="#34d399" icon="🏷️" />
        <StatCard label="Nền tảng" value={summary.total_platforms}
          sub="TikTok · Threads · Facebook" accent="#a78bfa" icon="🌐" />
        <StatCard label="Mô hình AI" value={summary.total_models}
          sub="2 Traditional · 1 Deep Learning" accent="#f472b6" icon="🤖" />
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Pie Chart */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="Phân phối theo nền tảng" badge="Pie Chart" />
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={65} outerRadius={100}
                dataKey="value" paddingAngle={4} label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}
                labelLine={{ stroke: "#334155" }}>
                {pieData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} stroke={entry.fill} strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", justifyContent: "center", gap: 20, marginTop: 8 }}>
            {platform_stats.map(p => (
              <div key={p.platform} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: PLATFORM_COLORS[p.platform] }} />
                <span style={{ fontSize: 12, color: "#94a3b8" }}>
                  {p.platform.charAt(0).toUpperCase() + p.platform.slice(1)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Bar Chart */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="So sánh tổng & tiếng Việt" badge="Bar Chart" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} barGap={6}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              <Bar dataKey="Tổng bài viết" fill="#38bdf8" radius={[4,4,0,0]} />
              <Bar dataKey="Tiếng Việt" fill="#6366f1" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Timeline Chart */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
        <SectionHeader title="Timeline crawl dữ liệu theo tháng" badge="Line Chart" />
        <ResponsiveContainer width="100%" height={240}>
          <LineChart data={crawl_timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 12 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
            {["tiktok", "threads", "facebook"].map(p => (
              <Line key={p} type="monotone" dataKey={p}
                name={p.charAt(0).toUpperCase() + p.slice(1)}
                stroke={PLATFORM_COLORS[p]} strokeWidth={2.5}
                dot={{ fill: PLATFORM_COLORS[p], r: 4 }} activeDot={{ r: 6 }} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Platform cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        {platform_stats.map(p => (
          <div key={p.platform} style={{
            background: "#0f172a",
            border: `1px solid ${PLATFORM_COLORS[p.platform]}40`,
            borderRadius: 16, padding: 22,
            boxShadow: `0 0 20px ${PLATFORM_COLORS[p.platform]}15`,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12,
                background: `${PLATFORM_COLORS[p.platform]}20`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 20, color: PLATFORM_COLORS[p.platform],
                border: `1px solid ${PLATFORM_COLORS[p.platform]}40`,
              }}>
                {PLATFORM_ICONS[p.platform]}
              </div>
              <div>
                <div style={{ fontWeight: 700, color: "#f1f5f9", fontSize: 15, textTransform: "capitalize" }}>
                  {p.platform}
                </div>
                <div style={{ fontSize: 11, color: "#64748b" }}>Social Platform</div>
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b", fontSize: 13 }}>Tổng bài viết</span>
                <span style={{ color: PLATFORM_COLORS[p.platform], fontWeight: 700 }}>
                  {fmt(p.total_records)}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b", fontSize: 13 }}>Tiếng Việt</span>
                <span style={{ color: "#94a3b8", fontWeight: 600 }}>
                  {fmt(p.vietnamese_records)}
                </span>
              </div>
              <div style={{ marginTop: 4 }}>
                <div style={{ background: "#1e293b", borderRadius: 99, height: 6, overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: 99,
                    width: `${(p.vietnamese_records / p.total_records * 100).toFixed(0)}%`,
                    background: `linear-gradient(90deg,${PLATFORM_COLORS[p.platform]},${PLATFORM_COLORS[p.platform]}80)`,
                  }} />
                </div>
                <div style={{ fontSize: 10, color: "#475569", marginTop: 4, textAlign: "right" }}>
                  {(p.vietnamese_records / p.total_records * 100).toFixed(1)}% tiếng Việt
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── DATASET PAGE ──────────────────────────────────────────────
function DatasetPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await fetchAPI("/datasets/overview");
      setData(res ?? MOCK.dataset);
      setLoading(false);
    })();
  }, []);

  if (loading) return <Loader />;
  const splits = data?.data ?? MOCK.dataset.data;
  const totalLabeled = data?.total_labeled ?? MOCK.dataset.total_labeled;

  const trainData = splits.find(s => s.split_set === "train");
  const testData  = splits.find(s => s.split_set === "test");

  // Data for charts
  const splitBarData = [
    { name: "Train", value: trainData?.total_records ?? 0, fill: "#38bdf8" },
    { name: "Test",  value: testData?.total_records ?? 0,  fill: "#a78bfa" },
  ];

  const platformTrainData = trainData ? Object.entries(trainData.platforms).map(([k,v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1), train: v,
    test: testData?.platforms[k] ?? 0,
  })) : [];

  const labelData = trainData ? Object.entries(trainData.labels).map(([k,v]) => ({
    name: k.replace("_", " ").replace(/\b\w/g,l=>l.toUpperCase()),
    train: v, test: testData?.labels[k] ?? 0,
    fill: LABEL_COLORS[k],
  })) : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {/* KPI */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
        <StatCard label="Tổng đã gán nhãn" value={fmt(totalLabeled)}
          sub="Train + Test" accent="#38bdf8" icon="🏷️" />
        <StatCard label="Tập Train" value={fmt(trainData?.total_records)}
          sub={`${pct(trainData?.ratio ?? 0.8)} tổng`} accent="#34d399" icon="📚" />
        <StatCard label="Tập Test" value={fmt(testData?.total_records)}
          sub={`${pct(testData?.ratio ?? 0.2)} tổng`} accent="#a78bfa" icon="🧪" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Train/Test Split Donut */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="Tỉ lệ Train / Test" />
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={splitBarData} innerRadius={70} outerRadius={100}
                dataKey="value" paddingAngle={5}
                label={({ name, percent }) => `${name} ${(percent*100).toFixed(0)}%`}>
                {splitBarData.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Pie>
              <Tooltip content={<ChartTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Label Distribution */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="Phân phối nhãn Train vs Test" />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={labelData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} />
              <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
              <Tooltip content={<ChartTooltip />} />
              <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              <Bar dataKey="train" name="Train" fill="#38bdf8" radius={[4,4,0,0]} />
              <Bar dataKey="test"  name="Test"  fill="#a78bfa" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Platform breakdown */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
        <SectionHeader title="Phân phối theo nền tảng (Train vs Test)" />
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={platformTrainData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 12 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 11 }} />
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
            <Bar dataKey="train" name="Train" fill="#34d399" radius={[4,4,0,0]} />
            <Bar dataKey="test"  name="Test"  fill="#f472b6" radius={[4,4,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// ─── MODEL EVALUATION PAGE ─────────────────────────────────────
function ModelPage() {
  const [models, setModels] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      const res = await fetchAPI("/models/comparison");
      const data = res ?? MOCK.models;
      setModels(data);
      setSelected(data[2]); // PhoBERT default
      setLoading(false);
    })();
  }, []);

  if (loading) return <Loader />;
  if (!models?.length) return <div style={{ color: "#64748b" }}>Không có dữ liệu</div>;

  const bestAcc   = Math.max(...models.map(m => m.accuracy));
  const bestMacro = Math.max(...models.map(m => m.macro_f1));
  const bestHate  = Math.max(...models.map(m => m.target_hate_f1));

  // Radar data
  const radarData = ["accuracy","macro_f1","macro_precision","macro_recall","target_hate_f1","target_normal_f1"].map(key => {
    const entry = { metric: key.replace(/_/g," ").replace(/\b\w/g,l=>l.toUpperCase()) };
    models.forEach((m, i) => { entry[m.model_display_name] = +(m[key]*100).toFixed(1); });
    return entry;
  });

  // Bar comparison data
  const barCompare = models.map((m, i) => ({
    name: m.model_display_name,
    "Accuracy": +(m.accuracy*100).toFixed(1),
    "Macro F1": +(m.macro_f1*100).toFixed(1),
    "Hate F1": +(m.target_hate_f1*100).toFixed(1),
    fill: MODEL_COLORS[i],
  }));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {/* Comparison Table */}
      <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
        <SectionHeader title="Bảng so sánh mô hình" badge={`${models.length} Models`} />
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "separate", borderSpacing: "0 6px" }}>
            <thead>
              <tr>
                {["Mô hình","Loại","Accuracy","Macro F1","Weighted F1","Precision","Recall","Hate F1","Offensive F1","Normal F1"].map(h => (
                  <th key={h} style={{
                    padding: "8px 14px", fontSize: 11, color: "#64748b",
                    textAlign: "left", letterSpacing: "0.05em", textTransform: "uppercase",
                    borderBottom: "1px solid #1e293b",
                  }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((m, i) => {
                const isSelected = selected?.model_id === m.model_id;
                return (
                  <tr key={m.model_id} onClick={() => setSelected(m)}
                    style={{
                      cursor: "pointer",
                      background: isSelected ? `${MODEL_COLORS[i]}15` : "#0a0f1a",
                      outline: isSelected ? `1px solid ${MODEL_COLORS[i]}60` : "none",
                      borderRadius: 10, transition: "all 0.15s",
                    }}>
                    <td style={{ padding: "12px 14px", borderRadius: "10px 0 0 10px" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <div style={{ width: 10, height: 10, borderRadius: "50%", background: MODEL_COLORS[i] }} />
                        <span style={{ color: "#f1f5f9", fontWeight: 600, fontSize: 13 }}>
                          {m.model_display_name}
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: "12px 14px" }}>
                      <span style={{
                        background: m.model_type === "deep_learning" ? "#a78bfa20" : "#38bdf820",
                        color: m.model_type === "deep_learning" ? "#a78bfa" : "#38bdf8",
                        border: `1px solid ${m.model_type === "deep_learning" ? "#a78bfa40" : "#38bdf840"}`,
                        borderRadius: 20, padding: "2px 10px", fontSize: 11, fontWeight: 600,
                      }}>
                        {m.model_type === "deep_learning" ? "Deep Learning" : "Traditional"}
                      </span>
                    </td>
                    {[
                      [m.accuracy, m.accuracy === bestAcc],
                      [m.macro_f1, m.macro_f1 === bestMacro],
                      [m.weighted_f1, false],
                      [m.macro_precision, false],
                      [m.macro_recall, false],
                      [m.target_hate_f1, m.target_hate_f1 === bestHate],
                      [m.target_offensive_f1, false],
                      [m.target_normal_f1, false],
                    ].map(([val, isBest], idx) => (
                      <td key={idx} style={{ padding: "12px 14px" }}>
                        <span style={{
                          color: isBest ? "#fbbf24" : "#94a3b8",
                          fontWeight: isBest ? 800 : 500, fontSize: 13,
                        }}>
                          {pct(val)} {isBest ? "★" : ""}
                        </span>
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p style={{ fontSize: 11, color: "#475569", marginTop: 12, margin: "12px 0 0" }}>
          ★ Giá trị tốt nhất · Nhấn vào hàng để xem Confusion Matrix
        </p>
      </div>

      {/* Charts row */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        {/* Grouped Bar */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="So sánh chỉ số chính" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barCompare}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 10 }} />
              <YAxis domain={[60, 100]} tick={{ fill: "#64748b", fontSize: 11 }}
                tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v) => [`${v}%`]} contentStyle={{
                background: "#0f172a", border: "1px solid #334155", borderRadius: 8
              }} />
              <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
              <Bar dataKey="Accuracy" fill="#38bdf8" radius={[4,4,0,0]} />
              <Bar dataKey="Macro F1" fill="#a78bfa" radius={[4,4,0,0]} />
              <Bar dataKey="Hate F1"  fill="#f472b6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Radar Chart */}
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader title="Radar so sánh đa chiều" />
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#1e293b" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "#64748b", fontSize: 10 }} />
              <PolarRadiusAxis angle={30} domain={[60,100]} tick={{ fill: "#475569", fontSize: 9 }} />
              {models.map((m, i) => (
                <Radar key={m.model_id} name={m.model_display_name}
                  dataKey={m.model_display_name}
                  stroke={MODEL_COLORS[i]} fill={MODEL_COLORS[i]} fillOpacity={0.15}
                  strokeWidth={2} />
              ))}
              <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
              <Tooltip formatter={(v) => [`${v}%`]} contentStyle={{
                background: "#0f172a", border: "1px solid #334155", borderRadius: 8
              }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Selected model detail */}
      {selected && (
        <div style={{ background: "#0f172a", border: "1px solid #1e293b", borderRadius: 16, padding: 24 }}>
          <SectionHeader
            title={`Chi tiết: ${selected.model_display_name}`}
            badge={selected.version}
          />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
            {/* Metric badges */}
            <div>
              <p style={{ fontSize: 12, color: "#64748b", marginBottom: 12 }}>Chỉ số tổng thể</p>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <MetricBadge label="Accuracy" value={selected.accuracy}
                  best={selected.accuracy === bestAcc} />
                <MetricBadge label="Macro F1" value={selected.macro_f1}
                  best={selected.macro_f1 === bestMacro} color="#a78bfa" />
                <MetricBadge label="Macro Precision" value={selected.macro_precision} />
                <MetricBadge label="Macro Recall" value={selected.macro_recall} />
              </div>
              <p style={{ fontSize: 12, color: "#64748b", margin: "16px 0 12px" }}>Per-class F1</p>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10 }}>
                <MetricBadge label="Normal F1"   value={selected.target_normal_f1} color="#34d399" />
                <MetricBadge label="Hate F1"     value={selected.target_hate_f1}
                  best={selected.target_hate_f1 === bestHate} color="#f87171" />
                <MetricBadge label="Offensive F1" value={selected.target_offensive_f1} color="#fb923c" />
              </div>
              <div style={{ marginTop: 16, background: "#1e293b", borderRadius: 10, padding: 14 }}>
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 8 }}>Dataset Split</div>
                <div style={{ display: "flex", gap: 20 }}>
                  <div>
                    <div style={{ fontSize: 10, color: "#475569" }}>Train</div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#38bdf8" }}>
                      {pct(selected.train_ratio)}
                    </div>
                    <div style={{ fontSize: 11, color: "#64748b" }}>
                      {fmt(Math.round(selected.total_samples * selected.train_ratio))} mẫu
                    </div>
                  </div>
                  <div style={{ width: 1, background: "#334155" }} />
                  <div>
                    <div style={{ fontSize: 10, color: "#475569" }}>Test</div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#a78bfa" }}>
                      {pct(selected.test_ratio)}
                    </div>
                    <div style={{ fontSize: 11, color: "#64748b" }}>
                      {fmt(Math.round(selected.total_samples * selected.test_ratio))} mẫu
                    </div>
                  </div>
                  <div style={{ width: 1, background: "#334155" }} />
                  <div>
                    <div style={{ fontSize: 10, color: "#475569" }}>Tổng</div>
                    <div style={{ fontSize: 18, fontWeight: 800, color: "#f1f5f9" }}>
                      {fmt(selected.total_samples)}
                    </div>
                    <div style={{ fontSize: 11, color: "#64748b" }}>mẫu</div>
                  </div>
                </div>
              </div>
            </div>

            {/* Confusion Matrix */}
            <div>
              <ConfusionMatrix
                matrix={selected.confusion_matrix}
                modelName={selected.model_display_name}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── LOADER ────────────────────────────────────────────────────
function Loader() {
  return (
    <div style={{ display:"flex", justifyContent:"center", alignItems:"center", minHeight:300 }}>
      <div style={{
        width: 40, height: 40, borderRadius: "50%",
        border: "3px solid #1e293b",
        borderTop: "3px solid #38bdf8",
        animation: "spin 0.8s linear infinite",
      }} />
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}

// ─── APP SHELL ─────────────────────────────────────────────────
const PAGES = [
  { id: "dashboard", label: "Dashboard",      icon: "◉" },
  { id: "dataset",   label: "Quản lý Dataset", icon: "⊟" },
  { id: "models",    label: "Đánh giá Mô hình", icon: "⊕" },
];

export default function App() {
  const [page, setPage] = useState("dashboard");

  return (
    <div style={{
      minHeight: "100vh",
      background: "#060b14",
      color: "#f1f5f9",
      fontFamily: "'DM Sans', 'Segoe UI', system-ui, sans-serif",
      display: "flex",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 6px; background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
        tr:hover td { background: #0d1a2d !important; }
      `}</style>

      {/* Sidebar */}
      <aside style={{
        width: 240, minHeight: "100vh", flexShrink: 0,
        background: "#0a0f1a",
        borderRight: "1px solid #1e293b",
        display: "flex", flexDirection: "column",
        position: "sticky", top: 0, height: "100vh",
      }}>
        {/* Logo */}
        <div style={{ padding: "28px 24px 20px", borderBottom: "1px solid #1e293b" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: "linear-gradient(135deg,#38bdf8,#6366f1)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 18, fontWeight: 900,
            }}>H</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#f1f5f9", lineHeight: 1.2 }}>
                HateSpeech
              </div>
              <div style={{ fontSize: 10, color: "#475569" }}>Detection System</div>
            </div>
          </div>
          <div style={{
            marginTop: 14, background: "#0f172a", borderRadius: 8,
            padding: "6px 10px", display: "flex", alignItems: "center", gap: 6,
          }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#34d399" }} />
            <span style={{ fontSize: 11, color: "#34d399" }}>Hadoop Ecosystem</span>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ padding: "16px 12px", flex: 1 }}>
          <p style={{ fontSize: 10, color: "#334155", letterSpacing: "0.12em",
            textTransform: "uppercase", padding: "0 12px", marginBottom: 8 }}>Navigation</p>
          {PAGES.map(p => {
            const active = page === p.id;
            return (
              <button key={p.id} onClick={() => setPage(p.id)} style={{
                width: "100%", textAlign: "left", background: active
                  ? "linear-gradient(90deg,#38bdf815,#6366f108)"
                  : "transparent",
                border: active ? "1px solid #38bdf830" : "1px solid transparent",
                borderRadius: 10, padding: "10px 14px",
                display: "flex", alignItems: "center", gap: 10,
                cursor: "pointer", marginBottom: 4, transition: "all 0.15s",
                color: active ? "#38bdf8" : "#64748b",
              }}>
                <span style={{ fontSize: 16 }}>{p.icon}</span>
                <span style={{ fontSize: 13, fontWeight: active ? 700 : 500 }}>{p.label}</span>
                {active && <div style={{
                  marginLeft: "auto", width: 4, height: 4,
                  borderRadius: "50%", background: "#38bdf8",
                }} />}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: "16px 20px", borderTop: "1px solid #1e293b" }}>
          <div style={{ fontSize: 10, color: "#334155", lineHeight: 1.8 }}>
            <div>🗄 HDFS · Hive</div>
            <div>⚡ FastAPI · Python</div>
            <div>⚛ React · Recharts</div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main style={{ flex: 1, padding: "32px 36px", overflowY: "auto" }}>
        {/* Page header */}
        <div style={{ marginBottom: 28 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: "#f8fafc" }}>
            {PAGES.find(p => p.id === page)?.label}
          </h1>
          <p style={{ margin: "6px 0 0", color: "#475569", fontSize: 13 }}>
            {page === "dashboard" && "Tổng quan dữ liệu crawl từ TikTok, Threads, Facebook"}
            {page === "dataset" && "Quản lý và thống kê tập dữ liệu Train / Test"}
            {page === "models" && "So sánh hiệu năng TF-IDF + SVM · LR · PhoBERT"}
          </p>
        </div>

        {page === "dashboard" && <DashboardPage />}
        {page === "dataset"   && <DatasetPage />}
        {page === "models"    && <ModelPage />}
      </main>
    </div>
  );
}
