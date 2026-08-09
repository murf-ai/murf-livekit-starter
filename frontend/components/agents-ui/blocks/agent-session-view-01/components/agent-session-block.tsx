'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
} from '@livekit/components-react';

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

export function Fade({
  top = false,
  bottom = false,
  className,
}: FadeProps) {
  return (
    <div
      className={cn(
        'from-background pointer-events-none h-4 bg-linear-to-b to-transparent',
        top && 'bg-linear-to-b',
        bottom && 'bg-linear-to-t',
        className,
      )}
    />
  );
}

export interface AgentSessionView_01Props {
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
  preConnectMessage = 'MediSathi is ready. Ask me a health question.',
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
  const { state: agentState } = useAgent();

  const [chatOpen, setChatOpen] = useState(false);

  const scrollAreaRef = useRef<HTMLDivElement | null>(null);

  /*
   * Get the latest message text.
   *
   * LiveKit message objects can expose the text slightly differently
   * depending on the version, so this keeps the UI tolerant.
   */
  const getMessageText = (message: unknown): string => {
    if (!message || typeof message !== 'object') return '';

    const item = message as {
      message?: unknown;
      content?: unknown;
      text?: unknown;
    };

    if (typeof item.message === 'string') return item.message;
    if (typeof item.content === 'string') return item.content;
    if (typeof item.text === 'string') return item.text;

    if (Array.isArray(item.content)) {
      return item.content
        .filter((part) => typeof part === 'string')
        .join(' ');
    }

    return '';
  };

  const latestMessage = messages.at(-1);
  const latestCaption = getMessageText(latestMessage);

  const isLocalMessage = Boolean(
    latestMessage &&
      typeof latestMessage === 'object' &&
      'from' in latestMessage &&
      (latestMessage as { from?: { isLocal?: boolean } }).from?.isLocal,
  );

  const statusText =
    agentState === 'listening'
      ? '🎙️ MediSathi is listening'
      : agentState === 'speaking'
        ? '🔊 MediSathi is speaking'
        : agentState === 'thinking'
          ? '🤔 MediSathi is thinking'
          : '🟢 MediSathi is ready';

  const statusColor =
    agentState === 'listening'
      ? 'bg-emerald-400'
      : agentState === 'speaking'
        ? 'bg-cyan-400'
        : agentState === 'thinking'
          ? 'bg-amber-400'
          : 'bg-teal-400';

  const controls: AgentControlBarControls = {
    leave: true,
    microphone: true,
    chat: supportsChatInput,
    camera: supportsVideoInput,
    screenShare: supportsScreenShare,
  };

