"use client";
/**
 * src/app/page.js — EDA Dashboard Page
 * Phân tích khám phá dữ liệu: label, source, topic, text length
 */
import { useState, useEffect } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, ZAxis,
} from "recharts";

import AppShell from "@/components/layout/AppShell";
import { StatCard, SectionHeader, Card, ChartTooltip, Loader, ProgressBar } from "@/components/ui";

// ─── API helpers ─────────────────────────────────────────────
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const apiFetch = (path) => fetch(`${BASE}${path}`).then((r) => r.json());

const fmt  = (n) => (n ?? 0).toLocaleString("vi-VN");
const pct  = (v) => `${((v ?? 0) * 100).toFixed(1)}%`;
const pctN = (v) => `${(v ?? 0).toFixed(1)}%`;

// ─── Color tokens ────────────────────────────────────────────
const PLATFORM_COLORS = { tiktok: "#38bdf8", threads: "#a78bfa", facebook: "#34d399" };
const LABEL_COLORS = {
  "bình thường":   "#34d399",
  "offensive":     "#fb923c",
  "hate speech":   "#f87171",
  "chưa gán nhãn": "#64748b",
};
const LABEL_PALETTE = ["#34d399", "#fb923c", "#f87171", "#64748b"];
const TOPIC_COLORS  = [
  "#38bdf8","#a78bfa","#34d399","#fb923c","#f87171",
  "#fbbf24","#60a5fa","#c084fc","#4ade80","#f472b6",
];

