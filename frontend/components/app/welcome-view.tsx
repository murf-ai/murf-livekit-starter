import {
  ArrowRightIcon,
  Clock3Icon,
  IndianRupeeIcon,
  MapPinIcon,
  MicIcon,
  NavigationIcon,
  PackageCheckIcon,
  ShoppingBagIcon,
  TruckIcon,
} from 'lucide-react';
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
            Just ask Mitra. We’ll find it nearby.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-stone-600 italic sm:text-lg lg:mx-0 dark:text-stone-300">
            Speak naturally in Hindi, English, or Hinglish.
          </p>
          <div className="mx-auto mt-6 max-w-xl space-y-3 text-left lg:mx-0">
            <p className="rounded-2xl rounded-bl-md bg-stone-200 px-4 py-3 text-sm text-stone-800 sm:text-base dark:bg-stone-800 dark:text-stone-100">
              <span className="font-bold">You:</span> “Mere paas ₹500 ke andar achhe running
              shoes hain?”
            </p>
            <p className="ml-6 rounded-2xl rounded-br-md bg-orange-600 px-4 py-3 text-sm text-white sm:text-base">
              <span className="font-bold">Mitra:</span> “Haan! 3 nearby stores mein options
              mile hain.”
            </p>
          </div>
        </div>

        <div className="w-full max-w-md rounded-[2rem] border border-orange-200/70 bg-white/85 p-5 shadow-xl shadow-orange-900/5 backdrop-blur dark:border-orange-900 dark:bg-stone-900/85">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-lg font-bold text-stone-900 dark:text-stone-100">
                Nearby stores
              </p>
              <p className="text-sm text-stone-500 dark:text-stone-400">
                Local options around you
              </p>
            </div>
            <span className="grid size-10 place-items-center rounded-full bg-orange-100 text-orange-700 dark:bg-orange-950 dark:text-orange-300">
              <NavigationIcon className="size-5" />
            </span>
          </div>

          <div className="relative h-44 overflow-hidden rounded-2xl border border-stone-200 bg-[#f4ead8] dark:border-stone-700 dark:bg-stone-800">
            <div className="absolute inset-x-0 top-[38%] h-5 -rotate-6 bg-white/90 shadow-sm dark:bg-stone-700" />
            <div className="absolute top-0 left-[42%] h-full w-5 rotate-12 bg-white/90 shadow-sm dark:bg-stone-700" />
            <div className="absolute top-5 right-5 rounded-full bg-white/90 px-2 py-1 text-[10px] font-bold text-stone-600 shadow-sm dark:bg-stone-900 dark:text-stone-300">
              Your area
            </div>
            <MapPinIcon className="absolute top-7 left-12 size-8 fill-orange-600 text-orange-700 drop-shadow" />
            <MapPinIcon className="absolute right-14 bottom-7 size-8 fill-emerald-600 text-emerald-700 drop-shadow" />
            <span className="absolute bottom-10 left-[46%] grid size-8 place-items-center rounded-full border-4 border-white bg-blue-600 shadow-md dark:border-stone-900">
              <span className="size-2 rounded-full bg-white" />
            </span>
          </div>

          <div className="my-4 grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl bg-stone-50 p-3 dark:bg-stone-800">
              <p className="font-bold text-stone-900 dark:text-stone-100">Stride Local</p>
              <p className="mt-1 flex items-center gap-1 text-stone-500 dark:text-stone-400">
                <MapPinIcon className="size-3.5" /> 0.8 km
              </p>
            </div>
            <div className="rounded-xl bg-stone-50 p-3 dark:bg-stone-800">
              <p className="font-bold text-stone-900 dark:text-stone-100">City Footwear</p>
              <p className="mt-1 flex items-center gap-1 text-stone-500 dark:text-stone-400">
                <MapPinIcon className="size-3.5" /> 1.4 km
              </p>
            </div>
          </div>

          <div className="mb-5 grid grid-cols-2 gap-x-3 gap-y-2 text-xs font-medium text-stone-700 dark:text-stone-300">
            <span className="flex items-center gap-1.5">
              <IndianRupeeIcon className="size-4 text-orange-600" /> From ₹399
            </span>
            <span className="flex items-center gap-1.5">
              <Clock3Icon className="size-4 text-emerald-600" />
              <span className="text-emerald-700 dark:text-emerald-400">Open now</span>
            </span>
            <span className="flex items-center gap-1.5">
              <TruckIcon className="size-4 text-orange-600" /> Pickup / Delivery
            </span>
            <span className="flex items-center gap-1.5">
              <PackageCheckIcon className="size-4 text-emerald-600" /> 6 options available
            </span>
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
