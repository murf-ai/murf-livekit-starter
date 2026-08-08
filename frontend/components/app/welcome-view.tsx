import { ArrowRightIcon, HeadphonesIcon, MicIcon, ShoppingBagIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

function MitraMark() {
  return (
    <div className="relative grid size-24 place-items-center rounded-[2rem] bg-orange-600 text-white shadow-[0_20px_50px_-20px_rgba(194,65,12,0.65)]">
      <ShoppingBagIcon className="size-11" strokeWidth={1.8} />
      <span className="absolute -right-2 -bottom-2 grid size-9 place-items-center rounded-full border-4 border-orange-50 bg-emerald-700">
        <MicIcon className="size-4" />
      </span>
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
    <div ref={ref} className="w-full px-5 py-10">
      <section className="mx-auto flex max-w-5xl flex-col items-center gap-10 lg:flex-row lg:justify-between">
        <div className="max-w-2xl text-center lg:text-left">
          <div className="mb-7 flex justify-center lg:justify-start">
            <MitraMark />
          </div>
          <p className="mb-3 font-mono text-xs font-bold tracking-[0.2em] text-orange-700 uppercase">
            Your local shopping companion
          </p>
          <h1 className="text-4xl leading-[1.05] font-bold tracking-tight text-stone-900 sm:text-6xl dark:text-orange-50">
            Meet Mitra. Shop local, simply by speaking.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-stone-600 sm:text-lg lg:mx-0 dark:text-stone-300">
            स्थानीय products खोजें, listed prices पूछें, और pickup या delivery order request
            तैयार करें। हिंदी, English, या दोनों में बात करें।
          </p>
        </div>

        <div className="w-full max-w-sm rounded-[2rem] border border-orange-200/70 bg-white/80 p-6 shadow-xl shadow-orange-900/5 backdrop-blur dark:border-orange-900 dark:bg-stone-900/80">
          <div className="mb-6 flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-full bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
              <HeadphonesIcon className="size-5" />
            </span>
            <div>
              <p className="font-semibold text-stone-900 dark:text-stone-100">Mitra is ready</p>
              <p className="text-sm text-stone-500 dark:text-stone-400">मित्र तैयार है</p>
            </div>
          </div>

          <Button
            size="lg"
            onClick={onStartCall}
            className="h-14 w-full rounded-2xl bg-orange-600 text-base font-bold text-white shadow-lg shadow-orange-600/20 hover:bg-orange-700"
          >
            {startButtonText}
            <ArrowRightIcon className="size-5" />
          </Button>
          <p className="mt-4 text-center text-xs leading-5 text-stone-500 dark:text-stone-400">
            We’ll ask for microphone access. Mitra never asks for your OTP or PIN.
          </p>
        </div>
      </section>
    </div>
  );
};
