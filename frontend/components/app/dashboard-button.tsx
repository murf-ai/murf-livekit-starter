'use client';

import { ChartBar } from '@phosphor-icons/react';

export function DashboardButton() {
  return (
    <a
      href="/dashboard"
      aria-label="Open call dashboard"
      className="group pointer-events-auto fixed top-4 right-4 z-50 inline-flex items-center gap-2 rounded-full border border-emerald-400/25 bg-slate-950/70 px-3.5 py-2 text-sm font-medium text-emerald-100 shadow-[0_8px_28px_-12px_rgba(16,185,129,0.65)] backdrop-blur-md transition hover:border-emerald-300/50 hover:bg-emerald-950/70 hover:text-white"
    >
      <span className="flex size-7 items-center justify-center rounded-full bg-emerald-400/15 text-emerald-300 transition group-hover:bg-emerald-400/25">
        <ChartBar className="size-4" weight="bold" />
      </span>
      <span className="pr-0.5">Dashboard</span>
    </a>
  );
}
