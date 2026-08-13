'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext, useVoiceAssistant } from '@livekit/components-react';
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

type SessionPhase = 'ready' | 'connecting' | 'listening' | 'speaking' | 'ended';

const resolvePhaseFromVoiceState = (voiceState?: string): SessionPhase => {
  switch (voiceState) {
    case 'speaking':
      return 'speaking';
    case 'listening':
    case 'thinking':
    case 'idle':
    default:
      return 'listening';
  }
};

const resolveStatusCopy = (phase: SessionPhase) => {
  switch (phase) {
    case 'connecting':
      return {
        label: 'Connecting',
        description: 'The agent is joining the call. Please wait a moment.',
      };
    case 'speaking':
      return {
        label: 'Speaking',
        description: 'The agent is replying to you now.',
      };
    case 'ended':
      return {
        label: 'Call ended',
        description: 'The conversation has finished. Start again whenever you are ready.',
      };
    case 'listening':
    default:
      return {
        label: 'Ready',
        description: 'The agent is ready to help. Tap the button to begin.',
      };
  }
};

const getPermissionError = (error: unknown) => {
  if (error instanceof DOMException && error.name === 'NotAllowedError') {
    return 'Allow microphone access in your browser, then refresh the page and try again.';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Microphone access was blocked. Please allow it in your browser and try again.';
};

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start, end } = useSessionContext();
  const { resolvedTheme } = useTheme();
  const { state: voiceAssistantState } = useVoiceAssistant();
  const { state: agentState } = useAgent();
  const [sessionPhase, setSessionPhase] = useState<SessionPhase>('ready');
  const [permissionError, setPermissionError] = useState<string | null>(null);
  const [hasAttemptedStart, setHasAttemptedStart] = useState(false);
  const [currentTab, setCurrentTab] = useState<'home' | 'schemes' | 'fraud' | 'complaint' | 'escalations'>('home');

  const handleStartCall = async () => {
    setPermissionError(null);
    setHasAttemptedStart(true);
    setSessionPhase('connecting');

    try {
      await start();
    } catch (error) {
      setHasAttemptedStart(false);
      setSessionPhase('ready');
      setPermissionError(getPermissionError(error));
    }
  };

  useEffect(() => {
    if (!hasAttemptedStart) {
      return;
    }

    if (isConnected) {
      const nextPhase = resolvePhaseFromVoiceState(voiceAssistantState ?? agentState);
      setSessionPhase(nextPhase);
      return;
    }

    if (sessionPhase !== 'connecting') {
      setSessionPhase('ended');
    }
  }, [agentState, hasAttemptedStart, isConnected, sessionPhase, voiceAssistantState]);

  const statusCopy = resolveStatusCopy(sessionPhase);

  return (
    <AnimatePresence mode="wait">
      {!isConnected && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={sessionPhase === 'ended' ? 'Start again' : appConfig.startButtonText}
          statusLabel={statusCopy.label}
          statusDescription={statusCopy.description}
          permissionError={permissionError}
          onStartCall={handleStartCall}
          currentTab={currentTab}
          onTabChange={setCurrentTab}
        />
      )}
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
