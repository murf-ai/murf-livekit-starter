import { Button } from '@/components/ui/button';
import { Store, ShieldCheck, Speech, Landmark } from 'lucide-react';

function WelcomeGlow() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute -top-[40%] left-[50%] -translate-x-[50%] h-[600px] w-[800px] rounded-full bg-violet-500/10 blur-[120px] dark:bg-violet-500/15" />
      <div className="absolute top-[20%] left-[10%] h-[300px] w-[300px] rounded-full bg-blue-500/5 blur-[80px] dark:bg-blue-500/10" />
      <div className="absolute bottom-[10%] right-[10%] h-[350px] w-[350px] rounded-full bg-indigo-500/5 blur-[90px] dark:bg-indigo-500/10" />
    </div>
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
    <div ref={ref} className="relative w-full max-w-4xl px-6 py-12 mx-auto">
      <WelcomeGlow />
      
      <section className="flex flex-col items-center justify-center text-center">
        {/* Animated Brand badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 text-xs font-semibold text-violet-600 bg-violet-100 rounded-full dark:bg-violet-900/30 dark:text-violet-300 animate-pulse">
          <Store className="size-3.5" />
          <span>Local Voice Commerce AI</span>
        </div>

        {/* Hero Headline */}
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 dark:from-violet-400 dark:via-indigo-300 dark:to-blue-400 bg-clip-text text-transparent pb-3">
          Vyapar AI
        </h1>
        
        <p className="text-lg md:text-xl text-muted-foreground max-w-lg mt-2 font-medium leading-relaxed">
          Discover products, check prices, and shop from nearby merchants instantly using just your voice.
        </p>

        {/* Animated Microphone/Pulsing Call Button Area */}
        <div className="relative mt-10 group">
          <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 opacity-60 blur-md transition duration-1000 group-hover:opacity-100 group-hover:duration-200 animate-tilt" />
          <Button
            size="lg"
            onClick={onStartCall}
            className="relative px-10 py-7 text-sm font-bold tracking-wider uppercase rounded-full bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700 text-white shadow-xl transition-all duration-300 hover:scale-105"
          >
            <Speech className="mr-2 size-5 animate-bounce" />
            {startButtonText}
          </Button>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 text-left">
        <div className="p-6 rounded-2xl border bg-card/50 backdrop-blur-md shadow-xs transition-all duration-300 hover:bg-card/80 hover:shadow-md hover:border-violet-500/30">
          <div className="p-3 w-fit rounded-lg bg-violet-100 text-violet-600 dark:bg-violet-900/20 dark:text-violet-400 mb-4">
            <Store className="size-6" />
          </div>
          <h3 className="font-semibold text-foreground text-base">Local Commerce</h3>
          <p className="text-muted-foreground text-sm mt-2 leading-relaxed">
            Instantly query stocks and find which nearby local stores have your desired products.
          </p>
        </div>

        <div className="p-6 rounded-2xl border bg-card/50 backdrop-blur-md shadow-xs transition-all duration-300 hover:bg-card/80 hover:shadow-md hover:border-violet-500/30">
          <div className="p-3 w-fit rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/20 dark:text-indigo-400 mb-4">
            <Speech className="size-6" />
          </div>
          <h3 className="font-semibold text-foreground text-base">Natural Indian Voices</h3>
          <p className="text-muted-foreground text-sm mt-2 leading-relaxed">
            Interact fluently using warm, context-aware voices optimized for conversational commerce.
          </p>
        </div>

        <div className="p-6 rounded-2xl border bg-card/50 backdrop-blur-md shadow-xs transition-all duration-300 hover:bg-card/80 hover:shadow-md hover:border-violet-500/30">
          <div className="p-3 w-fit rounded-lg bg-blue-100 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 mb-4">
            <ShieldCheck className="size-6" />
          </div>
          <h3 className="font-semibold text-foreground text-base">Safe & Secure</h3>
          <p className="text-muted-foreground text-sm mt-2 leading-relaxed">
            All calls are secured via LiveKit cloud streams to ensure private user sessions.
          </p>
        </div>
      </section>

      {/* Footer Branding */}
      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center px-4">
        <p className="text-muted-foreground text-xs font-medium flex items-center gap-1.5 opacity-80">
          <Landmark className="size-3.5 text-violet-500" />
          <span>Powered by Vyapar AI & Murf Falcon TTS</span>
        </p>
      </div>
    </div>
  );
};
