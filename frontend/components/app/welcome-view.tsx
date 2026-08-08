'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { useMicPermission } from '@/hooks/useMicPermission';

// Wheat / crop SVG icon symbolising farming
function KrishiIcon() {
  return (
    <svg
      width="72"
      height="72"
      viewBox="0 0 72 72"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="mb-4"
    >
      {/* Sun */}
      <circle cx="36" cy="20" r="8" fill="currentColor" opacity="0.9" />
      <line x1="36" y1="6" x2="36" y2="2" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="36" y1="38" x2="36" y2="34" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="22" y1="20" x2="18" y2="20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="54" y1="20" x2="50" y2="20" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="26.1" y1="10.1" x2="23.3" y2="7.3" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="48.7" y1="32.7" x2="45.9" y2="29.9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="45.9" y1="10.1" x2="48.7" y2="7.3" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      <line x1="23.3" y1="32.7" x2="26.1" y2="29.9" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      {/* Wheat stalk */}
      <line x1="36" y1="36" x2="36" y2="68" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      {/* Wheat grains left */}
      <ellipse cx="30" cy="42" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 30 42)" />
      <ellipse cx="27" cy="51" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 27 51)" />
      <ellipse cx="26" cy="60" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(-30 26 60)" />
      {/* Wheat grains right */}
      <ellipse cx="42" cy="42" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 42 42)" />
      <ellipse cx="45" cy="51" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 45 51)" />
      <ellipse cx="46" cy="60" rx="5" ry="3" fill="currentColor" opacity="0.8" transform="rotate(30 46 60)" />
    </svg>
  );
}

// Spinning loader for the connecting state
function ConnectingSpinner() {
  return (
    <svg
      className="mb-4 animate-spin"
      width="48"
      height="48"
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Connecting..."
    >
      <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" strokeOpacity="0.2" />
      <path
        d="M44 24A20 20 0 0 0 24 4"
        stroke="currentColor"
        strokeWidth="4"
        strokeLinecap="round"
      />
    </svg>
  );
}

// Microphone blocked icon
function MicBlockedIcon() {
  return (
    <svg
      width="48"
      height="48"
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="mb-3 text-red-500"
    >
      <rect x="16" y="6" width="16" height="24" rx="8" fill="currentColor" opacity="0.15" stroke="currentColor" strokeWidth="2" />
      <line x1="8" y1="8" x2="40" y2="40" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      <path d="M10 24a14 14 0 0 0 28 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.4" />
      <line x1="24" y1="38" x2="24" y2="44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeOpacity="0.4" />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const { permissionState, requestMicPermission } = useMicPermission();
  const [isConnecting, setIsConnecting] = useState(false);
  const [micError, setMicError] = useState(false);

  const handleStart = async () => {
    // If permission is explicitly denied, show the error panel
    if (permissionState === 'denied') {
      setMicError(true);
      return;
    }

    // For 'prompt' or 'unknown', ask first so we can catch the denial early
    if (permissionState === 'prompt' || permissionState === 'unknown') {
      const granted = await requestMicPermission();
      if (!granted) {
        setMicError(true);
        return;
      }
    }

    setIsConnecting(true);
    onStartCall();
  };

  // ── Mic permission denied panel ─────────────────────────────────────────────
  if (micError || permissionState === 'denied') {
    return (
      <div ref={ref} className="flex flex-col items-center justify-center text-center px-6 max-w-sm mx-auto">
        <MicBlockedIcon />
        <h2 className="text-foreground text-lg font-bold mb-2">Microphone Access Blocked</h2>
        <p className="text-muted-foreground text-sm mb-1 leading-relaxed">
          <span className="font-semibold text-foreground">माइक की अनुमति नहीं मिली।</span>
        </p>
        <p className="text-muted-foreground text-sm mb-5 leading-relaxed">
          KrishiMitra AI को आपसे बात करने के लिए माइक्रोफोन की जरूरत है।
          Please enable microphone access in your browser settings and refresh this page.
        </p>
        <div className="rounded-lg border border-border bg-muted/50 p-4 text-left text-xs text-muted-foreground w-full mb-4 space-y-1">
          <p className="font-semibold text-foreground mb-1">How to enable:</p>
          <p>🔒 <strong>Chrome/Edge:</strong> Click the lock icon in the address bar → Microphone → Allow</p>
          <p>🦊 <strong>Firefox:</strong> Click the shield icon → Permissions → Allow Microphone</p>
          <p>🍎 <strong>Safari:</strong> Safari menu → Settings for This Website → Microphone → Allow</p>
        </div>
        <Button
          size="lg"
          variant="outline"
          onClick={() => {
            setMicError(false);
            window.location.reload();
          }}
          className="rounded-full font-mono text-xs font-bold tracking-wider uppercase"
        >
          Refresh Page / पेज रिफ्रेश करें
        </Button>
      </div>
    );
  }

  // ── Connecting state ──────────────────────────────────────────────────────────
  if (isConnecting) {
    return (
      <div ref={ref} className="flex flex-col items-center justify-center text-center px-6">
        <div className="text-[var(--krishi-accent)]">
          <ConnectingSpinner />
        </div>
        <p className="text-foreground text-base font-semibold">Connecting...</p>
        <p className="text-muted-foreground text-sm mt-1">
          KrishiMitra AI se judh rahe hain, thodi der ruko…
        </p>
      </div>
    );
  }

  // ── Default welcome panel ──────────────────────────────────────────────────
  return (
    <div ref={ref} className="flex flex-col items-center justify-center text-center px-4">
      {/* Brand icon */}
      <div className="text-[var(--krishi-accent)] drop-shadow-sm">
        <KrishiIcon />
      </div>

      {/* Brand name */}
      <h1 className="text-foreground text-2xl font-bold tracking-tight mb-1">
        KrishiMitra AI
      </h1>

      {/* Tagline — bilingual */}
      <p className="text-muted-foreground text-sm mb-1 font-medium">
        आपका डिजिटल कृषि सहायक
      </p>
      <p className="text-muted-foreground text-xs mb-5 max-w-xs leading-relaxed">
        Crops · Irrigation · Soil · Govt. Schemes · Organic Farming
      </p>

      {/* Feature chips */}
      <div className="flex flex-wrap justify-center gap-2 mb-6 max-w-xs">
        {['🌾 Fasal Salah', '💧 Sinchai', '🌱 Mitti', '📋 Yojana', '🌿 Organic'].map((chip) => (
          <span
            key={chip}
            className="rounded-full border border-[var(--krishi-accent)]/30 bg-[var(--krishi-accent)]/10 px-3 py-0.5 text-xs font-medium text-[var(--krishi-accent)]"
          >
            {chip}
          </span>
        ))}
      </div>

      {/* CTA button */}
      <Button
        size="lg"
        onClick={handleStart}
        className="w-64 rounded-full font-mono text-xs font-bold tracking-wider uppercase bg-[var(--krishi-accent)] text-white hover:bg-[var(--krishi-accent)]/90 active:scale-95 transition-transform"
      >
        {startButtonText}
      </Button>

      <p className="text-muted-foreground text-xs mt-4 max-w-xs leading-relaxed">
        Hindi, English, ya mixed language — sab chalta hai 🙏
      </p>

      {/* Powered-by footer */}
      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center gap-1">
        <p className="text-muted-foreground text-xs leading-5">
          Powered by{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://murf.ai/api"
            className="underline underline-offset-2"
          >
            Murf Falcon TTS
          </a>
          {' '}·{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://livekit.io"
            className="underline underline-offset-2"
          >
            LiveKit
          </a>
        </p>
      </div>
    </div>
  );
};
