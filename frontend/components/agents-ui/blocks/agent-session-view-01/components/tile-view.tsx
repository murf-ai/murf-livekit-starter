import React, { useMemo } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, type MotionProps, motion } from 'motion/react';
import {
  type TrackReference,
  VideoTrack,
  useAgent,
  useLocalParticipant,
  useTracks,
  useVoiceAssistant,
} from '@livekit/components-react';
import { cn } from '@/lib/shadcn/utils';
import { FinanceAvatarVideo } from '@/components/app/finance-avatar-video';

const ANIMATION_TRANSITION: MotionProps['transition'] = {
  type: 'spring',
  stiffness: 675,
  damping: 75,
  mass: 1,
};

export function useLocalTrackRef(source: Track.Source) {
  const { localParticipant } = useLocalParticipant();
  const publication = localParticipant.getTrackPublication(source);
  const trackRef = useMemo<TrackReference | undefined>(
    () => (publication ? { source, participant: localParticipant, publication } : undefined),
    [source, publication, localParticipant]
  );
  return trackRef;
}

interface TileLayoutProps {
  chatOpen: boolean;
  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerWaveLineWidth?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerBarCount?: number;
}

export function TileLayout({ chatOpen }: TileLayoutProps) {
  const { videoTrack: agentVideoTrack } = useVoiceAssistant();
  const { state: agentState } = useAgent();
  const [screenShareTrack] = useTracks([Track.Source.ScreenShare]);
  const cameraTrack: TrackReference | undefined = useLocalTrackRef(Track.Source.Camera);

  const isCameraEnabled = cameraTrack && !cameraTrack.publication.isMuted;
  const isScreenShareEnabled = screenShareTrack && !screenShareTrack.publication.isMuted;
  const hasSecondTile = isCameraEnabled || isScreenShareEnabled;

  const isAvatar = agentVideoTrack !== undefined;
  const videoWidth = agentVideoTrack?.publication.dimensions?.width ?? 0;
  const videoHeight = agentVideoTrack?.publication.dimensions?.height ?? 0;

  // Chat open: pin a compact avatar at the top so messages stay readable.
  // Chat closed: large centered hero avatar.
  return (
    <div
      className={cn(
        'pointer-events-none absolute inset-x-0 z-20 flex justify-center',
        chatOpen
          ? 'top-14 h-auto md:top-16'
          : 'top-8 bottom-32 items-center md:top-12 md:bottom-40'
      )}
    >
      <div
        className={cn(
          'relative flex items-start justify-center gap-3',
          !chatOpen && 'h-full w-full max-w-2xl items-center px-4'
        )}
      >
        <AnimatePresence mode="popLayout">
          {!isAvatar && (
            <motion.div
              key="agent"
              layoutId="agent"
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={ANIMATION_TRANSITION}
              className="relative flex flex-col items-center justify-center"
            >
              <FinanceAvatarVideo
                isSpeaking={agentState === 'speaking'}
                alwaysPlay
                size={chatOpen ? 'md' : 'hero'}
                className="shadow-2xl"
              />
            </motion.div>
          )}

          {isAvatar && (
            <motion.div
              key="avatar"
              layoutId="avatar"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={ANIMATION_TRANSITION}
              className={cn(
                'overflow-hidden bg-black drop-shadow-xl/80',
                chatOpen ? 'size-28 rounded-full' : 'h-auto w-full max-w-md rounded-xl'
              )}
            >
              <VideoTrack
                width={videoWidth}
                height={videoHeight}
                trackRef={agentVideoTrack}
                className={cn(chatOpen ? 'size-28 object-cover' : 'w-full')}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Local camera / screen share — only when chat is open and enabled */}
        <AnimatePresence>
          {chatOpen && hasSecondTile && (
            <motion.div
              key="camera"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={ANIMATION_TRANSITION}
              className="pointer-events-auto aspect-square size-28 overflow-hidden rounded-full drop-shadow-lg"
            >
              <VideoTrack
                trackRef={cameraTrack || screenShareTrack}
                width={(cameraTrack || screenShareTrack)?.publication.dimensions?.width ?? 0}
                height={(cameraTrack || screenShareTrack)?.publication.dimensions?.height ?? 0}
                className="size-28 rounded-full object-cover"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
