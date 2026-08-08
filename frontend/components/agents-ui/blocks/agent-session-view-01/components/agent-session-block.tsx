'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from './tile-view';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      translateY: '0%',
    },
    hidden: {
      opacity: 0,
      translateY: '100%',
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.3,
    delay: 0.5,
    ease: 'easeOut',
  },
};

const CHAT_MOTION_PROPS: MotionProps = {
  variants: {
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeOut',
        duration: 0.3,
      },
    },
    visible: {
      opacity: 1,
      transition: {
        delay: 0.2,
        ease: 'easeOut',
        duration: 0.3,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS: MotionProps = {
  variants: {
    visible: {
      opacity: 1,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0.8,
      },
    },
    hidden: {
      opacity: 0,
      transition: {
        ease: 'easeIn',
        duration: 0.5,
        delay: 0,
      },
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

interface FadeProps {
  top?: boolean;
  bottom?: boolean;
  className?: string;
}

export function Fade({ top = false, bottom = false, className }: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className
      )}
    />
  );
}

// ─── State badge config ─────────────────────────────────────────────────────
type AgentStateName = 'connecting' | 'initializing' | 'listening' | 'thinking' | 'speaking' | 'disconnected' | 'unknown';

interface StateConfig {
  label: string;
  labelHi: string;
  color: string;
  dotClass: string;
  pulse: boolean;
}

const STATE_CONFIG: Record<AgentStateName, StateConfig> = {
  connecting: {
    label: 'Connecting',
    labelHi: 'जुड़ रहे हैं',
    color: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-400/30',
    dotClass: 'bg-yellow-500',
    pulse: true,
  },
  initializing: {
    label: 'Starting',
    labelHi: 'शुरू हो रहा है',
    color: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-400/30',
    dotClass: 'bg-yellow-500',
    pulse: true,
  },
  listening: {
    label: 'Listening',
    labelHi: 'सुन रहा हूँ',
    color: 'bg-[var(--krishi-accent-muted)] text-[var(--krishi-accent)] border-[var(--krishi-accent)]/30',
    dotClass: 'bg-[var(--krishi-accent)]',
    pulse: true,
  },
  thinking: {
    label: 'Thinking',
    labelHi: 'सोच रहा हूँ',
    color: 'bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-400/30',
    dotClass: 'bg-purple-500',
    pulse: true,
  },
  speaking: {
    label: 'Speaking',
    labelHi: 'बोल रहा हूँ',
    color: 'bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-400/30',
    dotClass: 'bg-blue-500',
    pulse: true,
  },
  disconnected: {
    label: 'Call Ended',
    labelHi: 'बात खत्म',
    color: 'bg-muted text-muted-foreground border-border',
    dotClass: 'bg-muted-foreground',
    pulse: false,
  },
  unknown: {
    label: 'Ready',
    labelHi: 'तैयार',
    color: 'bg-muted text-muted-foreground border-border',
    dotClass: 'bg-muted-foreground',
    pulse: false,
  },
};

interface AgentStateBadgeProps {
  state: AgentStateName;
}

function AgentStateBadge({ state }: AgentStateBadgeProps) {
  const config = STATE_CONFIG[state] ?? STATE_CONFIG.unknown;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={state}
        initial={{ opacity: 0, y: -6, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 6, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-semibold tracking-wide',
          config.color
        )}
        role="status"
        aria-live="polite"
        aria-label={`Agent state: ${config.label}`}
      >
        <span
          className={cn(
            'inline-block h-1.5 w-1.5 rounded-full',
            config.dotClass,
            config.pulse && 'animate-pulse'
          )}
        />
        {config.labelHi} · {config.label}
      </motion.div>
    </AnimatePresence>
  );
}

// ─── Call Ended overlay ─────────────────────────────────────────────────────
interface CallEndedOverlayProps {
  onRestart: () => void;
}

