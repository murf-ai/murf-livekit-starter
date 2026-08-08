'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Mic,
  MicOff,
  Volume2,
  Sparkles,
  Radio,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Cpu,
} from 'lucide-react';
import { cn } from '@/lib/shadcn/utils';

export type AgentDisplayState =
  | 'READY'
  | 'CONNECTING'
  | 'LISTENING'
  | 'SPEAKING'
  | 'CALL_ENDED'
  | 'MIC_ERROR';

export interface AgentStateHeaderProps {
  state: AgentDisplayState;
  isUserSpeaking?: boolean;
  isAgentSpeaking?: boolean;
  isMicMuted?: boolean;
  className?: string;
}

export function AgentStateHeader({
  state,
  isUserSpeaking = false,
  isAgentSpeaking = false,
  isMicMuted = false,
  className,
}: AgentStateHeaderProps) {
  // Determine speaker badge text & style
  let speakerText = 'Agent ready';
  let speakerIcon = <Sparkles className="size-3.5 text-emerald-400 animate-pulse" />;

  if (state === 'CONNECTING') {
    speakerText = 'Connecting to agent...';
    speakerIcon = <RefreshCw className="size-3.5 text-amber-400 animate-spin" />;
  } else if (state === 'SPEAKING' || isAgentSpeaking) {
    speakerText = 'Agent is speaking...';
    speakerIcon = <Volume2 className="size-3.5 text-indigo-400 animate-bounce" />;
  } else if (state === 'LISTENING') {
    if (isUserSpeaking) {
      speakerText = 'Listening to you...';
      speakerIcon = <Mic className="size-3.5 text-emerald-400 animate-pulse" />;
    } else {
      speakerText = "I'm listening...";
      speakerIcon = <Radio className="size-3.5 text-emerald-400 animate-pulse" />;
    }
  } else if (state === 'CALL_ENDED') {
    speakerText = 'Conversation ended';
    speakerIcon = <CheckCircle2 className="size-3.5 text-slate-400" />;
  } else if (state === 'MIC_ERROR') {
    speakerText = 'Microphone access blocked';
    speakerIcon = <AlertTriangle className="size-3.5 text-red-400 animate-pulse" />;
  }

  // State pill styling
  const stateBadgeStyles: Record<AgentDisplayState, { bg: string; border: string; text: string; dot: string; label: string }> = {
    READY: {
      bg: 'bg-emerald-500/10 dark:bg-emerald-950/40',
      border: 'border-emerald-500/30',
      text: 'text-emerald-700 dark:text-emerald-300',
      dot: 'bg-emerald-500 shadow-emerald-500/50 shadow-md',
      label: 'READY',
    },
    CONNECTING: {
      bg: 'bg-amber-500/10 dark:bg-amber-950/40',
      border: 'border-amber-500/30',
      text: 'text-amber-700 dark:text-amber-300',
      dot: 'bg-amber-500 animate-ping shadow-amber-500/50 shadow-md',
      label: 'CONNECTING',
    },
    LISTENING: {
      bg: 'bg-emerald-500/15 dark:bg-emerald-950/60',
      border: 'border-emerald-500/40',
      text: 'text-emerald-600 dark:text-emerald-300',
      dot: 'bg-emerald-400 animate-pulse shadow-emerald-400/80 shadow-lg',
      label: 'LISTENING',
    },
    SPEAKING: {
      bg: 'bg-indigo-500/15 dark:bg-indigo-950/60',
      border: 'border-indigo-500/40',
      text: 'text-indigo-600 dark:text-indigo-300',
      dot: 'bg-indigo-400 animate-pulse shadow-indigo-400/80 shadow-lg',
      label: 'SPEAKING',
    },
    CALL_ENDED: {
      bg: 'bg-slate-500/10 dark:bg-slate-900/50',
      border: 'border-slate-500/30',
      text: 'text-slate-600 dark:text-slate-400',
      dot: 'bg-slate-400',
      label: 'CALL ENDED',
    },
    MIC_ERROR: {
      bg: 'bg-red-500/15 dark:bg-red-950/60',
      border: 'border-red-500/40',
      text: 'text-red-600 dark:text-red-400',
      dot: 'bg-red-500 animate-bounce',
      label: 'MIC ERROR',
    },
  };

  const badge = stateBadgeStyles[state];

  return (
    <div
      aria-label={`Voice agent status: ${badge.label}`}
      className={cn(
        'w-full max-w-xl mx-auto px-4 py-2.5 rounded-2xl backdrop-blur-xl transition-all duration-300',
        'border shadow-lg flex items-center justify-between gap-3',
        badge.bg,
        badge.border,
        className
      )}
    >
      {/* Left: Agent Brand / Icon */}
      <div className="flex items-center gap-2.5">
        <div className="relative flex items-center justify-center size-8 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
          <Cpu className="size-4" />
          {(state === 'LISTENING' || state === 'SPEAKING') && (
            <span className="absolute -top-0.5 -right-0.5 flex size-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full size-2.5 bg-emerald-500"></span>
            </span>
          )}
        </div>
        <div>
          <h2 className="text-xs font-bold tracking-wider uppercase text-foreground/90 leading-none">
            FinSafe Voice AI
          </h2>
          <div className="flex items-center gap-1.5 pt-1">
            {speakerIcon}
            <span className="text-xs font-medium text-muted-foreground leading-none">
              {speakerText}
            </span>
          </div>
        </div>
      </div>

      {/* Right: State Pill & Mic Badge */}
      <div className="flex items-center gap-2">
        {/* Mic Active Indicator */}
        {(state === 'LISTENING' || state === 'SPEAKING') && (
          <div
            title={isMicMuted ? 'Microphone Muted' : 'Microphone Active'}
            className={cn(
              'flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-semibold tracking-wide border transition-all',
              isMicMuted
                ? 'bg-red-500/10 text-red-500 border-red-500/20'
                : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20'
            )}
          >
            {isMicMuted ? <MicOff className="size-3" /> : <Mic className="size-3 animate-pulse" />}
            <span className="hidden sm:inline">{isMicMuted ? 'MUTED' : 'MIC ON'}</span>
          </div>
        )}

        {/* State Badge */}
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase border shadow-xs',
            badge.bg,
            badge.border,
            badge.text
          )}
        >
          <span className={cn('size-2 rounded-full', badge.dot)} />
          <span>{badge.label}</span>
        </div>
      </div>
    </div>
  );
}
