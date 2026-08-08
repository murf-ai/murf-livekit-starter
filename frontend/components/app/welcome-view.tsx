import { AudioLines, Landmark, Mic, ShieldCheck } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

function WelcomeImage() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-fg0 mb-4 size-16"
    >
      <path
        d="M15 24V40C15 40.7957 14.6839 41.5587 14.1213 42.1213C13.5587 42.6839 12.7956 43 12 43C11.2044 43 10.4413 42.6839 9.87868 42.1213C9.31607 41.5587 9 40.7957 9 40V24C9 23.2044 9.31607 22.4413 9.87868 21.8787C10.4413 21.3161 11.2044 21 12 21C12.7956 21 13.5587 21.3161 14.1213 21.8787C14.6839 22.4413 15 23.2044 15 24ZM22 5C21.2044 5 20.4413 5.31607 19.8787 5.87868C19.3161 6.44129 19 7.20435 19 8V56C19 56.7957 19.3161 57.5587 19.8787 58.1213C20.4413 58.6839 21.2044 59 22 59C22.7956 59 23.5587 58.6839 24.1213 58.1213C24.6839 57.5587 25 56.7957 25 56V8C25 7.20435 24.6839 6.44129 24.1213 5.87868C23.5587 5.31607 22.7956 5 22 5ZM32 13C31.2044 13 30.4413 13.3161 29.8787 13.8787C29.3161 14.4413 29 15.2044 29 16V48C29 48.7957 29.3161 49.5587 29.8787 50.1213C30.4413 50.6839 31.2044 51 32 51C32.7956 51 33.5587 50.6839 34.1213 50.1213C34.6839 49.5587 35 48.7957 35 48V16C35 15.2044 34.6839 14.4413 34.1213 13.8787C33.5587 13.3161 32.7956 13 32 13ZM42 21C41.2043 21 40.4413 21.3161 39.8787 21.8787C39.3161 22.4413 39 23.2044 39 24V40C39 40.7957 39.3161 41.5587 39.8787 42.1213C40.4413 42.6839 41.2043 43 42 43C42.7957 43 43.5587 42.6839 44.1213 42.1213C44.6839 41.5587 45 40.7957 45 40V24C45 23.2044 44.6839 22.4413 44.1213 21.8787C43.5587 21.3161 42.7957 21 42 21ZM52 17C51.2043 17 50.4413 17.3161 49.8787 17.8787C49.3161 18.4413 49 19.2044 49 20V44C49 44.7957 49.3161 45.5587 49.8787 46.1213C50.4413 46.6839 51.2043 47 52 47C52.7957 47 53.5587 46.6839 54.1213 46.1213C54.6839 45.5587 55 44.7957 55 44V20C55 19.2044 54.6839 18.4413 54.1213 17.8787C53.5587 17.3161 52.7957 17 52 17Z"
        fill="currentColor"
      />
    </svg>
  );
}

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
  statusLabel: string;
  statusDescription: string;
  permissionError?: string | null;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  statusLabel,
  statusDescription,
  permissionError,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="w-full px-4">
      <section className="mx-auto flex max-w-3xl flex-col items-center justify-center text-center">
        <div className="bg-background/95 border-border/70 w-full rounded-[28px] border border-slate-300/80 p-8 shadow-[0_20px_60px_-28px_rgba(15,23,42,0.35)] backdrop-blur md:p-10">
          <div className="mb-5 flex items-center justify-center gap-2 text-[11px] font-semibold tracking-[0.32em] text-slate-600 uppercase">
            <Landmark className="size-4" />
            <span>Financial Support Desk</span>
          </div>

          <div className="mb-6 flex justify-center">
            <div className="bg-slate-100 text-slate-800 flex size-16 items-center justify-center rounded-2xl border border-slate-300">
              <WelcomeImage />
            </div>
          </div>

          <div className="mb-5 rounded-2xl border border-slate-300/80 bg-slate-50/90 p-4 text-left shadow-sm dark:border-slate-700 dark:bg-slate-900/70">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
              <AudioLines className="size-4" />
              <span>{statusLabel}</span>
            </div>
            <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{statusDescription}</p>
          </div>

          <p className="mx-auto max-w-2xl text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white">
            Access secure financial support through a guided voice service.
          </p>

          <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-slate-600 dark:text-slate-300">
            This service provides clear, official guidance for account questions, service requests, and next-step support in a structured and compliant experience.
          </p>

          <div className="mt-6 flex flex-wrap justify-center gap-3 text-sm text-slate-600 dark:text-slate-300">
            <span className="rounded-full border border-slate-300 bg-white/80 px-3 py-1.5 dark:border-slate-700 dark:bg-slate-950/80">
              Official support guidance
            </span>
            <span className="rounded-full border border-slate-300 bg-white/80 px-3 py-1.5 dark:border-slate-700 dark:bg-slate-950/80">
              Structured account assistance
            </span>
            <span className="rounded-full border border-slate-300 bg-white/80 px-3 py-1.5 dark:border-slate-700 dark:bg-slate-950/80">
              Clear next steps
            </span>
          </div>

          <Button
            size="lg"
            onClick={onStartCall}
            className="mt-8 h-12 rounded-full px-7 text-sm font-semibold tracking-[0.2em] uppercase"
          >
            {startButtonText}
          </Button>

          {permissionError ? (
            <div className="mx-auto mt-6 max-w-2xl rounded-2xl border border-amber-300/70 bg-amber-50 p-4 text-left text-sm text-amber-900 dark:border-amber-700/60 dark:bg-amber-950/70 dark:text-amber-200">
              <div className="mb-2 flex items-center gap-2 font-semibold">
                <Mic className="size-4" />
                <span>Microphone access is required</span>
              </div>
              <p>{permissionError}</p>
              <p className="mt-2">Open your browser site settings and allow microphone access, then refresh and try again so support can assist you through the secure service.</p>
            </div>
          ) : null}
        </div>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center px-4">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Need help getting set up? Check out the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="underline"
          >
            Voice AI quickstart
          </a>
          .
        </p>
      </div>
    </div>
  );
};
