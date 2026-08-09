'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { MediaDeviceFailure } from 'livekit-client';
import { MicOffIcon, RefreshCwIcon, ShoppingBagIcon } from 'lucide-react';
import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { SessionEvent, useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { AgentSessionView_01 } from '@/components/agents-ui/blocks/agent-session-view-01';
import { WelcomeView } from '@/components/app/welcome-view';
import { Button } from '@/components/ui/button';

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
  const session = useSessionContext();
  const { isConnected, start } = session;
  const { resolvedTheme } = useTheme();
  const [viewState, setViewState] = useState<'ready' | 'connecting' | 'active' | 'ended' | 'error'>(
    'ready'
  );
  const connectedOnce = useRef(false);

  const showMicrophoneError = useCallback((error: Error) => {
    const failure = MediaDeviceFailure.getFailure(error);
    const permissionDenied =
      failure === MediaDeviceFailure.PermissionDenied ||
      error.name === 'NotAllowedError' ||
      /permission denied|not allowed/i.test(error.message);

    if (permissionDenied) {
      setViewState('error');
      void session.end();
    }
  }, [session]);

  useEffect(() => {
    session.internal.emitter.on(SessionEvent.MediaDevicesError, showMicrophoneError);
    return () => {
      session.internal.emitter.off(SessionEvent.MediaDevicesError, showMicrophoneError);
    };
  }, [session.internal.emitter, showMicrophoneError]);

  useEffect(() => {
    if (isConnected) {
      connectedOnce.current = true;
      setViewState('active');
    } else if (connectedOnce.current && viewState === 'active') {
      setViewState('ended');
    }
  }, [isConnected, viewState]);

  const handleStart = async () => {
    setViewState('connecting');
    try {
      await start({ tracks: { microphone: { enabled: true } } });
    } catch (error) {
      console.error('Unable to start voice session', error);
      showMicrophoneError(error instanceof Error ? error : new Error(String(error)));
    }
  };

  const handleRestart = () => {
    connectedOnce.current = false;
    setViewState('ready');
  };

  return (
    <AnimatePresence mode="wait">
      {/* Welcome view */}
      {viewState === 'ready' && (
        <MotionWelcomeView
          key="welcome"
          {...VIEW_MOTION_PROPS}
          startButtonText={appConfig.startButtonText}
          onStartCall={handleStart}
        />
      )}
      {viewState === 'connecting' && (
        <motion.section
          key="connecting"
          {...VIEW_MOTION_PROPS}
          className="mx-auto flex max-w-md flex-col items-center px-6 text-center"
          aria-live="polite"
        >
          <div className="relative mb-7 grid size-24 place-items-center rounded-full bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300">
            <ShoppingBagIcon className="size-9" />
            <span className="absolute inset-0 animate-ping rounded-full border border-orange-500/40" />
          </div>
          <p className="font-mono text-xs font-bold tracking-[0.2em] text-orange-700 uppercase">
            Connecting
          </p>
          <h2 className="mt-3 text-3xl font-bold">Mitra is joining your call</h2>
          <p className="mt-3 text-stone-500 dark:text-stone-400">
            बस एक पल रुकिए। Please allow microphone access when prompted.
          </p>
        </motion.section>
      )}
      {viewState === 'error' && (
        <motion.section
          key="microphone-error"
          {...VIEW_MOTION_PROPS}
          className="mx-auto max-w-md px-6 text-center"
          role="alert"
        >
          <span className="mx-auto mb-6 grid size-20 place-items-center rounded-full bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-300">
            <MicOffIcon className="size-8" />
          </span>
          <p className="font-mono text-xs font-bold tracking-[0.2em] text-red-700 uppercase">
            Microphone blocked
          </p>
          <h2 className="mt-3 text-3xl font-bold">Mitra can’t hear you yet</h2>
          <p className="mt-3 leading-7 text-stone-600 dark:text-stone-300">
            Open your browser’s site settings, allow microphone access, then try again.
          </p>
          <Button onClick={handleRestart} className="mt-7 h-12 rounded-xl px-6">
            <RefreshCwIcon /> Try again
          </Button>
        </motion.section>
      )}
      {viewState === 'ended' && (
        <motion.section
          key="ended"
          {...VIEW_MOTION_PROPS}
          className="mx-auto max-w-md px-6 text-center"
          aria-live="polite"
        >
          <span className="mx-auto mb-6 grid size-20 place-items-center rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            <ShoppingBagIcon className="size-8" />
          </span>
          <p className="font-mono text-xs font-bold tracking-[0.2em] text-emerald-700 uppercase">
            Call ended
          </p>
          <h2 className="mt-3 text-3xl font-bold">Thanks for shopping local</h2>
          <p className="mt-3 text-stone-500 dark:text-stone-400">
            बातचीत पूरी हुई। You can speak with Mitra again anytime.
          </p>
          <Button onClick={handleRestart} className="mt-7 h-12 rounded-xl px-6">
            <RefreshCwIcon /> Start another call
          </Button>
        </motion.section>
      )}
      {/* Session view */}
      {viewState === 'active' && isConnected && (
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
          preConnectMessage="Mitra is listening — बोलिए, मैं सुन रहा हूँ"
          onMicrophoneError={showMicrophoneError}
          className="fixed inset-0"
        />
      )}
    </AnimatePresence>
  );
}
