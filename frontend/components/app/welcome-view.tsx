'use client';

import React from 'react';
import { motion } from 'motion/react';
import { PhoneCall } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';
import { FinanceAvatarVideo } from './finance-avatar-video';
import { SpeakerStatusBadge } from './speaker-status-badge';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  ref?: React.Ref<HTMLDivElement>;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
  ...props
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6 py-12 text-center"
      {...props}
    >
      <SpeakerStatusBadge state="ready" className="mb-10" />

      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      >
        <FinanceAvatarVideo alwaysPlay size="hero" />
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08, duration: 0.45 }}
        className="mt-8 text-4xl font-semibold tracking-tight text-white md:text-5xl"
      >
        Jan Sahay
        <span className="ml-2 font-normal text-emerald-400/90">(जन सहाय)</span>
      </motion.h1>

      <motion.p
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.14, duration: 0.45 }}
        className="mt-3 max-w-md text-[15px] leading-relaxed text-slate-400 md:text-base"
      >
        Your AI guide for government financial schemes and safe digital banking.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.22, duration: 0.45 }}
        className="mt-10"
      >
        <Button
          size="lg"
          onClick={onStartCall}
          className="group h-12 min-w-[220px] rounded-full bg-white px-8 text-sm font-semibold tracking-wide text-slate-950 shadow-[0_0_0_1px_rgba(255,255,255,0.08),0_12px_40px_-12px_rgba(16,185,129,0.55)] transition-all duration-300 hover:bg-emerald-50 hover:shadow-[0_0_0_1px_rgba(16,185,129,0.25),0_16px_48px_-12px_rgba(16,185,129,0.65)] active:scale-[0.98]"
        >
          <PhoneCall className="size-4 text-emerald-600 transition-transform group-hover:scale-110" />
          <span>{startButtonText || 'Start conversation'}</span>
        </Button>
      </motion.div>
    </div>
  );
};
