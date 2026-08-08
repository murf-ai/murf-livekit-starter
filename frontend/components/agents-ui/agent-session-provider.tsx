import { Room } from 'livekit-client';
import {
  RoomAudioRenderer,
  type RoomAudioRendererProps,
  SessionProvider,
  type SessionProviderProps,
  type UseSessionReturn,
} from '@livekit/components-react';

export type AgentSessionProviderProps = SessionProviderProps &
  RoomAudioRendererProps & {
    room?: Room;
    volume?: number;
    muted?: boolean;
    session: UseSessionReturn;
    children: React.ReactNode;
  };

export function AgentSessionProvider({
  session,
  children,
  volume: _volume,
  ...roomAudioRendererProps
}: AgentSessionProviderProps) {
  return (
    <SessionProvider session={session}>
      {children}
      {/* HTMLMediaElement.volume only accepts [0, 1] — always use 1 */}
      <RoomAudioRenderer {...roomAudioRendererProps} volume={1} />
    </SessionProvider>
  );
}
