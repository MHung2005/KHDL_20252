"use client";
/**
 * src/app/models/page.js — Model Evaluation Page
 */
import { useState, useEffect } from "react";
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

import AppShell from "@/components/layout/AppShell";
import { StatCard, SectionHeader, Card, ChartTooltip, Loader, Badge } from "@/components/ui";
import ConfusionMatrix from "@/components/charts/ConfusionMatrix";
import { getModelComparison, fmt, pct, MODEL_COLORS } from "@/lib/api";

// ─── Metric Badge ───────────────────────────────────────────────
function MetricBlock({ label, value, isBest, color = "#38bdf8" }) {
  return (
    <div
      className="rounded-xl p-3 border transition-all"
      style={{
        background: isBest ? `${color}10` : "#0a1120",
        borderColor: isBest ? `${color}40` : "#1e2f4a",
      }}
    >
      {isBest && (
        <div className="text-[9px] font-extrabold tracking-widest mb-1" style={{ color }}>
          ★ BEST
        </div>
      )}
      <div className="text-[10px] text-ink-muted mb-1">{label}</div>
      <div className="text-lg font-extrabold" style={{ color: isBest ? color : "#94a3b8" }}>
        {pct(value)}
      </div>
    </div>
  );
}

export default function ModelsPage() {
  const [models,   setModels]   = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    getModelComparison().then((data) => {
      setModels(data);
      // default: PhoBERT
      setSelected(data.find((m) => m.model_type === "deep_learning") ?? data[0]);
      setLoading(false);
    });
  }, []);

  if (loading) return <AppShell><Loader /></AppShell>;
  if (!models.length) return <AppShell><p className="text-ink-muted">Không có dữ liệu</p></AppShell>;

  const bestAcc  = Math.max(...models.map((m) => m.accuracy));
  const bestF1   = Math.max(...models.map((m) => m.macro_f1));
  const bestHate = Math.max(...models.map((m) => m.target_hate_f1));

  // Bar comparison data
  const barData = models.map((m) => ({
    name: m.model_display_name,
    "Accuracy": +(m.accuracy * 100).toFixed(1),
    "Macro F1": +(m.macro_f1 * 100).toFixed(1),
    "Hate F1":  +(m.target_hate_f1 * 100).toFixed(1),
  }));

  // Radar data
  const radarKeys = ["accuracy","macro_f1","macro_precision","macro_recall","target_hate_f1","target_normal_f1"];
  const radarLabels = { accuracy:"Accuracy", macro_f1:"Macro F1", macro_precision:"Precision",
    macro_recall:"Recall", target_hate_f1:"Hate F1", target_normal_f1:"Normal F1" };
  const radarData = radarKeys.map((k) => {
    const entry = { metric: radarLabels[k] };
    models.forEach((m) => { entry[m.model_display_name] = +(m[k] * 100).toFixed(1); });
    return entry;
  });

  return (
    <AppShell>
      <div className="mb-7">
        <h1 className="text-2xl font-extrabold text-ink">Đánh giá Mô hình</h1>
        <p className="text-sm text-ink-muted mt-1">
          So sánh hiệu năng TF-IDF + SVM · TF-IDF + LR · PhoBERT
        </p>
      </div>

      {/* KPI - best model */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Best Accuracy"  value={pct(bestAcc)}  sub="PhoBERT" color="blue"   icon="🎯" delay={0}   />
        <StatCard label="Best Macro F1"  value={pct(bestF1)}   sub="PhoBERT" color="violet" icon="📈" delay={80}  />
        <StatCard label="Best Hate F1"   value={pct(bestHate)} sub="PhoBERT" color="pink"   icon="🛡" delay={160} />
        <StatCard label="Số mô hình"     value={models.length} sub="3 được đánh giá" color="teal" icon="🤖" delay={240} />
      </div>

      {/* Comparison table */}
      <Card delay={120} className="mb-5">
        <SectionHeader title="Bảng so sánh tổng hợp" badge={`${models.length} Models`} />
        <div className="overflow-x-auto">
          <table className="w-full text-xs border-separate" style={{ borderSpacing: "0 5px" }}>
            <thead>
              <tr>
                {["Mô hình","Loại","Accuracy","Macro F1","W. F1","Precision","Recall","Hate F1","Offensv F1","Normal F1","Samples"].map((h) => (
                  <th key={h} className="pb-2 pt-0 text-left text-[9px] uppercase tracking-widest text-ink-faint font-semibold px-3 border-b border-surface-border">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map((m, i) => {
                const isSel = selected?.model_id === m.model_id;
                return (
                  <tr
                    key={m.model_id}
                    onClick={() => setSelected(m)}
                    className="cursor-pointer rounded-xl transition-all"
                    style={{
                      background: isSel ? `${MODEL_COLORS[i]}10` : "#0a0f1a",
                      outline: isSel ? `1px solid ${MODEL_COLORS[i]}40` : "none",
                      borderRadius: 12,
                    }}
                  >
                    <td className="px-3 py-2.5 rounded-l-xl">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: MODEL_COLORS[i] }} />
                        <span className="font-bold text-ink text-[11px]">{m.model_display_name}</span>
                      </div>
                    </td>
                    <td className="px-3 py-2.5">
                      <Badge variant={m.model_type}>
                        {m.model_type === "deep_learning" ? "Deep Learning" : "Traditional"}
                      </Badge>
                    </td>
                    {[
                      [m.accuracy,             m.accuracy === bestAcc],
                      [m.macro_f1,             m.macro_f1 === bestF1],
                      [m.weighted_f1,          false],
                      [m.macro_precision,      false],
                      [m.macro_recall,         false],
                      [m.target_hate_f1,       m.target_hate_f1 === bestHate],
                      [m.target_offensive_f1,  false],
                      [m.target_normal_f1,     false],
                    ].map(([val, best], idx) => (
                      <td key={idx} className="px-3 py-2.5">
                        <span className="font-bold" style={{ color: best ? "#fbbf24" : "#94a3b8" }}>
                          {pct(val)}{best ? " ★" : ""}
                        </span>
                      </td>
                    ))}
                    <td className="px-3 py-2.5 rounded-r-xl text-ink-muted">
                      {fmt(m.total_samples)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="text-[10px] text-ink-faint mt-2">★ Giá trị tốt nhất · Nhấn vào hàng để xem chi tiết bên dưới</p>
      </Card>

      {/* Chart row */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card delay={200}>
          <SectionHeader title="So sánh chỉ số chính" />
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={barData} barSize={18} barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 9 }} axisLine={false} tickLine={false} />
              <YAxis domain={[60, 100]} tick={{ fill: "#64748b", fontSize: 9 }} tickFormatter={(v) => `${v}%`} axisLine={false} tickLine={false} />
              <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: "#0f1a2e", border: "1px solid #1e2f4a", borderRadius: 10 }} labelStyle={{ color: "#94a3b8" }} itemStyle={{ fontSize: 11 }} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#64748b", paddingTop: 8 }} />
              <Bar dataKey="Accuracy" fill="#38bdf8" radius={[4,4,0,0]} />
              <Bar dataKey="Macro F1" fill="#a78bfa" radius={[4,4,0,0]} />
              <Bar dataKey="Hate F1"  fill="#f472b6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card delay={280}>
          <SectionHeader title="Radar đa chiều" />
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={radarData} outerRadius={88}>
              <PolarGrid stroke="#1e2f4a" />
              <PolarAngleAxis dataKey="metric" tick={{ fill: "#64748b", fontSize: 9 }} />
              <PolarRadiusAxis angle={30} domain={[60, 100]} tick={{ fill: "#334155", fontSize: 8 }} />
              {models.map((m, i) => (
                <Radar key={m.model_id} name={m.model_display_name}
                  dataKey={m.model_display_name}
                  stroke={MODEL_COLORS[i]} fill={MODEL_COLORS[i]} fillOpacity={0.12} strokeWidth={2}
                />
              ))}
              <Legend wrapperStyle={{ fontSize: 10, color: "#64748b" }} />
              <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: "#0f1a2e", border: "1px solid #1e2f4a", borderRadius: 10 }} itemStyle={{ fontSize: 11 }} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Selected model detail */}
      {selected && (
        <Card delay={350}>
          <SectionHeader
            title={`Chi tiết: ${selected.model_display_name}`}
            badge={selected.version}
          />
          <div className="grid grid-cols-2 gap-8">
            {/* Left: metrics */}
            <div>
              <p className="text-[10px] uppercase tracking-widest text-ink-faint mb-3">Chỉ số tổng thể</p>
              <div className="grid grid-cols-2 gap-2.5 mb-5">
                <MetricBlock label="Accuracy"       value={selected.accuracy}        isBest={selected.accuracy === bestAcc} />
                <MetricBlock label="Macro F1"       value={selected.macro_f1}        isBest={selected.macro_f1 === bestF1} color="#a78bfa" />
                <MetricBlock label="Macro Precision" value={selected.macro_precision} />
                <MetricBlock label="Macro Recall"   value={selected.macro_recall} />
              </div>

              <p className="text-[10px] uppercase tracking-widest text-ink-faint mb-3">Per-class F1</p>
              <div className="grid grid-cols-3 gap-2.5 mb-5">
                <MetricBlock label="Normal F1"    value={selected.target_normal_f1}    color="#34d399" />
                <MetricBlock label="Hate F1"      value={selected.target_hate_f1}      isBest={selected.target_hate_f1 === bestHate} color="#f87171" />
                <MetricBlock label="Offensive F1" value={selected.target_offensive_f1} color="#fb923c" />
              </div>

              {/* Train/Test split */}
              <div className="bg-surface rounded-xl p-4 border border-surface-border">
                <p className="text-[10px] uppercase tracking-widest text-ink-faint mb-3">Dataset Split</p>
                <div className="flex gap-6">
                  {[
                    { label: "Train", val: selected.train_ratio, color: "#38bdf8" },
                    { label: "Test",  val: selected.test_ratio,  color: "#a78bfa" },
                    { label: "Total", val: null,                  color: "#f1f5f9", count: selected.total_samples },
                  ].map((s, i) => [
                    i > 0 && <div key={`div-${i}`} className="w-px bg-surface-border" />,
                    <div key={s.label}>
                      <p className="text-[9px] text-ink-muted mb-0.5">{s.label}</p>
                      <p className="text-xl font-extrabold" style={{ color: s.color }}>
                        {s.count ? fmt(s.count) : pct(s.val)}
                      </p>
                      <p className="text-[10px] text-ink-faint mt-0.5">
                        {s.count ? "mẫu" : `${fmt(Math.round(selected.total_samples * s.val))} mẫu`}
                      </p>
                    </div>,
                  ])}
                </div>
              </div>
            </div>

            {/* Right: confusion matrix */}
            <div>
              <p className="text-[10px] uppercase tracking-widest text-ink-faint mb-3">Confusion Matrix</p>
              <ConfusionMatrix
                matrix={selected.confusion_matrix}
                modelName={selected.model_display_name}
              />
            </div>
          </div>
        </Card>
      )}
    </AppShell>
  );
}