  useEffect(() => {
    const lastMessage = messages.at(-1);
    const lastMessageIsLocal =
      lastMessage &&
      typeof lastMessage === 'object' &&
      'from' in lastMessage &&
      Boolean(
        (lastMessage as { from?: { isLocal?: boolean } }).from?.isLocal,
      );

    if (scrollAreaRef.current && lastMessageIsLocal) {
      scrollAreaRef.current.scrollTop =
        scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <section
      ref={ref}
      className={cn(
        'relative z-10 h-full w-full overflow-hidden bg-[#031312] text-white',
        className,
      )}
      {...props}
    >
      {/* Background glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-32 top-20 h-96 w-96 rounded-full bg-teal-500/10 blur-3xl" />
        <div className="absolute right-0 top-1/3 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute bottom-0 left-1/3 h-80 w-80 rounded-full bg-emerald-500/5 blur-3xl" />

        {/* Healthcare ECG decoration */}
        <div className="absolute left-0 top-[38%] hidden w-[28%] opacity-20 lg:block">
          <svg
            viewBox="0 0 500 120"
            className="h-auto w-full"
            fill="none"
          >
            <path
              d="M0 65 H80 L105 65 L125 20 L145 100 L165 50 L190 65 H260 L280 65 L300 35 L315 85 L330 65 H500"
              stroke="#14B8A6"
              strokeWidth="2"
            />
          </svg>
        </div>

        <div className="absolute right-0 top-[48%] hidden w-[22%] opacity-10 lg:block">
          <svg
            viewBox="0 0 400 100"
            className="h-auto w-full"
            fill="none"
          >
            <path
              d="M0 50 H70 L90 50 L110 20 L125 80 L145 50 H220 L245 50 L265 30 L280 70 L295 50 H400"
              stroke="#22D3EE"
              strokeWidth="2"
            />
          </svg>
        </div>
      </div>

      {/* Header */}
      <header className="absolute left-0 right-0 top-0 z-40 flex items-center justify-between px-5 py-5 md:px-10 md:py-7">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-teal-400/30 bg-teal-400/10 text-2xl shadow-[0_0_30px_rgba(20,184,166,0.15)]">
            🩺
          </div>

          <div>
            <h1 className="text-xl font-bold tracking-tight md:text-2xl">
              Health <span className="text-teal-400">Access</span>
            </h1>
            <p className="text-xs text-white/50 md:text-sm">
              Your voice health companion
            </p>
          </div>
        </div>

        <div className="hidden text-right md:block">
          <div className="flex items-center justify-end gap-2 text-sm font-semibold text-teal-300">
            <span>🔒</span>
            Privacy First
          </div>
          <p className="mt-1 text-xs text-white/40">
            Limited health profile information only
          </p>
        </div>
      </header>

      {/* Agent status */}
      <div className="absolute left-1/2 top-5 z-40 -translate-x-1/2 md:top-7">
        <div className="flex items-center gap-2 rounded-full border border-teal-400/30 bg-[#071d1b]/90 px-5 py-2.5 shadow-[0_0_35px_rgba(20,184,166,0.12)] backdrop-blur-xl">
          <span
            className={cn(
              'h-2.5 w-2.5 rounded-full shadow-[0_0_12px_currentColor]',
              statusColor,
            )}
          />

          <span className="text-sm font-semibold whitespace-nowrap md:text-base">
            {statusText}
          </span>
        </div>
      </div>

      {/* Left suggested questions */}
      <aside className="absolute bottom-32 left-6 z-30 hidden w-64 lg:block xl:left-10">
        <div className="rounded-2xl border border-teal-400/20 bg-[#061b19]/80 p-5 shadow-2xl backdrop-blur-xl">
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xl">💡</span>
            <h2 className="font-semibold text-teal-300">
              Try asking
            </h2>
          </div>

          <div className="space-y-3 text-sm text-white/75">
            <div className="flex gap-2">
              <span className="text-teal-400">✓</span>
              <span>&quot;I have a headache since morning&quot;</span>
            </div>

            <div className="flex gap-2">
              <span className="text-teal-400">✓</span>
              <span>&quot;What are signs of dehydration?&quot;</span>
            </div>

            <div className="flex gap-2">
              <span className="text-teal-400">✓</span>
              <span>&quot;How can I improve my sleep?&quot;</span>
            </div>

            <div className="flex gap-2">
              <span className="text-teal-400">✓</span>
              <span>&quot;Give me healthy diet tips&quot;</span>
            </div>
          </div>

          <div className="mt-4 border-t border-white/10 pt-4 text-xs font-medium text-teal-300">
            Speak naturally. I&apos;ll take care of the rest.
          </div>
        </div>
      </aside>

      {/* Right profile */}
      <aside className="absolute right-6 top-28 z-30 hidden w-72 xl:right-10 xl:block">
        <div className="rounded-2xl border border-teal-400/25 bg-[#061b19]/85 p-5 shadow-2xl backdrop-blur-xl">
          <div className="mb-5 flex items-center justify-between border-b border-white/10 pb-4">
            <div className="flex items-center gap-2">
              <span className="text-xl">👤</span>
              <h2 className="text-sm font-bold tracking-wide">
                HEALTH ACCESS PROFILE
              </h2>
            </div>

            <span className="text-teal-400">⌁</span>
          </div>

          <div className="space-y-5">
            <div>
              <p className="text-sm font-semibold text-white">
                Age band
              </p>
              <p className="mt-1 text-sm text-white/45">
                Not provided
              </p>
            </div>

            <div className="border-t border-white/10 pt-4">
              <p className="text-sm font-semibold text-white">
                Ongoing conditions
              </p>
              <p className="mt-1 text-sm text-white/45">
                None recorded
              </p>
            </div>

            <div className="border-t border-white/10 pt-4">
              <p className="text-sm font-semibold text-white">
                Last triage outcome
              </p>
              <p className="mt-1 text-sm text-white/45">
                Not assessed yet
              </p>
            </div>
          </div>

          <p className="mt-5 border-t border-white/10 pt-4 text-xs leading-5 text-white/40">
            Limited profile information helps MediSathi provide
            more relevant support.
          </p>
        </div>

        {/* Privacy */}
        <div className="mt-4 rounded-2xl border border-emerald-400/20 bg-emerald-400/5 p-5 backdrop-blur-xl">
          <div className="flex items-center gap-2 text-sm font-semibold text-emerald-300">
            <span>🛡️</span>
            Privacy-first by design
          </div>

          <p className="mt-3 text-xs leading-5 text-white/55">
            Only limited health profile information is retained.
            Written-out medical notes are not stored.
          </p>
        </div>
      </aside>

      {/* Main visualizer area */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div
          className={cn(
            'relative flex w-full max-w-4xl flex-col items-center px-5',
            'pt-20 pb-44 md:pt-24 md:pb-40',
          )}
        >
          {/* Visualizer glow */}
          <div className="relative mb-8 flex h-52 w-52 items-center justify-center md:h-64 md:w-64">
            <div className="absolute inset-0 animate-pulse rounded-full border border-teal-400/10" />

            <div className="absolute inset-5 rounded-full border border-teal-400/20 shadow-[0_0_80px_rgba(20,184,166,0.15)]" />

            <div className="absolute inset-10 rounded-full border-2 border-teal-400/60 shadow-[0_0_60px_rgba(20,184,166,0.3)]" />

            <div className="absolute inset-16 rounded-full bg-gradient-to-br from-teal-300/30 via-cyan-400/10 to-transparent blur-xl" />

            <div className="relative z-10 flex h-28 w-28 items-center justify-center rounded-full border border-teal-300/40 bg-[#062421] shadow-[0_0_50px_rgba(20,184,166,0.25)] md:h-32 md:w-32">
              <div className="text-5xl md:text-6xl">🎙️</div>
            </div>

            {/* Sound waves */}
            <div className="absolute -left-20 right-0 top-1/2 h-20 -translate-y-1/2 md:-left-32 md:-right-32">
              <div className="flex h-full items-center justify-center gap-1 opacity-80">
                {[4, 8, 16, 28, 12, 34, 18, 42, 22, 10, 30, 15, 38, 20, 8].map(
                  (height, index) => (
                    <motion.div
                      key={index}
                      animate={{
                        height: [
                          `${height}px`,
                          `${Math.max(6, height * 0.45)}px`,
                          `${height}px`,
                        ],
                      }}
                      transition={{
                        duration: 1 + index * 0.04,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }}
                      className="w-1 rounded-full bg-gradient-to-b from-teal-300 to-cyan-500"
                    />
                  ),
                )}
              </div>
            </div>
          </div>

          {/* Live caption */}
          <div className="w-full max-w-2xl">
            <div className="mb-3 flex items-center justify-center gap-3">
              <div className="h-px flex-1 bg-gradient-to-r from-transparent to-teal-400/50" />

              <div className="flex items-center gap-2 text-xs font-bold tracking-[0.2em] text-teal-300">
                <span className="animate-pulse">▮▮</span>
                LIVE CAPTION
                <span className="animate-pulse">▮▮</span>
              </div>

              <div className="h-px flex-1 bg-gradient-to-l from-transparent to-teal-400/50" />
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={latestCaption || 'empty-caption'}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="min-h-[96px] rounded-2xl border border-teal-400/25 bg-[#061b19]/80 px-6 py-5 text-center shadow-[0_0_40px_rgba(20,184,166,0.06)] backdrop-blur-xl md:px-10"
              >
                {latestCaption ? (
                  <>
                    <div className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-teal-400/70">
                      {isLocalMessage ? 'You' : 'MediSathi'}
                    </div>

                    <p className="text-base leading-7 text-white md:text-lg">
                      {latestCaption}
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-base leading-7 text-white/70 md:text-lg">
                      Hello! I&apos;m MediSathi, your AI healthcare
                      assistant.
                    </p>

                    <p className="mt-1 text-base text-white/45">
                      How can I help you with your health today?
                    </p>
                  </>
                )}
              </motion.div>
            </AnimatePresence>

            <p className="mt-3 text-center text-xs text-white/35">
              🛡️ General health information only — not a medical
              diagnosis.
            </p>
          </div>
        </div>
      </div>

      {/* Existing LiveKit chat transcript */}
      <div className="absolute inset-x-0 top-0 bottom-[135px] z-50 flex flex-col md:bottom-[170px]">
        <AnimatePresence>
          {chatOpen && (
            <motion.div
              {...CHAT_MOTION_PROPS}
              className="flex h-full w-full flex-col gap-4 space-y-3"
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

      {/* Bottom controls */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-[100] md:inset-x-12"
      >
        {isPreConnectBufferEnabled && (
          <AnimatePresence>
            {messages.length === 0 && (
              <MotionMessage
                key="pre-connect-message"
                duration={2}
                aria-hidden={messages.length > 0}
                {...SHIMMER_MOTION_PROPS}
                className="pointer-events-none mx-auto block w-full max-w-2xl pb-4 text-center text-sm font-semibold text-white/60"
              >
                {preConnectMessage}
              </MotionMessage>
            )}
          </AnimatePresence>
        )}

        <div className="relative mx-auto max-w-3xl pb-3 md:pb-8">
          <Fade
            bottom
            className="absolute inset-x-0 top-0 h-8 -translate-y-full"
          />

          <div className="rounded-[28px] border border-white/10 bg-[#061513]/90 p-2 shadow-2xl backdrop-blur-2xl">
            <AgentControlBar
              variant="livekit"
              controls={controls}
              isChatOpen={chatOpen}
              isConnected={session.isConnected}
              onDisconnect={session.end}
              onIsChatOpenChange={setChatOpen}
            />
          </div>
        </div>
      </motion.div>

      {/* Footer */}
      <footer className="absolute bottom-0 left-0 right-0 z-40 hidden items-center justify-between border-t border-white/5 bg-[#031312]/80 px-6 py-3 text-xs text-white/35 backdrop-blur-xl md:flex">
        <div>
          🛡️ General health information only. Not a substitute for
          professional medical advice.
        </div>

        <div>
          Powered by <span className="text-white/60">Murf Falcon</span>{' '}
          + <span className="text-white/60">LiveKit</span>
        </div>
      </footer>
    </section>
  );
}