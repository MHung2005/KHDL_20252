"use client";
/**
 * src/components/layout/Sidebar.js
 */
import { usePathname } from "next/navigation";
import Link from "next/link";
import clsx from "clsx";
import { StatusDot } from "@/components/ui";

const NAV = [
  {
    href: "/",
    label: "Dashboard",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
    desc: "Tổng quan",
  },
  {
    href: "/dataset",
    label: "Dataset",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
    desc: "Train / Test",
  },
  {
    href: "/models",
    label: "Đánh giá Model",
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    desc: "SVM · LR · PhoBERT",
  },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside className="w-56 min-h-screen flex-shrink-0 bg-surface border-r border-surface-border flex flex-col sticky top-0 h-screen">
      {/* Logo */}
      <div className="p-5 border-b border-surface-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-accent-violet flex items-center justify-center text-white font-extrabold text-base shadow-lg">
            H
          </div>
          <div>
            <p className="text-sm font-extrabold text-ink leading-tight">HateSpeech</p>
            <p className="text-[10px] text-ink-muted">Detection System</p>
          </div>
        </div>
        <div className="bg-[#060b14] rounded-lg px-3 py-1.5 flex items-center gap-2">
          <StatusDot color="teal" />
          <span className="text-[10px] text-accent-teal font-semibold">Hadoop · PySpark</span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-1">
        <p className="text-[9px] uppercase tracking-widest text-ink-faint px-3 mb-2 mt-1">
          Navigation
        </p>
        {NAV.map((item) => {
          const active = path === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-150 group",
                active
                  ? "bg-brand-400/10 text-brand-400 border border-brand-400/20"
                  : "text-ink-muted hover:text-ink hover:bg-surface-hover border border-transparent"
              )}
            >
              <span className={clsx("flex-shrink-0", active ? "text-brand-400" : "text-ink-faint group-hover:text-ink-muted")}>
                {item.icon}
              </span>
              <div className="min-w-0">
                <p className={clsx("text-xs font-semibold leading-tight", active ? "text-brand-400" : "")}>
                  {item.label}
                </p>
                <p className="text-[9px] text-ink-faint truncate">{item.desc}</p>
              </div>
              {active && (
                <div className="ml-auto w-1 h-1 rounded-full bg-brand-400 flex-shrink-0" />
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-surface-border">
        <div className="space-y-1">
          {[
            { icon: "🗄", text: "HDFS · Apache Hive" },
            { icon: "⚡", text: "FastAPI · Python" },
            { icon: "⚛", text: "Next.js · Recharts" },
          ].map(({ icon, text }) => (
            <p key={text} className="text-[10px] text-ink-faint flex items-center gap-1.5">
              <span>{icon}</span>{text}
            </p>
          ))}
        </div>
        <div className="mt-3 pt-3 border-t border-surface-border">
          <p className="text-[9px] text-ink-faint">v1.0.0 — Mock Data Mode</p>
        </div>
      </div>
    </aside>
  );
}
