'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Mic,
  MicOff,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  ShieldAlert,
  HelpCircle,
  ShieldCheck,
  ArrowRight,
  Volume2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

export type WelcomeViewState = 'READY' | 'CONNECTING' | 'CALL_ENDED' | 'MIC_ERROR';

export interface WelcomeViewProps {
  state?: WelcomeViewState;
  startButtonText?: string;
  onStartCall: () => void;
  onStartAgain?: () => void;
  onTryAgain?: () => void;
  errorMessage?: string | null;
  errorDescription?: string | null;
}

const PROMPT_EXAMPLES = [
  {
    icon: '🏛️',
    title: 'Government Schemes',
    prompt: 'Explain Pradhan Mantri Jan Dhan Yojana (PMJDY)',
  },
  {
    icon: '🛡️',
    title: 'Fraud Alert Check',
    prompt: 'Is sharing an OTP or installing AnyDesk safe?',
  },
  {
    icon: '💳',
    title: 'Banking Terms',
    prompt: 'What is a CIBIL score and how does it work?',
  },
  {
    icon: '📜',
    title: 'Pension & Savings',
    prompt: 'Tell me about Atal Pension Yojana and SSY',
  },
];

export const WelcomeView = React.forwardRef<HTMLDivElement, WelcomeViewProps>(
  (
    {
      state = 'READY',
      startButtonText = 'Start Conversation',
      onStartCall,
      onStartAgain,
      onTryAgain,
      errorMessage,
      errorDescription,
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className="relative z-10 flex flex-col items-center justify-center min-h-[85vh] w-full max-w-4xl mx-auto px-4 py-8 text-center"
      >
        <AnimatePresence mode="wait">
          {/* STATE A: READY */}
          {state === 'READY' && (
            <motion.div
              key="ready-state"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center max-w-2xl w-full"
            >
              {/* Hero AI Avatar Icon */}
              <div className="relative mb-6 group cursor-pointer" onClick={onStartCall}>
                <div className="absolute -inset-4 rounded-full bg-gradient-to-r from-emerald-500/20 to-teal-500/20 blur-xl opacity-75 group-hover:opacity-100 transition duration-500 animate-pulse" />
                <div className="relative flex items-center justify-center size-24 rounded-3xl bg-background border-2 border-emerald-500/30 shadow-2xl shadow-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <Mic className="size-10 text-emerald-500 animate-pulse" />
                  <div className="absolute -bottom-2 -right-2 bg-emerald-500 text-white rounded-full p-1.5 shadow-md">
                    <Sparkles className="size-4" />
                  </div>
                </div>
              </div>

              {/* Status Badges */}
              <div className="flex items-center gap-2 mb-4 flex-wrap justify-center">
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-600 dark:text-emerald-300 border border-emerald-500/20">
                  <span className="size-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>State: READY</span>
                </div>
                <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-500/10 text-teal-600 dark:text-teal-300 border border-teal-500/20">
                  <Sparkles className="size-3 text-teal-500" />
                  <span>Day 4: Persistent Memory</span>
                </div>
              </div>

              {/* Title & Tagline */}
              <h1 className="text-3xl sm:text-4xl md:text-5xl font-extrabold tracking-tight text-foreground mb-3">
                FinSafe AI Voice Assistant
              </h1>

              <p className="text-base sm:text-lg text-muted-foreground max-w-xl leading-relaxed mb-8">
                Your interactive AI guide for Indian government financial schemes, banking literacy, and real-time fraud prevention.
              </p>

              {/* Main Primary CTA Button */}
              <div className="w-full max-w-sm mb-10">
                <Button
                  size="lg"
                  onClick={onStartCall}
                  className="w-full h-14 rounded-2xl text-base font-bold tracking-wide uppercase shadow-lg shadow-emerald-500/20 bg-emerald-600 hover:bg-emerald-500 text-white transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3 cursor-pointer"
                >
                  <Mic className="size-5" />
                  <span>{startButtonText}</span>
                  <ArrowRight className="size-5 opacity-80" />
                </Button>
                <p className="text-xs text-muted-foreground pt-3.5 font-medium">
                  Press button to allow mic access & start your live voice conversation
                </p>
              </div>

              {/* Sample Prompt Chips Grid */}
              <div className="w-full max-w-2xl">
                <div className="flex items-center justify-center gap-2 mb-3 text-xs font-bold tracking-wider uppercase text-muted-foreground">
                  <HelpCircle className="size-3.5" />
                  <span>What you can ask FinSafe AI</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-left">
                  {PROMPT_EXAMPLES.map((item, idx) => (
                    <div
                      key={idx}
                      onClick={onStartCall}
                      className="group p-3.5 rounded-xl bg-card border border-border/60 hover:border-emerald-500/40 hover:bg-emerald-500/5 transition-all duration-200 cursor-pointer shadow-xs"
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-base">{item.icon}</span>
                        <span className="text-xs font-bold text-foreground group-hover:text-emerald-600 dark:group-hover:text-emerald-400">
                          {item.title}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground line-clamp-1 italic">
                        "{item.prompt}"
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* STATE B: CONNECTING */}
          {state === 'CONNECTING' && (
            <motion.div
              key="connecting-state"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center max-w-md w-full p-8 rounded-3xl bg-card border border-border/80 shadow-2xl"
            >
              {/* Radar pulse visualizer */}
              <div className="relative flex items-center justify-center size-28 mb-6">
                <div className="absolute inset-0 rounded-full bg-amber-500/20 animate-ping opacity-75" />
                <div className="absolute -inset-4 rounded-full bg-gradient-to-r from-amber-500/10 to-emerald-500/10 blur-md animate-pulse" />
                <div className="relative flex items-center justify-center size-20 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-500">
                  <RefreshCw className="size-9 animate-spin" />
                </div>
              </div>

              {/* Status Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-3 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-300 border border-amber-500/20">
                <span className="size-2 rounded-full bg-amber-500 animate-ping" />
                <span>State: CONNECTING</span>
              </div>

              <h2 className="text-2xl font-bold text-foreground mb-2">
                Connecting to your voice agent...
              </h2>

              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                Establishing secure WebRTC audio stream & initializing Murf Falcon voice pipeline.
              </p>

              <div className="w-full bg-muted rounded-full h-1.5 overflow-hidden mb-4">
                <div className="bg-gradient-to-r from-amber-500 to-emerald-500 h-full w-2/3 animate-pulse rounded-full" />
              </div>

              <Button disabled variant="outline" className="w-full rounded-xl text-xs font-semibold">
                Connecting... Please wait
              </Button>
            </motion.div>
          )}

          {/* STATE E: CALL ENDED */}
          {state === 'CALL_ENDED' && (
            <motion.div
              key="call-ended-state"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center max-w-md w-full p-8 rounded-3xl bg-card border border-border/80 shadow-2xl"
            >
              <div className="relative flex items-center justify-center size-20 mb-5 rounded-2xl bg-slate-500/10 border border-slate-500/30 text-slate-500">
                <CheckCircle2 className="size-10 text-slate-400" />
              </div>

              {/* Status Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-3 rounded-full text-xs font-bold uppercase tracking-wider bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">
                <span className="size-2 rounded-full bg-slate-400" />
                <span>State: CALL ENDED</span>
              </div>

              <h2 className="text-2xl font-bold text-foreground mb-2">
                Conversation ended
              </h2>

              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                Your voice session with FinSafe AI has completed. Click below whenever you want to start a new voice session.
              </p>

              <Button
                size="lg"
                onClick={onStartAgain || onStartCall}
                className="w-full h-12 rounded-xl text-sm font-bold tracking-wide uppercase bg-emerald-600 hover:bg-emerald-500 text-white shadow-md flex items-center justify-center gap-2 cursor-pointer"
              >
                <RefreshCw className="size-4" />
                <span>Start Again</span>
              </Button>
            </motion.div>
          )}

          {/* STATE F: MICROPHONE ERROR */}
          {state === 'MIC_ERROR' && (
            <motion.div
              key="mic-error-state"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="flex flex-col items-center max-w-md w-full p-8 rounded-3xl bg-card border border-red-500/30 shadow-2xl shadow-red-500/5 text-left"
            >
              <div className="flex items-center justify-center size-16 mb-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-500 self-center">
                <ShieldAlert className="size-8" />
              </div>

              {/* Status Badge */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 mb-3 rounded-full text-xs font-bold uppercase tracking-wider bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20 self-center">
                <span className="size-2 rounded-full bg-red-500 animate-pulse" />
                <span>MICROPHONE ACCESS BLOCKED</span>
              </div>

              <h2 className="text-xl font-bold text-foreground mb-2 text-center">
                {errorMessage || 'Microphone access is blocked'}
              </h2>

              <p className="text-xs text-muted-foreground mb-4 text-center">
                {errorDescription ||
                  'Please allow microphone access in your browser settings and try again.'}
              </p>

              <div className="w-full p-3.5 rounded-xl bg-muted/60 border border-border/80 mb-6 text-xs text-muted-foreground space-y-2">
                <p className="font-semibold text-foreground">How to fix this:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Click the camera/lock icon in your browser address bar.</li>
                  <li>Set <strong>Microphone</strong> permission to <strong>Allow</strong>.</li>
                  <li>Click <strong>Try Again</strong> below.</li>
                </ol>
              </div>

              <Button
                size="lg"
                onClick={onTryAgain || onStartCall}
                className="w-full h-12 rounded-xl text-sm font-bold tracking-wide uppercase bg-red-600 hover:bg-red-500 text-white shadow-md flex items-center justify-center gap-2 cursor-pointer"
              >
                <RefreshCw className="size-4" />
                <span>Try Again</span>
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    );
  }
);

WelcomeView.displayName = 'WelcomeView';
