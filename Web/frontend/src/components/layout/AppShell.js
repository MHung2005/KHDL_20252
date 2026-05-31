"use client";
/**
 * src/components/layout/AppShell.js
 */
import Sidebar from "./Sidebar";

export default function AppShell({ children }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 px-8 py-7 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
