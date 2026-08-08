import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-background px-6"
    >
      {/* Background decoration */}
      <div className="pointer-events-none absolute -left-32 -top-32 size-96 rounded-full bg-teal-500/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 size-96 rounded-full bg-cyan-500/10 blur-3xl" />

      <div className="relative z-10 flex w-full max-w-lg flex-col items-center text-center">
        {/* Logo */}
        <div className="mb-7 flex size-24 items-center justify-center rounded-full border border-teal-400/30 bg-teal-500/10 shadow-lg shadow-teal-500/10">
          <span className="text-5xl">🩺</span>
        </div>

        {/* Brand */}
        <p className="text-4xl font-bold tracking-tight md:text-5xl">
          Medi<span className="text-teal-400">Sathi</span>
        </p>

        <p className="mt-3 text-lg font-medium text-muted-foreground">
          AI Healthcare Voice Assistant
        </p>

        <p className="mt-5 max-w-md text-sm leading-6 text-muted-foreground md:text-base">
          Your friendly voice companion for everyday health questions.
          Just speak naturally and MediSathi will listen and respond.
        </p>

        {/* Feature badges */}
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <span className="rounded-full border px-3 py-1.5 text-xs">
            🎙️ Voice First
          </span>

          <span className="rounded-full border px-3 py-1.5 text-xs">
            ⚡ Fast Response
          </span>

          <span className="rounded-full border px-3 py-1.5 text-xs">
            🇮🇳 Built for India
          </span>
        </div>

        {/* Start button */}
        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 h-14 w-full max-w-sm rounded-full bg-teal-500 text-sm font-bold tracking-wider text-white shadow-lg shadow-teal-500/20 transition-all hover:bg-teal-600 hover:shadow-teal-500/30"
        >
          🎙️ {startButtonText}
        </Button>

        <p className="mt-4 text-xs text-muted-foreground">
          Powered by <span className="font-semibold">Murf Falcon</span> +
          LiveKit
        </p>

        <p className="mt-8 max-w-sm text-xs leading-5 text-muted-foreground">
          MediSathi provides general health information and does not replace
          professional medical advice.
        </p>
      </div>
    </div>
  );
};