"use client";
/**
 * src/app/page.js — Dashboard Page
 */
import { useState, useEffect } from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

import  AppShell  from "@/components/layout/AppShell";
import { StatCard, SectionHeader, Card, ChartTooltip, Loader, ProgressBar } from "@/components/ui";
import {
  getDashboardSummary,
  fmt, pct, PLATFORM_COLORS, LABEL_COLORS,
} from "@/lib/api";

// ─── Platform Card ──────────────────────────────────────────────
function PlatformCard({ p, delay }) {
  const color = PLATFORM_COLORS[p.platform];
  const viRatio = p.total_records > 0 ? (p.vietnamese_records / p.total_records) : 0;

  const iconMap = { tiktok: "TK", threads: "@", facebook: "fb" };

  return (
    <div
      className="rounded-2xl border p-5 animate-slide-up"
      style={{
        borderColor: `${color}30`,
        background: "linear-gradient(135deg,#0f1a2e,#0a1120)",
        boxShadow: `0 0 24px ${color}12`,
        animationDelay: `${delay}ms`,
        animationFillMode: "both",
      }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div
          className="w-11 h-11 rounded-xl flex items-center justify-center font-extrabold text-sm"
          style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
        >
          {iconMap[p.platform]}
        </div>
        <div>
          <p className="text-sm font-bold text-ink capitalize">{p.platform}</p>
          <p className="text-[10px] text-ink-muted">Social Platform</p>
        </div>
      </div>

      <div className="space-y-2.5">
        <div className="flex justify-between text-xs">
          <span className="text-ink-muted">Tổng bài viết</span>
          <span className="font-bold" style={{ color }}>{fmt(p.total_records)}</span>
        </div>
        <div className="flex justify-between text-xs">
          <span className="text-ink-muted">Tiếng Việt</span>
          <span className="text-ink-muted font-semibold">{fmt(p.vietnamese_records)}</span>
        </div>
        <ProgressBar
          value={p.vietnamese_records}
          max={p.total_records}
          color={color}
          sublabel={pct(viRatio)}
        />
        <div className="flex justify-between text-[10px] text-ink-faint">
          <span>Avg. độ dài</span>
          <span>{Math.round(p.avg_char_count ?? 0)} ký tự</span>
        </div>
      </div>
    </div>
  );
}

// ─── Dashboard Page ─────────────────────────────────────────────
export default function DashboardPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardSummary().then((d) => {
      setData(d);
      setLoading(false);
    });
  }, []);

  if (loading) return <AppShell><Loader /></AppShell>;

  const { platform_stats, crawl_timeline } = data;

  const pieData = platform_stats.map((p) => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    value: p.total_records,
    fill: PLATFORM_COLORS[p.platform],
  }));

  const barData = platform_stats.map((p) => ({
    name: p.platform.charAt(0).toUpperCase() + p.platform.slice(1),
    "Tổng": p.total_records,
    "Tiếng Việt": p.vietnamese_records,
  }));

  const labelDistData = [
    { name: "Normal",      value: 5630, fill: LABEL_COLORS.normal },
    { name: "Hate Speech", value: 2640, fill: LABEL_COLORS.hate_speech },
    { name: "Offensive",   value: 1730, fill: LABEL_COLORS.offensive },
  ];

  return (
    <AppShell>
      {/* Header */}
      <div className="mb-7">
        <h1 className="text-2xl font-extrabold text-ink">Dashboard</h1>
        <p className="text-sm text-ink-muted mt-1">
          Tổng quan dữ liệu crawl từ TikTok, Threads
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Tổng bài viết"  value={fmt(data.total_records)}   sub="Từ 2 nền tảng"              color="blue"   icon="📊" delay={0}   />
        <StatCard label="Đã gán nhãn"    value={fmt(data.total_labeled)}    sub={`${pct(data.total_labeled/data.total_records)} tổng`} color="teal"   icon="🏷️" delay={80}  />
        <StatCard label="Nền tảng"       value={data.total_platforms}       sub="TikTok · Threads" color="violet" icon="🌐" delay={160} />
        <StatCard label="Mô hình AI"     value={data.total_models}          sub="2 Traditional · 1 DL"       color="pink"   icon="🤖" delay={240} />
      </div>

      {/* Row 1: Pie + Bar */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card delay={100}>
          <SectionHeader title="Phân phối theo nền tảng" badge="Pie Chart" />
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={62} outerRadius={92}
                dataKey="value" paddingAngle={4}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={{ stroke: "#334155", strokeWidth: 1 }}
              >
                {pieData.map((e, i) => (
                  <Cell key={i} fill={e.fill} stroke={e.fill} strokeWidth={2} />
                ))}
              </Pie>
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-5 mt-1">
            {platform_stats.map((p) => (
              <div key={p.platform} className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full" style={{ background: PLATFORM_COLORS[p.platform] }} />
                <span className="text-[11px] text-ink-muted capitalize">{p.platform}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card delay={180}>
          <SectionHeader title="Tổng & Tiếng Việt theo nền tảng" badge="Bar Chart" />
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} barGap={4} barSize={22}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#64748b", paddingTop: 8 }} />
              <Bar dataKey="Tổng"        fill="#38bdf8" radius={[5,5,0,0]} />
              <Bar dataKey="Tiếng Việt" fill="#6366f1" radius={[5,5,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Timeline */}
      <Card delay={260} className="mb-5">
        <SectionHeader title="Timeline crawl dữ liệu theo tháng" badge="Line Chart" />
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={crawl_timeline}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip formatter={(v) => `${v.toLocaleString("vi-VN")} bài`} />} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#64748b", paddingTop: 8 }} />
            {["tiktok", "threads"].map((p) => (
              <Line key={p} type="monotone" dataKey={p}
                name={p.charAt(0).toUpperCase() + p.slice(1)}
                stroke={PLATFORM_COLORS[p]} strokeWidth={2.5}
                dot={{ fill: PLATFORM_COLORS[p], r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* Row 3: Platform cards + Label dist */}
      <div className="grid grid-cols-3 gap-4 mb-5">
        {platform_stats.map((p, i) => (
          <PlatformCard key={p.platform} p={p} delay={80 + i * 70} />
        ))}
      </div>

      {/* Label distribution */}
      <Card delay={400}>
        <SectionHeader title="Phân phối nhãn toàn bộ dữ liệu gán nhãn" badge="Donut" />
        <div className="flex items-center gap-8">
          <ResponsiveContainer width={200} height={180}>
            <PieChart>
              <Pie data={labelDistData} innerRadius={52} outerRadius={78}
                dataKey="value" paddingAngle={5}>
                {labelDistData.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Pie>
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex-1 space-y-4">
            {labelDistData.map((d) => (
              <ProgressBar
                key={d.name}
                value={d.value}
                max={10000}
                color={d.fill}
                label={d.name}
                sublabel={`${d.value.toLocaleString("vi-VN")} mẫu`}
              />
            ))}
          </div>
        </div>
      </Card>
    </AppShell>
  );
}
