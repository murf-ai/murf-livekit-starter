'use client';

import { useMemo, useState, useEffect } from 'react';
import { TokenSource } from 'livekit-client';
import { useSession } from '@livekit/components-react';
import { WarningIcon } from '@phosphor-icons/react/dist/ssr';
import type { AppConfig } from '@/app-config';
import { AgentSessionProvider } from '@/components/agents-ui/agent-session-provider';
import { StartAudioButton } from '@/components/agents-ui/start-audio-button';
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

// --- NEW: Custom Microphone Error Screen ---
function MicPermissionBanner() {
  const [micState, setMicState] = useState<string>('prompt');

  useEffect(() => {
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: 'microphone' as PermissionName }).then((status) => {
        setMicState(status.state);
        status.onchange = () => setMicState(status.state);
      });
    }
  }, []);

  // If they haven't denied it, don't show the error
  if (micState !== 'denied') return null;

  return (
    <div className="absolute inset-0 z-[100] bg-black/90 flex flex-col items-center justify-center text-center p-6 backdrop-blur-md">
      <div className="bg-red-950/80 border-2 border-red-500 rounded-3xl p-8 max-w-md shadow-[0_0_50px_rgba(239,68,68,0.3)]">
        <svg className="w-16 h-16 text-red-500 mx-auto mb-4 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
        <h2 className="text-2xl font-bold text-white mb-3">Microphone Blocked</h2>
        <p className="text-red-200 mb-6 leading-relaxed">
          Raksha requires microphone access to hear your emergency. <br/><br/>
          Please click the <b>lock icon (🔒)</b> in your browser's address bar, change Microphone to <b>"Allow"</b>, and refresh this page.
        </p>
        <button onClick={() => window.location.reload()} className="bg-red-600 hover:bg-red-500 text-white font-bold py-3 px-6 rounded-full w-full transition-colors shadow-lg">
          I have allowed it, Reload Page
        </button>
      </div>
    </div>
  );
}
// ------------------------------------------

interface AppProps {
  appConfig: AppConfig;
}

export function App({ appConfig }: AppProps) {
  const tokenSource = useMemo(() => {
    return typeof process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT === 'string'
      ? getSandboxTokenSource(appConfig)
      : TokenSource.endpoint('/api/token');
  }, [appConfig]);

  const session = useSession(
    tokenSource,
    appConfig.agentName ? { agentName: appConfig.agentName } : undefined
  );

  return (
    <AgentSessionProvider session={session}>
      <AppSetup />
      
      {/* --- FOOLPROOF BACKGROUND LAYER --- */}
      <div 
        className="fixed inset-0 z-[-10]" 
        style={{
          backgroundImage: "linear-gradient(rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.85)), url('/background.jpg')",
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundColor: '#050505' 
        }} 
      />
      {/* ---------------------------------- */}
      
      <main className="grid h-svh grid-cols-1 place-content-center relative">
        
        {/* The new Mic Guard component */}
        <MicPermissionBanner />
        
        <ViewController appConfig={appConfig} />

        {/* CUSTOM EMERGENCY BUTTON */}
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-50">
          <a 
            href="tel:112"
            className="flex items-center gap-2 px-6 py-2 rounded-full border border-orange-900/80 text-orange-400 hover:bg-orange-500/10 transition-colors text-sm font-medium shadow-lg bg-black/50 backdrop-blur-sm"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            Emergency contact (आपातकालीन संपर्क)
          </a>
        </div>
        
      </main>
      
      <StartAudioButton label="Start Audio" />
      <Toaster
        icons={{ warning: <WarningIcon weight="bold" /> }}
        position="top-center"
        className="toaster group"
        style={{
          '--normal-bg': 'var(--popover)',
          '--normal-text': 'var(--popover-foreground)',
          '--normal-border': 'var(--border)',
        } as React.CSSProperties}
      />
    </AgentSessionProvider>
  );
}