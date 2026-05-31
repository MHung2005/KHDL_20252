"use client";
/**
 * src/app/dataset/page.js — Dataset Management Page
 */
import { useState, useEffect } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

import AppShell from "@/components/layout/AppShell";
import { StatCard, SectionHeader, Card, ChartTooltip, Loader, ProgressBar, Badge } from "@/components/ui";
import { getDatasetOverview, fmt, pct, PLATFORM_COLORS, LABEL_COLORS } from "@/lib/api";

const SPLIT_COLORS = { train: "#38bdf8", test: "#a78bfa" };
const LABEL_NAMES  = { normal: "Normal", hate_speech: "Hate Speech", offensive: "Offensive" };

export default function DatasetPage() {
  const [data, setData]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [active, setActive]   = useState("train");

  useEffect(() => {
    getDatasetOverview().then((d) => { setData(d); setLoading(false); });
  }, []);

  if (loading) return <AppShell><Loader /></AppShell>;

  const splits     = data?.data ?? [];
  const trainData  = splits.find((s) => s.split_set === "train");
  const testData   = splits.find((s) => s.split_set === "test");
  const totalLab   = data?.total_labeled ?? 10000;
  const current    = active === "train" ? trainData : testData;

  const splitPie = [
    { name: "Train", value: trainData?.total_records ?? 0, fill: SPLIT_COLORS.train },
    { name: "Test",  value: testData?.total_records  ?? 0, fill: SPLIT_COLORS.test  },
  ];

  const platformBar = ["tiktok", "threads", "facebook"].map((p) => ({
    name: p.charAt(0).toUpperCase() + p.slice(1),
    Train: trainData?.platforms?.[p] ?? 0,
    Test:  testData?.platforms?.[p]  ?? 0,
  }));

  const labelBar = Object.keys(LABEL_NAMES).map((k) => ({
    name:  LABEL_NAMES[k],
    Train: trainData?.labels?.[k] ?? 0,
    Test:  testData?.labels?.[k]  ?? 0,
    fill:  LABEL_COLORS[k],
  }));

  const currentLabels = Object.entries(current?.labels ?? {}).map(([k, v]) => ({
    key: k, name: LABEL_NAMES[k], value: v, fill: LABEL_COLORS[k],
  }));

  return (
    <AppShell>
      <div className="mb-7">
        <h1 className="text-2xl font-extrabold text-ink">Quản lý Dataset</h1>
        <p className="text-sm text-ink-muted mt-1">Phân chia Train / Test theo nền tảng và nhãn</p>
      </div>

      {/* KPI */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatCard label="Tổng gán nhãn" value={fmt(totalLab)}                       sub="Train + Test"    color="blue"   icon="🏷️" delay={0}   />
        <StatCard label="Tập Train"     value={fmt(trainData?.total_records)}        sub={pct(trainData?.ratio ?? 0.8)}   color="teal"   icon="📚" delay={80}  />
        <StatCard label="Tập Test"      value={fmt(testData?.total_records)}         sub={pct(testData?.ratio  ?? 0.2)}   color="violet" icon="🧪" delay={160} />
        <StatCard label="Lớp nhãn"      value="3"                                    sub="Normal · Hate · Offensive"       color="amber"  icon="🏷" delay={240} />
      </div>

      {/* Row 1: Split pie + Platform bar */}
      <div className="grid grid-cols-2 gap-5 mb-5">
        <Card delay={100}>
          <SectionHeader title="Tỉ lệ Train / Test" />
          <div className="flex items-center gap-6">
            <ResponsiveContainer width={160} height={160}>
              <PieChart>
                <Pie data={splitPie} innerRadius={48} outerRadius={72}
                  dataKey="value" paddingAngle={6}>
                  {splitPie.map((e, i) => <Cell key={i} fill={e.fill} />)}
                </Pie>
                <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-4">
              {splitPie.map((s) => (
                <div key={s.name}>
                  <div className="flex justify-between text-xs mb-1">
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 rounded-full" style={{ background: s.fill }} />
                      <span className="text-ink-muted">{s.name}</span>
                    </div>
                    <span className="font-bold" style={{ color: s.fill }}>
                      {pct(s.value / totalLab)}
                    </span>
                  </div>
                  <ProgressBar value={s.value} max={totalLab} color={s.fill} sublabel={fmt(s.value)} />
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card delay={180}>
          <SectionHeader title="Phân phối theo nền tảng" badge="Train vs Test" />
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={platformBar} barSize={20} barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
              <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
              <Legend wrapperStyle={{ fontSize: 11, color: "#64748b" }} />
              <Bar dataKey="Train" fill="#38bdf8" radius={[5,5,0,0]} />
              <Bar dataKey="Test"  fill="#a78bfa" radius={[5,5,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Label distribution bar */}
      <Card delay={260} className="mb-5">
        <SectionHeader title="Phân phối nhãn Train vs Test" badge="Grouped Bar" />
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={labelBar} barSize={28} barGap={6}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2f4a" vertical={false} />
            <XAxis dataKey="name" tick={{ fill: "#64748b", fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip content={<ChartTooltip formatter={(v) => v.toLocaleString("vi-VN")} />} />
            <Legend wrapperStyle={{ fontSize: 11, color: "#64748b" }} />
            <Bar dataKey="Train" fill="#38bdf8" radius={[5,5,0,0]} />
            <Bar dataKey="Test"  fill="#a78bfa" radius={[5,5,0,0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Detail table with tab */}
      <Card delay={340}>
        <div className="flex items-center justify-between mb-4">
          <SectionHeader title="Chi tiết tập dữ liệu" />
          <div className="flex gap-2 ml-auto">
            {["train", "test"].map((s) => (
              <button
                key={s}
                onClick={() => setActive(s)}
                className={`text-xs px-4 py-1.5 rounded-full font-semibold border transition-all ${
                  active === s
                    ? "bg-brand-400/10 text-brand-400 border-brand-400/30"
                    : "text-ink-muted border-surface-border hover:border-ink-faint"
                }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {current ? (
          <>
            <div className="grid grid-cols-3 gap-3 mb-5">
              {currentLabels.map((l) => (
                <div key={l.key}
                  className="rounded-xl p-3.5 border"
                  style={{ borderColor: `${l.fill}30`, background: `${l.fill}08` }}
                >
                  <p className="text-[10px] font-semibold uppercase tracking-wider mb-1" style={{ color: l.fill }}>
                    {l.name}
                  </p>
                  <p className="text-2xl font-extrabold text-ink">{fmt(l.value)}</p>
                  <p className="text-[10px] text-ink-muted mt-0.5">
                    {pct(l.value / (current.total_records || 1))} tập {active}
                  </p>
                  <ProgressBar value={l.value} max={current.total_records} color={l.fill} />
                </div>
              ))}
            </div>

            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-surface-border">
                  {["Nền tảng", "Số lượng", "Tỉ lệ"].map((h) => (
                    <th key={h} className="pb-2 text-left text-[10px] uppercase tracking-wider text-ink-muted font-semibold">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {Object.entries(current?.platforms ?? {}).map(([plat, cnt]) => (
                  <tr key={plat} className="hover:bg-surface-hover transition-colors">
                    <td className="py-2.5 flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ background: PLATFORM_COLORS[plat] }} />
                      <span className="capitalize text-ink font-medium">{plat}</span>
                    </td>
                    <td className="py-2.5 font-bold text-ink">{fmt(cnt)}</td>
                    <td className="py-2.5">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden max-w-[80px]">
                          <div className="h-full rounded-full" style={{ width: pct(cnt / current.total_records), background: PLATFORM_COLORS[plat] }} />
                        </div>
                        <span className="text-ink-muted">{pct(cnt / current.total_records)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ) : null}
      </Card>
    </AppShell>
  );
}