function CallEndedOverlay({ onRestart }: CallEndedOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="absolute inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background/90 backdrop-blur-sm text-center px-6"
    >
      {/* Wheat icon */}
      <svg width="48" height="48" viewBox="0 0 72 72" fill="none" xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true" className="text-[var(--krishi-accent)] opacity-80">
        <line x1="36" y1="36" x2="36" y2="68" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        <ellipse cx="30" cy="42" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 30 42)" />
        <ellipse cx="27" cy="51" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 27 51)" />
        <ellipse cx="26" cy="60" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 26 60)" />
        <ellipse cx="42" cy="42" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 42 42)" />
        <ellipse cx="45" cy="51" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 45 51)" />
        <ellipse cx="46" cy="60" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 46 60)" />
      </svg>

      <div>
        <p className="text-foreground text-lg font-bold">Baat Khatam — Call Ended</p>
        <p className="text-muted-foreground text-sm mt-1">
          Asha hai aapki madad ho gayi hogi 🙏
        </p>
      </div>

      <button
        onClick={onRestart}
        className="mt-2 rounded-full border border-[var(--krishi-accent)] bg-[var(--krishi-accent)]/10 px-6 py-2 text-sm font-semibold text-[var(--krishi-accent)] transition hover:bg-[var(--krishi-accent)]/20 active:scale-95"
      >
        Dobara Baat Karein — Start Again
      </button>
    </motion.div>
  );
}

// ─── Main view ───────────────────────────────────────────────────────────────
export interface AgentSessionView_01Props {
  /**
   * Message shown above the controls before the first chat message is sent.
   * @default 'Namaste! Apna sawal poochh sakte hain 🙏'
   */
  preConnectMessage?: string;
  supportsChatInput?: boolean;
  supportsVideoInput?: boolean;
  supportsScreenShare?: boolean;
  isPreConnectBufferEnabled?: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;
  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Namaste! Apna sawal poochh sakte hain 🙏',
  supportsChatInput = true,
  supportsVideoInput = true,
  supportsScreenShare = true,
  isPreConnectBufferEnabled = true,

  audioVisualizerType,
  audioVisualizerColor,
  audioVisualizerColorShift,
  audioVisualizerBarCount,
  audioVisualizerGridRowCount,
  audioVisualizerGridColumnCount,
  audioVisualizerRadialBarCount,
  audioVisualizerRadialRadius,
  audioVisualizerWaveLineWidth,
  ref,
  className,
  ...props
}: React.ComponentProps<'section'> & AgentSessionView_01Props) {
  const session = useSessionContext();
  const { messages } = useSessionMessages(session);
  const [chatOpen, setChatOpen] = useState(true); // always show transcript
  const [callEnded, setCallEnded] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();

  // Map to our badge state type
  const badgeState: AgentStateName =
    callEnded ? 'disconnected'
    : (['connecting', 'initializing', 'listening', 'thinking', 'speaking'].includes(agentState as string)
        ? (agentState as AgentStateName)
        : 'unknown');

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal = lastMessage?.from?.isLocal === true;

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  // Detect disconnect → show call ended overlay
  useEffect(() => {
    if (!session.isConnected && messages.length > 0) {
      setCallEnded(true);
    }
  }, [session.isConnected, messages.length]);

  const handleRestart = () => {
    setCallEnded(false);
    session.end();
  };

  return (
    <section
      ref={ref}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      {/* ── Call Ended overlay ── */}
      <AnimatePresence>
        {callEnded && (
          <CallEndedOverlay onRestart={handleRestart} />
        )}
      </AnimatePresence>

      <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />

      {/* ── Agent state badge ── */}
      <div className="absolute top-4 left-1/2 z-20 -translate-x-1/2">
        <AgentStateBadge state={badgeState} />
      </div>

      {/* ── Transcript ── */}
      <div className="absolute top-0 bottom-[135px] flex w-full flex-col md:bottom-[170px]">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
            >
              <AgentChatTranscript
                agentState={agentState}
                messages={messages}
                className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-40 md:[&>div>div]:px-6"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Tile layout (audio visualizer) ── */}
      <TileLayout
        chatOpen={chatOpen}
        audioVisualizerType={audioVisualizerType}
        audioVisualizerColor={audioVisualizerColor}
        audioVisualizerColorShift={audioVisualizerColorShift}
        audioVisualizerBarCount={audioVisualizerBarCount}
        audioVisualizerRadialBarCount={audioVisualizerRadialBarCount}
        audioVisualizerRadialRadius={audioVisualizerRadialRadius}
        audioVisualizerGridRowCount={audioVisualizerGridRowCount}
        audioVisualizerGridColumnCount={audioVisualizerGridColumnCount}
        audioVisualizerWaveLineWidth={audioVisualizerWaveLineWidth}
      />

      {/* ── Bottom controls ── */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
        {/* Pre-connect message */}
        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}
        <div className="bg-background relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={() => {
              setCallEnded(true);
              session.end();
            }}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
