'use client';

import React from 'react';
import { motion } from 'motion/react';
import { ChartBar, PhoneCall } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { FinanceAvatarVideo } from './finance-avatar-video';
import { SpeakerStatusBadge, StartAgainLabel } from './speaker-status-badge';

export type CallSummary = {
  connected: boolean;
  outcome: 'success' | 'failed';
  reason: string;
  queries: string[];
};

interface CallEndedViewProps {
  onStartAgain: () => void;
  summary?: CallSummary;
}

export function CallEndedView({ onStartAgain, summary }: CallEndedViewProps) {
  const failed = summary?.outcome === 'failed';
  const queries = summary?.queries ?? [];

  return (
    <div className="relative z-10 flex max-h-[calc(100vh-5rem)] w-full flex-col items-center overflow-y-auto px-6 py-6 text-center md:py-10">
      <SpeakerStatusBadge state="ended" className="mb-10" />

      <FinanceAvatarVideo alwaysPlay size="xl" />

      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8 text-2xl font-semibold tracking-tight text-white md:text-3xl"
      >
        {failed ? 'Call cancelled' : 'Call ended'}
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400"
      >
        {summary?.reason || 'Thanks for talking with Jan Sahay. Start again anytime.'}
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.14 }}
        className="mt-6 w-full max-w-md rounded-2xl border border-white/10 bg-slate-950/55 p-4 text-left backdrop-blur-md"
      >
        <div className="mb-3 flex items-center justify-between gap-3">
          <p className="text-xs font-medium tracking-wide text-slate-400 uppercase">Call notes</p>
          <span
            className={
              failed
                ? 'rounded-full bg-rose-500/15 px-2.5 py-0.5 text-xs font-medium text-rose-300'
                : 'rounded-full bg-emerald-500/15 px-2.5 py-0.5 text-xs font-medium text-emerald-300'
            }
          >
            {failed ? 'Failed' : 'Successful'}
          </span>
        </div>
        <p className="text-sm text-slate-300">
          {summary?.connected
            ? 'The caller connected to Jan Sahay.'
            : 'The call was cancelled before connecting.'}
        </p>
        <p className="mt-3 text-xs font-medium tracking-wide text-slate-400 uppercase">Queries</p>
        {queries.length > 0 ? (
          <ul className="mt-2 space-y-1.5">
            {queries.map((query, index) => (
              <li
                key={`${index}-${query.slice(0, 24)}`}
                className="rounded-lg bg-white/5 px-3 py-2 text-sm text-slate-200"
              >
                {query}
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-2 text-sm text-slate-500">No queries in this call.</p>
        )}
        <a
          href="/dashboard"
          className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-emerald-300 transition hover:text-emerald-200"
        >
          <ChartBar className="size-4" weight="bold" />
          Open dashboard
        </a>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="mt-10"
      >
        <Button
          size="lg"
          onClick={onStartAgain}
          className="group flex h-12 min-w-[200px] items-center justify-center gap-2 rounded-full bg-white px-8 text-sm font-semibold text-slate-950 shadow-[0_12px_40px_-12px_rgba(16,185,129,0.5)] transition-all duration-300 hover:bg-emerald-50 active:scale-[0.98]"
        >
          <PhoneCall className="size-4 text-emerald-600" />
          <span>Call Back</span>
        </Button>
      </motion.div>
    </div>
  );
}
