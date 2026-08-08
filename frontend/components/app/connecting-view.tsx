'use client';

import React from 'react';
import { motion } from 'motion/react';
import { FinanceAvatarVideo } from './finance-avatar-video';
import { SpeakerStatusBadge } from './speaker-status-badge';

interface ConnectingViewProps {
  onCancel?: () => void;
}

export function ConnectingView({ onCancel }: ConnectingViewProps) {
  return (
    <div className="relative z-10 flex min-h-[80vh] flex-col items-center justify-center px-6 text-center">
      <SpeakerStatusBadge state="connecting" className="mb-10" />

      <div className="relative flex items-center justify-center">
        <div className="absolute size-48 animate-spin rounded-full border border-purple-400/20 [animation-duration:12s]" />
        <div className="absolute size-40 animate-spin rounded-full border border-dashed border-emerald-400/25 [animation-direction:reverse] [animation-duration:18s]" />
        <FinanceAvatarVideo alwaysPlay size="xl" />
      </div>

      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8 text-2xl font-semibold tracking-tight text-white md:text-3xl"
      >
        Connecting
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400"
      >
        Setting up a secure voice link with Jan Sahay…
      </motion.p>

      {onCancel && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.25 }}
          onClick={onCancel}
          className="mt-10 text-xs font-medium tracking-wide text-slate-500 transition hover:text-slate-300"
        >
          Cancel
        </motion.button>
      )}
    </div>
  );
}
