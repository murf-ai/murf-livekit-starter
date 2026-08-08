import { AlertTriangle, Mic, PhoneCall, RotateCcw, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';

type WelcomeState = 'ready' | 'connecting' | 'ended';

const welcomeCopy = {
  ready: {
    label: 'Ready',
    title: 'Telugu UPI fraud help, by voice',
    body: 'Suraksha Saathi helps you check suspicious collect requests, OTP calls, and payment pressure before you act.',
    button: null,
  },
  connecting: {
    label: 'Connecting',
    title: 'Joining your safe call',
    body: 'Please wait while Suraksha Saathi connects to the Telugu voice agent.',
    button: null,
  },
  ended: {
    label: 'Call ended',
    title: 'Conversation ended',
    body: 'Start again if you want to check another UPI request, QR code, or fraud call.',
    button: 'Start again',
  },
};

interface WelcomeViewProps {
  startButtonText: string;
  state?: WelcomeState;
  microphoneError?: string | null;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  state = 'ready',
  microphoneError,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  const copy = welcomeCopy[state];
  const buttonText = copy.button ?? startButtonText;
  const isConnecting = state === 'connecting';

  return (
    <div ref={ref} data-day3-state={copy.label}>
      <section className="bg-background text-foreground min-h-svh px-5 py-8 md:px-10">
        <div className="mx-auto grid min-h-[calc(100svh-4rem)] w-full max-w-5xl content-center gap-8 lg:grid-cols-[1fr_360px] lg:items-center">
          <div className="max-w-2xl">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-teal-700/20 bg-teal-600/10 px-3 py-1 text-sm font-medium text-teal-800 dark:text-teal-200">
              <ShieldCheck className="size-4" />
              <span>{copy.label}</span>
            </div>

            <h1 className="text-4xl leading-tight font-semibold tracking-normal text-pretty md:text-6xl">
              {copy.title}
            </h1>

            <p className="text-muted-foreground mt-5 max-w-xl text-base leading-7 md:text-lg">
              {copy.body}
            </p>

            <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button
                size="lg"
                onClick={onStartCall}
                disabled={isConnecting}
                className="h-12 w-full rounded-md bg-teal-700 px-6 text-sm font-semibold text-white hover:bg-teal-800 sm:w-auto"
              >
                {state === 'ended' ? (
                  <RotateCcw className="mr-2 size-4" />
                ) : (
                  <PhoneCall className="mr-2 size-4" />
                )}
                {isConnecting ? 'Connecting...' : buttonText}
              </Button>

              <p className="text-muted-foreground text-sm leading-6">
                Keep OTP, UPI PIN, CVV, and passwords private.
              </p>
            </div>

            {microphoneError && (
              <div className="mt-5 flex max-w-xl gap-3 rounded-md border border-amber-500/40 bg-amber-50 p-3 text-sm leading-6 text-amber-950 dark:bg-amber-950/30 dark:text-amber-100">
                <AlertTriangle className="mt-0.5 size-4 shrink-0" />
                <p>{microphoneError}</p>
              </div>
            )}
          </div>

          <div className="rounded-lg border border-teal-800/15 bg-teal-950 p-5 text-white shadow-xl shadow-teal-950/10">
            <div className="flex items-center gap-3 border-b border-white/10 pb-4">
              <div className="grid size-11 place-items-center rounded-md bg-teal-400 text-teal-950">
                <Mic className="size-5" />
              </div>
              <div>
                <p className="text-sm font-semibold">Suraksha Saathi</p>
                <p className="text-xs text-teal-100">Telugu financial safety line</p>
              </div>
            </div>

            <div className="mt-5 space-y-4 text-sm leading-6 text-teal-50">
              <div className="flex gap-3">
                <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-300" />
                <p>
                  Unknown collect request vachinda? First reject or confirm from a known source.
                </p>
              </div>
              <div className="flex gap-3">
                <ShieldCheck className="mt-0.5 size-4 shrink-0 text-teal-300" />
                <p>
                  Money lost? Stop sharing, call your bank, then report to 1930 or
                  cybercrime.gov.in.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
