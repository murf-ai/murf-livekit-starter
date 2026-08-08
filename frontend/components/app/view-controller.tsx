'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionSessionView = motion.create(AgentSessionView_01);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: {
      opacity: 1,
    },
    hidden: {
      opacity: 0,
    },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const [isConnecting, setIsConnecting] = useState(false);
  const [hasCallEnded, setHasCallEnded] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);
  const wasConnectedRef = useRef(false);

  useEffect(() => {
    if (isConnected) {
      wasConnectedRef.current = true;
      setIsConnecting(false);
      setStartError(null);
      return;
    }

    if (wasConnectedRef.current) {
      setHasCallEnded(true);
      wasConnectedRef.current = false;
      setIsConnecting(false);
    }
  }, [isConnected]);

  const handleStartCall = async () => {
    setIsConnecting(true);
    setHasCallEnded(false);
    setStartError(null);

    try {
      await start();
    } catch (error) {
      console.error(error);
      setIsConnecting(false);
      const message = error instanceof Error ? error.message : '';
      const looksLikeMicError = /microphone|permission|denied|notallowed/i.test(message);
      setStartError(
        looksLikeMicError
          ? 'Microphone permission blocked. Open your browser site settings, allow microphone access, then start again.'
          : 'Call could not start. Check your connection and microphone permission, then start again.'
      );
    }
  };

  return (
    <AnimatePresence mode="wait">
      {/* Welcome view */}
      {!isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={hasCallEnded ? 'Start again' : appConfig.startButtonText}
          state={isConnecting ? 'connecting' : hasCallEnded ? 'ended' : 'ready'}
          microphoneError={startError}
          onStartCall={handleStartCall}
        />
      )}
      {/* Session view */}
      {isConnected && (
        <MotionSessionView
          key="session-view"
          {...VIEW_MOTION_PROPS}
          supportsChatInput={appConfig.supportsChatInput}
          supportsVideoInput={appConfig.supportsVideoInput}
          supportsScreenShare={appConfig.supportsScreenShare}
          isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
          audioVisualizerType={appConfig.audioVisualizerType}
          audioVisualizerColor={
            resolvedTheme === 'dark'
              ? appConfig.audioVisualizerColorDark
              : appConfig.audioVisualizerColor
          }
          audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
          audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
          audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
          audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
          audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
          audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
          audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
