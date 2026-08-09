'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useAgent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { ConnectingView } from '@/components/app/connecting-view';
import { CallEndedView } from '@/components/app/call-ended-view';
import { ParticleSwarmCanvas, type AgentUIState } from '@/components/app/particle-swarm-canvas';
import { MicPermissionModal } from '@/components/app/mic-permission-modal';
import { useMicPermissions } from '@/hooks/useMicPermissions';

const MotionWelcomeView = motion.create(WelcomeView);
const MotionConnectingView = motion.create(ConnectingView);
const MotionSessionView = motion.create(AgentSessionView_01);
const MotionCallEndedView = motion.create(CallEndedView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.4, ease: 'easeInOut' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start, end } = useSessionContext();
  const { state: agentState } = useAgent();
  const { resolvedTheme } = useTheme();
  
  const [isConnectingManual, setIsConnectingManual] = useState(false);
  const [hasStartedOnce, setHasStartedOnce] = useState(false);
  const [isCallEnded, setIsCallEnded] = useState(false);
  const [showMicModal, setShowMicModal] = useState(false);

  const { permissionState, requestMic } = useMicPermissions();

  useEffect(() => {
    if (isConnected) {
      setHasStartedOnce(true);
      setIsCallEnded(false);
      setIsConnectingManual(false);
    }
  }, [isConnected]);

  // Handle End Call Transition
  const handleDisconnect = async () => {
    setIsConnectingManual(false);
    setIsCallEnded(true);
    try {
      await end();
    } catch (err) {
      console.warn('Error ending session:', err);
    }
  };

  const handleStartCall = async () => {
    setIsCallEnded(false);
    if (permissionState === 'denied') {
      setShowMicModal(true);
      return;
    }
    const granted = await requestMic();
    if (!granted) {
      setShowMicModal(true);
      return;
    }
    setIsConnectingManual(true);
    try {
      // Ensure previous room is fully torn down before minting a new one.
      if (isConnected) {
        await end();
      }
      await start();
    } catch (err) {
      console.error('Failed to start session:', err);
      setIsConnectingManual(false);
      setIsCallEnded(true);
    }
  };

  const isConnecting = isConnectingManual || agentState === 'connecting' || agentState === 'initializing';

  // Map low-level session/agent state → Ready / Connecting / Thinking / Listening / Speaking / Ended
  let uiState: AgentUIState = 'ready';
  if (isConnecting && !isConnected) {
    uiState = 'connecting';
  } else if (isConnected) {
    // LiveKit AgentState: connecting | initializing | listening | thinking | speaking | ...
    switch (agentState) {
      case 'speaking':
        uiState = 'speaking';
        break;
      case 'thinking':
        uiState = 'thinking';
        break;
      case 'listening':
        uiState = 'listening';
        break;
      case 'connecting':
      case 'initializing':
        uiState = 'connecting';
        break;
      default:
        uiState = 'listening';
    }
  } else if (isCallEnded && hasStartedOnce) {
    uiState = 'ended';
  } else {
    uiState = 'ready';
  }

  return (
    <div className="relative min-h-screen w-full bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* 3D Three.js Particle Swarm Background Canvas */}
      <ParticleSwarmCanvas agentState={uiState} />

      <AnimatePresence mode="wait">
        {/* State 1: Ready */}
        {uiState === 'ready' && (
          <MotionWelcomeView
            key="welcome"
            {...VIEW_MOTION_PROPS}
            startButtonText={appConfig.startButtonText}
            onStartCall={handleStartCall}
          />
        )}

        {/* State 2: Connecting */}
        {uiState === 'connecting' && (
          <MotionConnectingView
            key="connecting"
            {...VIEW_MOTION_PROPS}
            onCancel={() => end()}
          />
        )}

        {/* Active call: listening / thinking / speaking */}
        {(uiState === 'listening' ||
          uiState === 'thinking' ||
          uiState === 'speaking') && (
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
            onDisconnect={handleDisconnect}
            className="fixed inset-0"
          />
        )}

        {/* State 5: Call Ended */}
        {uiState === 'ended' && (
          <MotionCallEndedView
            key="call-ended"
            {...VIEW_MOTION_PROPS}
            onStartAgain={handleStartCall}
          />
        )}
      </AnimatePresence>

      {/* Step 4: Microphone Permission Error Handling Modal */}
      <MicPermissionModal
        isOpen={showMicModal}
        onRetry={async () => {
          const granted = await requestMic();
          if (granted) {
            setShowMicModal(false);
            start();
          }
        }}
        onClose={() => setShowMicModal(false)}
      />
    </div>
  );
}
