'use client';

import { useEffect } from 'react';
import { RemoteAudioTrack, Track } from 'livekit-client';
import { useRemoteParticipants } from '@livekit/components-react';

/** Keep agent audio at max safe volume (1.0). Never set > 1 — crashes HTMLMediaElement. */
export function AudioVolumeBooster() {
  const remoteParticipants = useRemoteParticipants();

  useEffect(() => {
    const apply = () => {
      for (const participant of remoteParticipants) {
        for (const publication of participant.audioTrackPublications.values()) {
          const track = publication.track;
          if (
            track &&
            publication.source === Track.Source.Microphone &&
            track instanceof RemoteAudioTrack
          ) {
            try {
              track.setVolume(1);
            } catch {
              // ignore
            }
          }
        }
      }
      document.querySelectorAll<HTMLAudioElement>('audio').forEach((el) => {
        el.volume = 1;
      });
    };

    apply();
    const interval = setInterval(apply, 1000);
    return () => clearInterval(interval);
  }, [remoteParticipants]);

  return null;
}
