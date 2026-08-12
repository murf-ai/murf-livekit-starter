import { Button } from '@/components/ui/button';
import { ShieldCheck, PhoneCall, RefreshCw, AlertTriangle } from 'lucide-react';
import { motion } from 'motion/react';

export type WelcomeViewState = 'READY' | 'CONNECTING' | 'CALL_ENDED' | 'MIC_ERROR';

interface WelcomeViewProps {
  state: WelcomeViewState;
  errorMessage?: string | null;
  startButtonText: string;
  onStartCall: () => void;
  onStartAgain?: () => void;
  onTryAgain?: () => void;
}

export const WelcomeView = ({
  state,
  errorMessage,
  startButtonText,
  onStartCall,
  onStartAgain,
  onTryAgain,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div
      ref={ref}
      className="relative min-h-screen w-full bg-[#0F1B2D] text-[#EDEDE6] flex flex-col justify-between items-center p-6 select-none font-sans overflow-hidden"
    >
      {/* 2. Background Atmosphere: Slow Ambient Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 size-[500px] rounded-full bg-radial from-[#2F9E7C]/10 via-[#1C2B40]/20 to-transparent blur-3xl animate-pulse transition-all duration-1000" />

      {/* 3. Staggered Entrance: Header */}
      <motion.header
        initial={{ opacity: 0, y: -15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="z-10 w-full max-w-4xl flex items-center justify-between py-4 px-6 rounded-2xl bg-[#1C2B40]/60 backdrop-blur-md border border-white/10 shadow-lg shadow-[#2F9E7C]/5"
      >
        <div className="flex items-center space-x-3">
          <div className="size-9 rounded-xl bg-[#0F1B2D]/80 border border-[#2F9E7C]/30 flex items-center justify-center text-[#2F9E7C] shadow-inner">
            <ShieldCheck className="size-5" />
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-wide text-[#EDEDE6]">FinSafe Assistant</h1>
            <p className="text-xs text-[#8A97A8]">Private Banking & Financial Guidance</p>
          </div>
        </div>
        <div className="flex items-center space-x-2 bg-[#0F1B2D]/60 px-3 py-1.5 rounded-full border border-white/5">
          <span className="inline-block size-2 rounded-full bg-[#2F9E7C] animate-pulse"></span>
          <span className="text-xs font-mono text-[#8A97A8] tracking-wider uppercase">Encrypted 256-Bit</span>
        </div>
      </motion.header>

      {/* Main Container */}
      <main className="z-10 w-full max-w-xl flex flex-col items-center justify-center text-center my-auto py-10 px-4">
        {/* ARIA Live Region for Screen Readers */}
        <div className="sr-only" aria-live="polite" aria-atomic="true">
          {state === 'READY' && 'FinSafe Assistant is ready to call.'}
          {state === 'CONNECTING' && 'Connecting you now to FinSafe Assistant...'}
          {state === 'CALL_ENDED' && 'Call ended safely. Select start again to restart.'}
          {state === 'MIC_ERROR' && `Microphone error: ${errorMessage || 'Access blocked'}`}
        </div>

        {/* State 1: READY */}
        {state === 'READY' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.15, ease: 'easeOut' }}
            className="flex flex-col items-center"
          >
            {/* 4. Signature Multi-Layered Pulse Rings */}
            <div className="relative mb-10 flex items-center justify-center">
              <div className="absolute size-44 rounded-full border border-[#2F9E7C]/15 animate-ping opacity-25 motion-reduce:animate-none" />
              <div className="absolute size-36 rounded-full border border-[#2F9E7C]/30 animate-pulse opacity-50 motion-reduce:animate-none" />
              <div className="size-24 rounded-full bg-[#1C2B40]/90 backdrop-blur-md border border-[#2F9E7C]/50 flex items-center justify-center shadow-xl shadow-[#2F9E7C]/15 transition-transform hover:scale-105">
                <PhoneCall className="size-10 text-[#2F9E7C]" />
              </div>
            </div>

            <h2 className="text-2xl font-bold text-[#EDEDE6] tracking-tight mb-3">
              Talk to FinSafe Assistant
            </h2>
            <p className="text-sm text-[#8A97A8] max-w-md mb-8 leading-relaxed">
              Verify government schemes, check eligibility guidelines, or discuss financial questions safely with your AI voice advisor.
            </p>

            <Button
              size="lg"
              onClick={onStartCall}
              className="bg-[#2F9E7C] hover:bg-[#2F9E7C]/90 text-[#0F1B2D] font-semibold text-sm px-8 py-6 rounded-full shadow-lg shadow-[#2F9E7C]/20 transition-all cursor-pointer hover:scale-105 active:scale-95 focus:ring-2 focus:ring-[#2F9E7C] focus:ring-offset-2 focus:ring-offset-[#0F1B2D]"
            >
              {startButtonText || 'Start Call with FinSafe'}
            </Button>
          </motion.div>
        )}

        {/* State 2: CONNECTING */}
        {state === 'CONNECTING' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center"
          >
            <div className="relative mb-8 flex items-center justify-center">
              <div className="size-28 rounded-full border-2 border-[#2F9E7C]/20 border-t-[#2F9E7C] animate-spin" />
              <div className="absolute size-20 rounded-full bg-[#1C2B40]/80 backdrop-blur-md flex items-center justify-center">
                <ShieldCheck className="size-8 text-[#2F9E7C] animate-pulse" />
              </div>
            </div>

            <h2 className="text-xl font-semibold text-[#EDEDE6] mb-2">Connecting you now...</h2>
            <p className="text-xs text-[#8A97A8] font-mono tracking-wide">Establishing secure voice audio session</p>
          </motion.div>
        )}

        {/* State 5: CALL ENDED */}
        {state === 'CALL_ENDED' && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center"
          >
            <div className="size-20 rounded-full bg-[#1C2B40]/90 backdrop-blur-md border border-white/10 flex items-center justify-center mb-6 shadow-md">
              <PhoneCall className="size-8 text-[#8A97A8]" />
            </div>

            <h2 className="text-2xl font-bold text-[#EDEDE6] mb-2">Call Ended Safely</h2>
            <p className="text-sm text-[#8A97A8] max-w-sm mb-8 leading-relaxed">
              Your voice session with FinSafe Assistant has closed. No sensitive credentials were saved.
            </p>

            <Button
              size="lg"
              onClick={onStartAgain || onStartCall}
              className="bg-[#1C2B40]/90 hover:bg-[#1C2B40] border border-[#2F9E7C]/40 text-[#2F9E7C] font-semibold text-sm px-8 py-6 rounded-full transition-all cursor-pointer hover:scale-105 active:scale-95 flex items-center space-x-2"
            >
              <RefreshCw className="size-4 mr-2" />
              Start New Call
            </Button>
          </motion.div>
        )}

        {/* State: MIC ERROR (Amber Alert) */}
        {state === 'MIC_ERROR' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-full bg-[#1C2B40]/90 backdrop-blur-md border border-[#C98A3B]/40 rounded-2xl p-6 text-left shadow-xl shadow-[#C98A3B]/5"
          >
            <div className="flex items-start space-x-4 mb-4">
              <div className="size-10 rounded-xl bg-[#C98A3B]/15 border border-[#C98A3B]/40 flex items-center justify-center text-[#C98A3B] shrink-0">
                <AlertTriangle className="size-5" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-[#EDEDE6]">Microphone Access Blocked</h3>
                <p className="text-xs text-[#8A97A8] mt-1">
                  FinSafe Assistant requires microphone access to hear your questions.
                </p>
              </div>
            </div>

            <div className="bg-[#0F1B2D]/80 rounded-xl p-4 mb-6 border border-white/5">
              <p className="text-xs font-semibold text-[#C98A3B] uppercase tracking-wider mb-2">How to fix in your browser:</p>
              <ol className="text-xs text-[#8A97A8] space-y-1.5 list-decimal list-inside">
                <li>Click the <span className="text-[#EDEDE6] font-medium">lock icon</span> next to the URL address bar.</li>
                <li>Toggle <span className="text-[#EDEDE6] font-medium">Microphone</span> permission to <span className="text-[#2F9E7C] font-medium">Allow</span>.</li>
                <li>Click the button below to try connecting again.</li>
              </ol>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={onTryAgain || onStartCall}
                className="bg-[#C98A3B] hover:bg-[#C98A3B]/90 text-[#0F1B2D] font-semibold text-xs px-6 py-2.5 rounded-lg transition-all hover:scale-105 active:scale-95"
              >
                Try Again
              </Button>
            </div>
          </motion.div>
        )}
      </main>

      {/* 3. Staggered Entrance: Footer */}
      <motion.footer
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease: 'easeOut' }}
        className="z-10 w-full max-w-4xl pt-4 border-t border-white/10 flex flex-col md:flex-row items-center justify-between text-xs text-[#8A97A8]"
      >
        <p>© FinSafe Assistant • Institutional Security & Privacy Protection</p>
        <p className="mt-2 md:mt-0 font-mono text-[11px]">Ref ID: <span className="text-[#EDEDE6] tabular-nums">FIN-2026-V8</span></p>
      </motion.footer>
    </div>
  );
};

