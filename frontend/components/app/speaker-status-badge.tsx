'use client';

import React from 'react';
import { motion } from 'motion/react';
import {
  Microphone,
  SpeakerHigh,
  CircleNotch,
  PhoneDisconnect,
  Brain,
} from '@phosphor-icons/react';
import type { AgentUIState } from './particle-swarm-canvas';

interface SpeakerStatusBadgeProps {
  state: AgentUIState;
  className?: string;
}

const LABEL: Record<AgentUIState, string> = {
  ready: 'Ready',
  connecting: 'Connecting',
  thinking: 'Thinking',
  listening: 'Listening',
  speaking: 'Speaking',
  ended: 'Call ended',
};

export function SpeakerStatusBadge({ state, className = '' }: SpeakerStatusBadgeProps) {
  return (
    <motion.div
      key={state}
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      className={`inline-flex items-center gap-2.5 rounded-full border border-white/10 bg-white/5 px-3.5 py-1.5 text-xs font-medium tracking-wide text-slate-200 backdrop-blur-xl ${className}`}
    >
      {state === 'ready' && (
        <>
          <span className="relative flex size-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400/70" />
            <span className="relative inline-flex size-2 rounded-full bg-emerald-400" />
          </span>
          <span className="text-emerald-300">{LABEL.ready}</span>
        </>
      )}

      {state === 'connecting' && (
        <>
          <CircleNotch className="size-3.5 animate-spin text-violet-300" />
          <span className="text-violet-200">{LABEL.connecting}</span>
        </>
      )}

      {state === 'thinking' && (
        <>
          <Brain className="size-3.5 animate-pulse text-sky-300" />
          <span className="text-sky-200">{LABEL.thinking}</span>
        </>
      )}

      {state === 'listening' && (
        <>
          <Microphone className="size-3.5 text-emerald-400" />
          <span className="text-emerald-300">{LABEL.listening}</span>
        </>
      )}

      {state === 'speaking' && (
        <>
          <SpeakerHigh className="size-3.5 text-amber-300" />
          <span className="text-amber-200">{LABEL.speaking}</span>
        </>
      )}

      {state === 'ended' && (
        <>
          <PhoneDisconnect className="size-3.5 text-rose-300" />
          <span className="text-rose-200/90">{LABEL.ended}</span>
        </>
      )}
    </motion.div>
  );
}

export function StartAgainLabel() {
  return <span>Start again</span>;
}
