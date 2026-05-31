"use client";
/**
 * src/components/ui/index.js
 * Reusable UI primitives
 */

import clsx from "clsx";

// ─── STAT CARD ─────────────────────────────────────────────────
export function StatCard({ label, value, sub, color = "blue", icon, delay = 0 }) {
  const glowMap = {
    blue:   "card-glow-blue  border-brand-400/20",
    violet: "card-glow-violet border-accent-violet/20",
    teal:   "card-glow-teal  border-accent-teal/20",
    pink:   "card-glow-pink  border-accent-pink/20",
    amber:  "border-accent-amber/20",
  };
  const textMap = {
    blue:   "text-brand-400",
    violet: "text-accent-violet",
    teal:   "text-accent-teal",
    pink:   "text-accent-pink",
    amber:  "text-accent-amber",
  };
  return (
    <div
      className={clsx(
        "rounded-2xl border bg-gradient-to-br from-surface to-surface-card p-5",
        "animate-slide-up",
        glowMap[color]
      )}
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-[10px] uppercase tracking-widest text-ink-muted font-semibold">
          {label}
        </span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={clsx("text-4xl font-extrabold tabular-nums", textMap[color])}>
        {value}
      </div>
      {sub && (
        <div className="mt-1.5 text-[11px] text-ink-faint">{sub}</div>
      )}
    </div>
  );
}

// ─── SECTION HEADER ────────────────────────────────────────────
export function SectionHeader({ title, badge, action }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <div className="w-1 h-5 rounded-full bg-gradient-to-b from-brand-400 to-accent-violet flex-shrink-0" />
      <h2 className="text-base font-bold text-ink">{title}</h2>
      {badge && (
        <span className="text-[10px] font-semibold px-2.5 py-0.5 rounded-full bg-brand-400/10 text-brand-400 border border-brand-400/20">
          {badge}
        </span>
      )}
      {action && <div className="ml-auto">{action}</div>}
    </div>
  );
}

// ─── CARD ──────────────────────────────────────────────────────
export function Card({ children, className, delay = 0 }) {
  return (
    <div
      className={clsx(
        "bg-surface-card border border-surface-border rounded-2xl p-5",
        "animate-slide-up",
        className
      )}
      style={{ animationDelay: `${delay}ms`, animationFillMode: "both" }}
    >
      {children}
    </div>
  );
}

// ─── BADGE ─────────────────────────────────────────────────────
export function Badge({ children, variant = "default" }) {
  const variantMap = {
    default:      "bg-surface-border/50 text-ink-muted",
    blue:         "bg-brand-400/10 text-brand-400 border border-brand-400/20",
    violet:       "bg-accent-violet/10 text-accent-violet border border-accent-violet/20",
    teal:         "bg-accent-teal/10 text-accent-teal border border-accent-teal/20",
    pink:         "bg-accent-pink/10 text-accent-pink border border-accent-pink/20",
    amber:        "bg-accent-amber/10 text-accent-amber border border-accent-amber/20",
    "deep-learning": "bg-accent-violet/10 text-accent-violet border border-accent-violet/20",
    traditional:  "bg-brand-400/10 text-brand-400 border border-brand-400/20",
  };
  return (
    <span className={clsx("text-[10px] font-semibold px-2 py-0.5 rounded-full", variantMap[variant])}>
      {children}
    </span>
  );
}

// ─── PROGRESS BAR ──────────────────────────────────────────────
export function ProgressBar({ value, max, color = "#38bdf8", label, sublabel }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div>
      {(label || sublabel) && (
        <div className="flex justify-between items-center mb-1.5">
          {label   && <span className="text-xs text-ink-muted">{label}</span>}
          {sublabel && <span className="text-xs font-bold" style={{ color }}>{sublabel}</span>}
        </div>
      )}
      <div className="h-1.5 bg-surface rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}

// ─── CUSTOM RECHARTS TOOLTIP ───────────────────────────────────
export function ChartTooltip({ active, payload, label, formatter }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-surface border border-surface-border rounded-xl px-3.5 py-2.5 shadow-xl text-xs">
      {label && <p className="text-ink-muted mb-1.5 text-[11px]">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} className="font-semibold" style={{ color: p.color }}>
          {p.name}: {formatter ? formatter(p.value) : p.value?.toLocaleString("vi-VN")}
        </p>
      ))}
    </div>
  );
}

// ─── LOADER ────────────────────────────────────────────────────
export function Loader({ text = "Đang tải dữ liệu..." }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[280px] gap-4">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-surface-border" />
        <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand-400 animate-spin" />
      </div>
      <p className="text-xs text-ink-muted">{text}</p>
    </div>
  );
}

// ─── EMPTY STATE ───────────────────────────────────────────────
export function EmptyState({ icon = "📭", title = "Không có dữ liệu", sub }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] gap-3">
      <span className="text-4xl">{icon}</span>
      <p className="text-sm font-semibold text-ink-muted">{title}</p>
      {sub && <p className="text-xs text-ink-faint">{sub}</p>}
    </div>
  );
}

// ─── STATUS DOT ────────────────────────────────────────────────
export function StatusDot({ color = "teal", label }) {
  const colorMap = {
    teal:   "bg-accent-teal",
    red:    "bg-red-400",
    amber:  "bg-accent-amber",
    muted:  "bg-ink-faint",
  };
  return (
    <div className="flex items-center gap-1.5">
      <div className={clsx("w-1.5 h-1.5 rounded-full animate-pulse-slow", colorMap[color])} />
      {label && <span className="text-[10px] text-ink-muted">{label}</span>}
    </div>
  );
}
