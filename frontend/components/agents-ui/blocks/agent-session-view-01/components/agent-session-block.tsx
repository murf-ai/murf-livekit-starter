'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Track } from 'livekit-client';
import { AlertTriangle, Mic, ShieldCheck, Volume2 } from 'lucide-react';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
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

export interface AgentSessionView_01Props {
  /**
   * Message shown above the controls before the first chat message is sent.
   *
   * @default 'Agent is listening, ask it a question'
   */
  preConnectMessage?: string;
  /**
   * Enables or disables the chat toggle and transcript input controls.
   *
   * @default true
   */
  supportsChatInput?: boolean;
  /**
   * Enables or disables camera controls in the bottom control bar.
   *
   * @default true
   */
  supportsVideoInput?: boolean;
  /**
   * Enables or disables screen sharing controls in the bottom control bar.
   *
   * @default true
   */
  supportsScreenShare?: boolean;
  /**
   * Shows a pre-connect buffer state with a shimmer message before messages appear.
   *
   * @default true
   */
  isPreConnectBufferEnabled?: boolean;

  /** Selects the visualizer style rendered in the main tile area. */
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  /** Primary hex color used by supported audio visualizer variants. */
  audioVisualizerColor?: `#${string}`;
  /** Hue shift intensity used by certain visualizers. */
  audioVisualizerColorShift?: number;
  /** Number of bars to render when `audioVisualizerType` is `bar`. */
  audioVisualizerBarCount?: number;
  /** Number of rows in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridRowCount?: number;
  /** Number of columns in the visualizer when `audioVisualizerType` is `grid`. */
  audioVisualizerGridColumnCount?: number;
  /** Number of radial bars when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialBarCount?: number;
  /** Base radius of the radial visualizer when `audioVisualizerType` is `radial`. */
  audioVisualizerRadialRadius?: number;
  /** Stroke width of the wave path when `audioVisualizerType` is `wave`. */
  audioVisualizerWaveLineWidth?: number;
  /** Optional class name merged onto the outer `<section>` container. */
  className?: string;
}

export function AgentSessionView_01({
  preConnectMessage = 'Agent is listening, ask it a question',
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
  const [chatOpen, setChatOpen] = useState(false);
  const [microphoneError, setMicrophoneError] = useState<string | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();

  const day3State =
    agentState === 'speaking'
      ? 'Speaking'
      : agentState === 'listening'
        ? 'Listening'
        : session.isConnected
          ? 'Connecting'
          : 'Call ended';
  const speakerText =
    day3State === 'Speaking'
      ? 'Agent is speaking'
      : day3State === 'Listening'
        ? 'Listening to you'
        : day3State === 'Connecting'
          ? 'Connecting to Suraksha Saathi'
          : 'Call ended';
  const StatusIcon =
    day3State === 'Speaking'
      ? Volume2
      : day3State === 'Listening'
        ? Mic
        : day3State === 'Connecting'
          ? ShieldCheck
          : AlertTriangle;

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

  return (
    <section
      ref={ref}
      data-day3-state={day3State}
      data-day3-speaker={speakerText}
      className={cn('bg-background relative z-10 h-full w-full overflow-hidden', className)}
      {...props}
    >
      <Fade top className="absolute inset-x-4 top-0 z-10 h-40" />

      <div className="absolute inset-x-4 top-4 z-30 mx-auto flex max-w-3xl flex-col gap-3 md:top-6">
        <div className="bg-background/95 rounded-lg border border-teal-800/15 px-4 py-3 shadow-sm backdrop-blur">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-foreground flex items-center gap-2 text-sm font-semibold">
                <StatusIcon className="size-4 text-teal-700 dark:text-teal-300" />
                {speakerText}
              </p>
              <p className="text-muted-foreground text-xs leading-5">
                Telugu UPI fraud help. Do not share OTP, UPI PIN, CVV, or password.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-medium sm:grid-cols-5">
              {['Ready', 'Connecting', 'Listening', 'Speaking', 'Call ended'].map((stateName) => {
                const isActive = stateName === day3State;

                return (
                  <span
                    key={stateName}
                    className={cn(
                      'rounded-md border px-2.5 py-1.5 text-center',
                      isActive
                        ? 'border-teal-700 bg-teal-700 text-white'
                        : 'border-border bg-background text-muted-foreground'
                    )}
                  >
                    {stateName}
                  </span>
                );
              })}
            </div>
          </div>
        </div>

        {microphoneError && (
          <Alert className="border-amber-500/40 bg-amber-50 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
            <AlertTriangle className="size-4" />
            <AlertTitle>Microphone permission blocked</AlertTitle>
            <AlertDescription>
              {microphoneError} Open your browser site settings, allow microphone access, then start
              again.
            </AlertDescription>
          </Alert>
        )}
      </div>

      {/* transcript */}

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
      {/* Tile layout */}
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
      {/* Bottom */}
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
            onDisconnect={session.end}
            onDeviceError={({ source, error }) => {
              if (source === Track.Source.Microphone) {
                setMicrophoneError(error.message || 'The browser did not allow the microphone.');
              }
            }}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>
    </section>
  );
}