// ─── Boxplot component (approximated from stats) ─────────────
function BoxPlotBar({ data }) {
  // data: [{label_name, median, q1, q3, min, max, platform}]
  // Render as horizontal grouped bar showing IQR + whiskers using recharts trick
  const labels = [...new Set(data.map((d) => d.label_name))].filter(l => l !== "chưa gán nhãn");
  const platforms = [...new Set(data.map((d) => d.platform))];

  const barData = labels.map((lbl) => {
    const entry = { name: lbl };
    platforms.forEach((plat) => {
      const row = data.find((d) => d.label_name === lbl && d.platform === plat);
      if (row) {
        entry[`${plat}_median`] = row.median;
        entry[`${plat}_q1`]    = row.q1;
        entry[`${plat}_q3`]    = row.q3;
      }
    });
    return entry;
  });

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={barData} barSize={24} barGap={4}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false}
          label={{ value: "ký tự", angle: -90, position: "insideLeft", fill: "#64748b", fontSize: 9 }} />
        <Tooltip
          contentStyle={{ background: "#0f1a2e", border: "1px solid #1e2f4a", borderRadius: 10 }}
          labelStyle={{ color: "#94a3b8" }}
          formatter={(v, name) => [`${v} ký tự`, name]}
        />
        <Legend wrapperStyle={{ fontSize: 11, color: "#64748b" }} />
        {platforms.map((plat, i) => (
          <Bar key={plat} dataKey={`${plat}_median`} name={`${plat} (median)`}
            fill={PLATFORM_COLORS[plat] ?? TOPIC_COLORS[i]} radius={[4,4,0,0]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Heatmap component ───────────────────────────────────────
function Heatmap({ data }) {
  if (!data?.length) return null;
  const cols = ["binh_thuong", "offensive", "hate_speech"];
  const colLabels = { binh_thuong: "Bình thường", offensive: "Offensive", hate_speech: "Hate Speech" };

  const getColor = (val) => {
    const t = val / 100;
    const r = Math.round(15 + t * (248 - 15));
    const g = Math.round(26 + t * (113 - 26));
    const b = Math.round(46 + t * (46 - 46));
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead>
          <tr>
            <th className="text-left text-[10px] text-ink-faint pb-2 pr-4 font-semibold uppercase tracking-wider">Chủ đề</th>
            {cols.map((c) => (
              <th key={c} className="text-center text-[10px] pb-2 px-2 font-semibold uppercase tracking-wider"
                style={{ color: c === "hate_speech" ? "#f87171" : c === "offensive" ? "#fb923c" : "#34d399" }}>
                {colLabels[c]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={row.topic} className="border-t border-surface-border">
              <td className="py-1.5 pr-4 text-ink-muted capitalize font-medium">
                {row.topic.replace(/_/g, " ")}
              </td>
              {cols.map((c) => (
                <td key={c} className="py-1.5 px-2 text-center">
                  <span
                    className="inline-block px-2 py-0.5 rounded-lg text-[11px] font-bold"
                    style={{
                      background: getColor(row[c]),
                      color: row[c] > 50 ? "#e2e8f0" : "#94a3b8",
                    }}
                  >
                    {pctN(row[c])}
                  </span>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Main Page ───────────────────────────────────────────────
export default function DashboardPage() {
  const [summary,       setSummary]       = useState(null);
  const [labelDist,     setLabelDist]     = useState([]);
  const [sourceLabelDist, setSourceLabel] = useState([]);
  const [topicDist,     setTopicDist]     = useState([]);
  const [topicHeatmap,  setTopicHeatmap]  = useState([]);
  const [textLenStats,  setTextLenStats]  = useState([]);
  const [loading,       setLoading]       = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch("/dashboard/summary"),
      apiFetch("/dashboard/label-distribution"),
      apiFetch("/dashboard/source-label"),
      apiFetch("/dashboard/topic-distribution"),
      apiFetch("/dashboard/topic-label-heatmap"),
      apiFetch("/dashboard/text-length-stats"),
    ]).then(([sum, lbl, src, top, heat, txt]) => {
      setSummary(sum);
      setLabelDist(lbl?.data ?? []);
      setSourceLabel(src?.data ?? []);
      setTopicDist(top?.data ?? []);
      setTopicHeatmap(heat?.data ?? []);
      setTextLenStats(txt?.data ?? []);
      setLoading(false);
    });
  }, []);

  if (loading) return <AppShell><Loader /></AppShell>;

  // ── Chuẩn bị dữ liệu biểu đồ ──
  const totalRecords  = summary?.total_records  ?? 0;
  const totalLabeled  = summary?.total_labeled  ?? 0;
  const totalUnlabeled = summary?.total_unlabeled ?? 0;

  // Pie: phân phối nhãn (bỏ chưa gán nhãn để rõ hơn)
  const labelPieData = labelDist
    .filter((d) => d.label_name !== "chưa gán nhãn")
    .map((d) => ({ name: d.label_name, value: d.total, fill: LABEL_COLORS[d.label_name] ?? "#64748b" }));

  // Bar: phân phối nhãn theo nguồn — reshape thành [{source, binh_thuong, offensive, hate_speech}]
  const sourceLabelBar = (() => {
    const map = {};
    sourceLabelDist.forEach((d) => {
      if (d.label_name === "chưa gán nhãn") return;
      if (!map[d.platform]) map[d.platform] = { source: d.platform };
      map[d.platform][d.label_name] = d.count;
    });
    return Object.values(map);
  })();

  // Bar: phân phối theo chủ đề (top 10)
  const topicBarData = topicDist.slice(0, 10).map((d, i) => ({
    name: d.topic.replace(/_/g, " "),
    total: d.total,
    fill: TOPIC_COLORS[i % TOPIC_COLORS.length],
  }));

  return (
    <AppShell>
      {/* Header */}
      <div className="mb-7">
        <h1 className="text-2xl font-extrabold text-ink">EDA Dashboard</h1>
        <p className="text-sm text-ink-muted mt-1">
          Phân tích khám phá dữ liệu crawl từ TikTok · Threads
        </p>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Tổng bài viết"   value={fmt(totalRecords)}   sub="Từ 2 nền tảng"                                   color="blue"   icon="📊" delay={0}   />
        <StatCard label="Đã gán nhãn"     value={fmt(totalLabeled)}   sub={`${pct(totalLabeled/totalRecords)} tổng`}         color="teal"   icon="🏷️" delay={80}  />
        <StatCard label="Chưa gán nhãn"   value={fmt(totalUnlabeled)} sub={`${pct(totalUnlabeled/totalRecords)} tổng`}       color="amber"  icon="⏳" delay={160} />
        <StatCard label="Lớp nhãn"        value="3"                   sub="Bình thường · Offensive · Hate Speech"            color="violet" icon="🔖" delay={240} />
      </div>

      {/* Row 1: Label pie + Source grouped bar */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card delay={100}>
          <SectionHeader title="Phân phối nhãn tổng thể" badge="Pie Chart" />
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie data={labelPieData} innerRadius={48} outerRadius={72}
                  dataKey="value" paddingAngle={5}>
                  {labelPieData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Pie>
                <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-3">
              {labelPieData.map((d) => (
                <div key={d.name}>
                  <div className="flex justify-between text-xs mb-1">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full" style={{ background: d.fill }} />
                      <span className="text-ink-muted capitalize">{d.name}</span>
                    </div>
                    <span className="font-bold" style={{ color: d.fill }}>
                      {fmt(d.value)}
                    </span>
                  </div>
                  <ProgressBar value={d.value} max={totalLabeled} color={d.fill} sublabel={pct(d.value / totalLabeled)} />
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card delay={180}>
          <SectionHeader title="So sánh phân phối nhãn theo nguồn" badge="Grouped Bar" />
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={sourceLabelBar} barSize={22} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
              <XAxis dataKey="source" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#64748b" }} />
              <Bar dataKey="bình thường"  fill="#34d399" radius={[4,4,0,0]} />
              <Bar dataKey="offensive"    fill="#fb923c" radius={[4,4,0,0]} />
              <Bar dataKey="hate speech"  fill="#f87171" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Row 2: Topic bar */}
      <Card delay={240} className="mb-5">
        <SectionHeader title="Phân phối bài viết theo chủ đề (Top 10)" badge="Bar Chart" />
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={topicBarData} barSize={28}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 10 }}
              axisLine={false} tickLine={false} interval={0} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false}
              tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
            <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
            {topicBarData.map((entry, i) => null /* paint each bar custom */)}
            <Bar dataKey="total" radius={[5,5,0,0]}
              label={{ position: "top", fill: "#64748b", fontSize: 9, formatter: (v) => fmt(v) }}>
              {topicBarData.map((entry, i) => (
                <Cell key={i} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Row 3: Text length boxplot + Timeline */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card delay={300}>
          <SectionHeader title="Phân phối độ dài văn bản theo nhãn" badge="Median / Q1-Q3" />
          <BoxPlotBar data={textLenStats} />
          <p className="text-[10px] text-ink-faint mt-2">
            Cột thể hiện giá trị median. Hate Speech có xu hướng dài hơn bình thường.
          </p>
        </Card>

        <Card delay={360}>
          <SectionHeader title="Timeline crawl theo tháng" badge="Bar Chart" />
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={summary?.crawl_timeline ?? []} barSize={18} barGap={3}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
              <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#64748b", fontSize: 9 }} axisLine={false} tickLine={false}
                tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#64748b" }} />
              <Bar dataKey="tiktok"  name="TikTok"  fill="#38bdf8" radius={[4,4,0,0]} />
              <Bar dataKey="threads" name="Threads" fill="#a78bfa" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Row 4: Topic-Label Heatmap */}
      <Card delay={420}>
        <SectionHeader title="Tỷ lệ phân phối nhãn theo chủ đề (%)" badge="Heatmap" />
        <Heatmap data={topicHeatmap} />
        <p className="text-[10px] text-ink-faint mt-3">
          Màu đậm hơn = tỷ lệ cao hơn. Chủ đề "chính trị" có tỷ lệ hate speech cao nhất.
        </p>
      </Card>
    </AppShell>
  );
} 