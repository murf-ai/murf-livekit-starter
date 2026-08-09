'use client';

import { useMemo } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
import { AudioVolumeBooster } from '@/components/app/audio-volume-booster';
import { ViewController } from '@/components/app/view-controller';
import { Toaster } from '@/components/ui/sonner';
import { useAgentErrors } from '@/hooks/useAgentErrors';
import { useDebugMode } from '@/hooks/useDebug';
import { getSandboxTokenSource } from '@/lib/utils';

const IN_DEVELOPMENT = process.env.NODE_ENV !== 'production';

function AppSetup() {
  useDebugMode({ enabled: IN_DEVELOPMENT });
  useAgentErrors();

  return null;
}

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  // Always mint a FRESH room token on every start().
  // TokenSource.endpoint caches the JWT until expiry, so "Start again" after END CALL
  // would rejoin the old empty room and the agent never re-dispatches.
  const tokenSource = useMemo(() => {
    if (typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string') {
      return getSandboxTokenSource(appConfig);
    }

    return TokenSource.literal(async () => {
      const roomConfig = appConfig.agentName
        ? { agents: [{ agent_name: appConfig.agentName }] }
        : undefined;

      const res = await fetch('/api/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(roomConfig ? { room_config: roomConfig } : {}),
      });

      if (!res.ok) {
        throw new Error((await res.text()) || 'Failed to fetch connection details');
      }

      return res.json();
    });
  }, [appConfig]);

  const session = useSession(tokenSource, {
    // Local agent process spin-up can take a few seconds after a previous job exits.
    agentConnectTimeoutMilliseconds: 45_000,
  });

  return (
    <AgentSessionProvider session={session} volume={1}>
      <AppSetup />
      <AudioVolumeBooster />
      <main className="grid h-svh grid-cols-1 place-content-center">
        <ViewController appConfig={appConfig} />
      </main>
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{
          warning: <WarningIcon weight="bold" />,
        }}
        position="top-center"
        className="toaster group"
        style={
          {
            '--normal-bg': 'var(--popover)',
            '--normal-text': 'var(--popover-foreground)',
            '--normal-border': 'var(--border)',
          } as React.CSSProperties
        }
      />
    </AgentSessionProvider>
  );
}
