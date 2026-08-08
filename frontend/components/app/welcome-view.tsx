import { Button } from '@/components/ui/button';

function WelcomeImage() {
  return (
    <svg
      width="64"
      height="64"
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="text-red-500 mb-4 size-16 animate-pulse"
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
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref} className="flex flex-col items-center justify-center min-h-screen px-4">
      {/* Tactical Glassmorphism Card */}
      <section className="bg-black/35 backdrop-blur-md border border-red-500/30 p-8 md:p-12 rounded-3xl shadow-[0_0_40px_rgba(0,0,0,0.8)] flex flex-col items-center justify-center text-center max-w-lg w-full">
        <WelcomeImage />

        <h1 className="text-xl md:text-2xl font-extrabold text-white tracking-wide mb-2">
          Raksha: Disaster Response Triage
        </h1>

        <p className="text-red-200 text-sm md:text-base max-w-prose pt-1 leading-relaxed font-medium mb-8">
          State your emergency, location, and immediate needs. Raksha will guide you in real-time.
        </p>

        {/* Spherical Mic Button */}
        <button
          onClick={onStartCall}
          aria-label={startButtonText}
          className="relative group flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-tr from-red-700 to-red-500 hover:from-red-600 hover:to-red-400 text-white shadow-[0_0_30px_rgba(239,68,68,0.5)] hover:shadow-[0_0_50px_rgba(239,68,68,0.8)] transition-all duration-300 transform hover:scale-105 active:scale-95 border-2 border-red-400/50"
        >
          {/* Outer pulsating ring */}
          <span className="absolute inset-0 rounded-full border border-red-400 animate-ping opacity-30 pointer-events-none"></span>
          
          {/* Microphone Icon */}
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="w-10 h-10 drop-shadow-md" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor" 
            strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </button>
        <span className="mt-3 text-xs font-mono font-semibold tracking-wider text-red-300 uppercase">
          {startButtonText}
        </span>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center">
        <p className="text-gray-400 max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm bg-black/40 px-4 py-1.5 rounded-full backdrop-blur-sm border border-white/10">
          Need help getting set up? Check out the{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://docs.livekit.io/agents/start/voice-ai/"
            className="underline text-red-400 hover:text-red-300"
          >
            Voice AI quickstart
          </a>
          .
        </p>
      </div>
    </div>
  );
};