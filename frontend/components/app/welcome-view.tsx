'use client';

import { AlertTriangle, Info, Languages, MicOff, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  micPermissionBlocked?: boolean;
  onRequestMicPermission?: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  micPermissionBlocked = false,
  onRequestMicPermission,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="mx-auto flex min-h-svh w-full max-w-4xl flex-col items-center justify-center px-4 py-8"
    >
      {/* Dhan Rakshak Brand & Avatar */}
      <section className="mb-8 flex flex-col items-center text-center">
        <div className="group relative mb-6">
          <div className="absolute -inset-1.5 animate-pulse rounded-full bg-gradient-to-r from-blue-600 to-amber-500 opacity-75 blur transition duration-1000 group-hover:opacity-100 group-hover:duration-200"></div>
          <img
            src="/avatar.png"
            alt="Dhan Rakshak Guardian Avatar"
            className="border-background relative size-32 rounded-full border-4 object-cover shadow-2xl transition-transform duration-500 group-hover:scale-105"
          />
          <div className="border-background absolute right-0 bottom-0 rounded-full border-2 bg-blue-600 p-2 text-white shadow-lg">
            <ShieldCheck className="size-5" />
          </div>
        </div>

        <h1 className="mb-2 bg-gradient-to-r from-blue-600 via-indigo-500 to-amber-500 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent md:text-5xl">
          धन रक्षक (Dhan Rakshak)
        </h1>
        <p className="text-muted-foreground max-w-lg text-lg font-medium">
          Your AI Financial Services Voice Assistant for Secure &amp; Smart Banking
        </p>
      </section>

      {/* Safety & Info Cards */}
      <section className="mb-8 grid w-full max-w-3xl grid-cols-1 gap-6 md:grid-cols-3">
        <div className="bg-card flex flex-col items-start rounded-2xl border p-5 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-4 rounded-xl bg-blue-500/10 p-3 text-blue-600 dark:text-blue-400">
            <ShieldCheck className="size-6" />
          </div>
          <h3 className="text-foreground mb-2 font-bold">100% Secure</h3>
          <p className="text-muted-foreground text-xs leading-relaxed">
            Dhan Rakshak will <strong>NEVER</strong> ask for your OTP, ATM PIN, UPI PIN, CVV, or
            full bank account details.
          </p>
        </div>

        <div className="bg-card flex flex-col items-start rounded-2xl border p-5 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-4 rounded-xl bg-amber-500/10 p-3 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="size-6" />
          </div>
          <h3 className="text-foreground mb-2 font-bold">Scam Awareness</h3>
          <p className="text-muted-foreground text-xs leading-relaxed">
            No police, RBI, or government agency will place you under{' '}
            <strong>"digital arrest"</strong> over phone or video calls.
          </p>
        </div>

        <div className="bg-card flex flex-col items-start rounded-2xl border p-5 shadow-sm transition-all duration-300 hover:shadow-md">
          <div className="mb-4 rounded-xl bg-emerald-500/10 p-3 text-emerald-600 dark:text-emerald-400">
            <Languages className="size-6" />
          </div>
          <h3 className="text-foreground mb-2 font-bold">Multi-Lingual</h3>
          <p className="text-muted-foreground text-xs leading-relaxed">
            Dhan Rakshak understands and speaks <strong>Hindi, English, and Hinglish</strong> to
            support everyone.
          </p>
        </div>
      </section>

      {/* Connection & Microphone Permission Error Handling */}
      <section className="flex w-full max-w-md flex-col items-center gap-4">
        {micPermissionBlocked ? (
          <div className="bg-destructive/10 border-destructive/20 flex w-full flex-col items-center rounded-2xl border p-5 text-center">
            <div className="bg-destructive/20 text-destructive mb-3 rounded-full p-3">
              <MicOff className="size-8" />
            </div>
            <h4 className="text-destructive mb-2 font-bold">Microphone Access Blocked</h4>
            <p className="text-muted-foreground mb-4 text-sm">
              Dhan Rakshak requires your microphone to listen to your banking questions.
            </p>
            <div className="bg-background text-muted-foreground mb-4 w-full space-y-2 rounded-xl border p-3 text-left text-xs">
              <p className="text-foreground flex items-center gap-1 font-semibold">
                <Info className="size-3.5 text-blue-500" /> How to enable:
              </p>
              <ol className="list-inside list-decimal space-y-1">
                <li>
                  Click the <strong>Lock 🔒 or Camera/Microphone icon</strong> in your browser's
                  address bar.
                </li>
                <li>
                  Toggle the <strong>Microphone</strong> permission to <strong>Allow</strong>.
                </li>
                <li>Refresh the page to apply changes.</li>
              </ol>
            </div>
            <Button
              onClick={onRequestMicPermission}
              className="bg-destructive hover:bg-destructive/95 w-full rounded-xl font-bold text-white"
            >
              Try Enabling Again
            </Button>
          </div>
        ) : (
          <div className="flex w-full flex-col items-center">
            <Button
              size="lg"
              onClick={onStartCall}
              className="h-12 w-64 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 text-sm font-bold tracking-wider text-white uppercase shadow-xl shadow-blue-500/20 transition-all duration-200 hover:scale-105 active:scale-95"
            >
              {startButtonText}
            </Button>
            <p className="text-muted-foreground mt-4 text-center text-xs">
              Click to start call. Make sure your microphone is enabled.
            </p>
          </div>
        )}
      </section>
    </div>
  );
};
