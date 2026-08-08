'use client';

import React from 'react';
import { motion } from 'motion/react';
import { PhoneCall } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { FinanceAvatarVideo } from './finance-avatar-video';
import { SpeakerStatusBadge, StartAgainLabel } from './speaker-status-badge';

interface CallEndedViewProps {
  onStartAgain: () => void;
}

export function CallEndedView({ onStartAgain }: CallEndedViewProps) {
  return (
    <div className="relative z-10 flex min-h-[80vh] flex-col items-center justify-center px-6 text-center">
      <SpeakerStatusBadge state="ended" className="mb-10" />

      <FinanceAvatarVideo alwaysPlay size="xl" />

      <motion.h2
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-8 text-2xl font-semibold tracking-tight text-white md:text-3xl"
      >
        Call ended
      </motion.h2>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="mt-2 max-w-sm text-sm leading-relaxed text-slate-400"
      >
        Thanks for talking with Jan Sahay. Start again anytime.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.16 }}
        className="mt-10"
      >
        <Button
          size="lg"
          onClick={onStartAgain}
          className="group h-12 min-w-[200px] rounded-full bg-white px-8 text-sm font-semibold text-slate-950 shadow-[0_12px_40px_-12px_rgba(16,185,129,0.5)] transition-all duration-300 hover:bg-emerald-50 active:scale-[0.98]"
        >
          <PhoneCall className="size-4 text-emerald-600" />
          <StartAgainLabel />
        </Button>
      </motion.div>
    </div>
  );
}
