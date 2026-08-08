'use client';

import React, { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { ConnectionState } from 'livekit-client';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView, type WelcomeViewState } from '@/components/app/welcome-view';

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
    duration: 0.4,
    ease: 'easeInOut',
  },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const session = useSessionContext();
  const isConnected = session.isConnected;
  const isConnecting =
    session.connectionState === ConnectionState.Connecting ||
    (session.connectionState as string) === 'connecting';
  const start = session.start;
  const { state: agentState } = useAgent();
  const { resolvedTheme } = useTheme();

  const [hasCallEnded, setHasCallEnded] = useState(false);
  const [micError, setMicError] = useState<{ message: string; description: string } | null>(null);

  // Track if we were previously connected, so when user or agent disconnects we go to CALL_ENDED state
  const [wasConnected, setWasConnected] = useState(false);
  useEffect(() => {
    if (isConnected) {
      setWasConnected(true);
      setHasCallEnded(false);
    } else if (wasConnected && !isConnected && !isConnecting) {
      setHasCallEnded(true);
    }
  }, [isConnected, isConnecting, wasConnected]);

  const handleStartCall = async () => {
    setMicError(null);
    setHasCallEnded(false);

    // 1. Check microphone access in browser
    try {
      if (typeof window !== 'undefined' && navigator?.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
      }
    } catch (err: any) {
      console.error('Microphone permission check failed:', err);
      if (err?.name === 'NotAllowedError' || err?.name === 'PermissionDeniedError') {
        setMicError({
          message: 'Microphone access is blocked',
          description: 'Please allow microphone access in your browser settings and try again.',
        });
        return;
      } else if (err?.name === 'NotFoundError' || err?.name === 'DevicesNotFoundError') {
        setMicError({
          message: 'No microphone found',
          description: 'Please connect a microphone to your device and try again.',
        });
        return;
      } else {
        setMicError({
          message: 'Microphone access error',
          description: err?.message || 'Unable to access your microphone.',
        });
        return;
      }
    }

    // 2. Start LiveKit session
    try {
      await start();
    } catch (err: any) {
      console.error('LiveKit connection error:', err);
      setMicError({
        message: 'Connection failed',
        description: err?.message || 'Unable to connect to the voice agent server. Please try again.',
      });
    }
  };

  const handleStartAgain = async () => {
    setHasCallEnded(false);
    setMicError(null);
    await handleStartCall();
  };

  const handleTryAgain = async () => {
    setMicError(null);
    await handleStartCall();
  };

  // Determine non-connected state
  let welcomeState: WelcomeViewState = 'READY';
  if (micError !== null) {
    welcomeState = 'MIC_ERROR';
  } else if (hasCallEnded && !isConnected && !isConnecting) {
    welcomeState = 'CALL_ENDED';
  } else if (isConnecting || (isConnected && (agentState === 'connecting' || agentState === 'initializing'))) {
    welcomeState = 'CONNECTING';
  }

  return (
    <AnimatePresence mode="wait">
      {/* Welcome / Pre-connection / Call Ended / Error views */}
      {!isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          state={welcomeState}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStartCall}
          onStartAgain={handleStartAgain}
          onTryAgain={handleTryAgain}
          errorMessage={micError?.message}
          errorDescription={micError?.description}
        />
      )}

      {/* Connected Active Voice Session view */}
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
