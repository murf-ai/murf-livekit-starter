'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext, useSessionMessages, useVoiceAssistant } from '@livekit/components-react';
import { AgentChatTranscript } from '@/components/agents-ui/agent-chat-transcript';
import {
  AgentControlBar,
  type AgentControlBarControls,
} from '@/components/agents-ui/agent-control-bar';
import { Shimmer } from '@/components/ai-elements/shimmer';
import { cn } from '@/lib/shadcn/utils';
import { TileLayout } from '@/components/agents-ui/blocks/agent-session-view-01/components/tile-view';
import { BharatPayStateIndicator, BharatPayCallEndedView } from '@/components/app/bharatpay-state-indicator';
import { Fade } from '@/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block';
import type { AgentSessionView_01Props } from '@/components/agents-ui/blocks/agent-session-view-01/components/agent-session-block';
import { VoiceBarVisualizer } from '@/components/ui/voice-bar-visualizer';

const MotionMessage = motion.create(Shimmer);

const BOTTOM_VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, translateY: '0%' },
    hidden: { opacity: 0, translateY: '100%' },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.3, delay: 0.5, ease: 'easeOut' },
};

const CHAT_MOTION_PROPS = {
  variants: {
    hidden: { opacity: 0, transition: { ease: 'easeOut', duration: 0.3 } },
    visible: { opacity: 1, transition: { delay: 0.2, ease: 'easeOut', duration: 0.3 } },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

const SHIMMER_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1, transition: { ease: 'easeIn', duration: 0.5, delay: 0.8 } },
    hidden: { opacity: 0, transition: { ease: 'easeIn', duration: 0.5, delay: 0 } },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
};

export function BharatPaySessionView({
  preConnectMessage = 'Namaste! Pooja is ready — start speaking anytime',
  supportsChatInput = true,
  supportsVideoInput = false,
  supportsScreenShare = false,
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
  const [chatOpen, setChatOpen] = useState(false); // Default to clean voice layout
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const { state: agentState } = useAgent();
  const { state: voiceState } = useVoiceAssistant();
  const [showEnded, setShowEnded] = useState(false);

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

  // Watch for disconnection
  useEffect(() => {
    if (agentState === 'disconnected') {
      const timer = setTimeout(() => setShowEnded(true), 400);
      return () => clearTimeout(timer);
    } else {
      setShowEnded(false);
    }
  }, [agentState]);

  const aiLoaderStatus = React.useMemo(() => {
    if (!session.isConnected) return 'connecting';
    if (voiceState === 'speaking') return 'speaking';
    if (voiceState === 'listening') return 'listening';
    return 'listening';
  }, [session.isConnected, voiceState]);

  const showCentralVoiceVisualizer = !chatOpen;

  return (
    <section
      ref={ref}
      className={cn('relative flex h-full w-full flex-col overflow-hidden bg-[#030303]', className)}
      {...props}
    >
      {/* Brand header strip */}
      <div className="flex w-full items-center justify-between border-b border-white/[0.04] bg-[#050505]/70 px-6 py-4 backdrop-blur-md z-50">
        <div className="flex items-center gap-2">
          <div className="flex size-6 items-center justify-center rounded-lg bg-gradient-to-br from-[#7c3aed] to-[#4f46e5]">
            <svg width="14" height="14" viewBox="0 0 52 52" fill="none">
              <path d="M14 12h14c4.418 0 8 3.582 8 8 0 2.21-.895 4.21-2.344 5.656A7.972 7.972 0 0 1 36 32c0 4.418-3.582 8-8 8H14V12zm6 6v6h8a3 3 0 0 0 0-6H20zm0 12v6h8a3 3 0 0 0 0-6H20z" fill="white" />
            </svg>
          </div>
          <span className="font-sans text-xs font-semibold tracking-wide text-[#f5f5f5] uppercase">
            BharatPay
          </span>
        </div>

        {/* Live state indicator */}
        <BharatPayStateIndicator agentState={agentState} isConnected={session.isConnected} />
      </div>

      <Fade top className="absolute inset-x-4 top-16 z-10 h-24" />

      {/* Main content viewport */}
      <div className="relative flex-1 w-full h-full">
        {showCentralVoiceVisualizer ? (
          <div className="flex h-full w-full flex-col items-center justify-center px-4 pb-24 relative">
            {/* Ambient pulse glow behind the visualizer */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
              <div className="absolute top-1/2 left-1/2 h-[350px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-purple-600/[0.035] blur-[90px]" />
            </div>

            <div className="relative w-full max-w-[80vw] overflow-visible px-2 flex justify-center">
              <VoiceBarVisualizer status={aiLoaderStatus} />
            </div>

            <div className="mt-12 flex flex-col items-center text-center">
              <span className="font-sans text-[10px] font-semibold tracking-[0.25em] text-[#8b5cf6] uppercase shadow-sm">
                BharatPay Pooja
              </span>
              <span className="mt-2 text-xs font-medium tracking-wider text-[#92929a] uppercase">
                {aiLoaderStatus === 'speaking' ? 'Pooja is speaking' : 'Pooja is listening'}
              </span>
            </div>
          </div>
        ) : (
          <>
            {/* Chat transcript */}
            <div className="absolute top-16 bottom-[135px] flex w-full flex-col md:bottom-[170px]">
              <AnimatePresence>
                {chatOpen && (
                  <motion.div
                    {...CHAT_MOTION_PROPS}
                    className="flex h-full w-full flex-col gap-4 space-y-3 transition-opacity duration-300 ease-out"
                  >
                    <AgentChatTranscript
                      agentState={agentState}
                      messages={messages}
                      className="mx-auto w-full max-w-2xl [&_.is-user>div]:rounded-[22px] [&>div>div]:px-4 [&>div>div]:pt-12 md:[&>div>div]:px-6"
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Visualizer tile */}
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
          </>
        )}
      </div>

      {/* Controls */}
      <motion.div
        {...BOTTOM_VIEW_MOTION_PROPS}
        className="absolute inset-x-3 bottom-0 z-50 md:inset-x-12"
      >
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

        <div className="bg-transparent relative mx-auto max-w-2xl pb-3 md:pb-12">
          <Fade bottom className="absolute inset-x-0 top-0 h-4 -translate-y-full" />
          <AgentControlBar
            variant="livekit"
            controls={controls}
            isChatOpen={chatOpen}
            isConnected={session.isConnected}
            onDisconnect={session.end}
            onIsChatOpenChange={setChatOpen}
          />
        </div>
      </motion.div>

      {/* Call Ended overlay */}
      <AnimatePresence>
        {showEnded && (
          <BharatPayCallEndedView onRestart={() => { setShowEnded(false); session.end(); window.location.reload(); }} />
        )}
      </AnimatePresence>
    </section>
  );
}
