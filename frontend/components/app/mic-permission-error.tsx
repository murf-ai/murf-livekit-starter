'use client';

import React from 'react';
import { motion } from 'motion/react';
import { MicOff, RefreshCcw, Chrome, Globe, HelpCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface MicPermissionErrorProps {
  onRetry: () => void;
}

export function MicPermissionError({ onRetry }: MicPermissionErrorProps) {
  return (
    <div className="relative flex h-full w-full flex-col items-center justify-center bg-[#030303] px-6 py-8">
      {/* Background Glow */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute top-1/2 left-1/2 h-[350px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-red-950/[0.05] blur-[80px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="relative z-10 flex w-full max-w-md flex-col items-center gap-4 rounded-3xl border border-red-500/20 bg-[#0b0b0b]/90 p-8 shadow-[0_8px_30px_rgba(0,0,0,0.6)] backdrop-blur-md md:p-10 text-center"
      >
        {/* Error icon */}
        <div className="mb-2 flex size-16 items-center justify-center rounded-full border border-red-500/30 bg-red-950/20 text-red-500 shadow-[0_0_20px_rgba(239,68,68,0.15)]">
          <MicOff size={28} strokeWidth={1.5} className="animate-pulse" />
        </div>

        <h2 className="text-xl font-bold tracking-tight text-[#f5f5f5]">
          Microphone Access Required
        </h2>
        <p className="text-xs leading-relaxed text-[#92929a] max-w-xs">
          Pooja needs microphone permission to hear your voice questions. Please allow access to begin.
        </p>

        {/* Step-by-step fix */}
        <div className="w-full bg-[#120a2e]/20 border border-white/[0.04] rounded-2xl p-5 text-left flex flex-col gap-4 mt-2">
          <p className="text-[10px] font-semibold tracking-wider text-[#c4a7ff] uppercase">
            How to enable your microphone:
          </p>

          <div className="flex items-start gap-3">
            <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-purple-500/25 text-[10px] font-bold text-[#c4a7ff]">
              1
            </div>
            <div className="flex flex-col text-xs text-[#92929a] leading-relaxed">
              <span className="text-[#f5f5f5] font-medium flex items-center gap-1">
                <Globe size={12} className="text-[#c4a7ff]" /> Check Address Bar
              </span>
              <span>Click the lock icon (🔒) next to the website URL.</span>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-purple-500/25 text-[10px] font-bold text-[#c4a7ff]">
              2
            </div>
            <div className="flex flex-col text-xs text-[#92929a] leading-relaxed">
              <span className="text-[#f5f5f5] font-medium flex items-center gap-1">
                <Chrome size={12} className="text-[#c4a7ff]" /> Allow Access
              </span>
              <span>Find "Microphone" in the menu and set it to "Allow".</span>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="flex size-5 shrink-0 items-center justify-center rounded-full bg-purple-500/25 text-[10px] font-bold text-[#c4a7ff]">
              3
            </div>
            <div className="flex flex-col text-xs text-[#92929a] leading-relaxed">
              <span className="text-[#f5f5f5] font-medium flex items-center gap-1">
                <RefreshCcw size={12} className="text-[#c4a7ff]" /> Refresh & Retry
              </span>
              <span>Reload the page or click the Try Again button below.</span>
            </div>
          </div>
        </div>

        {/* Retry button */}
        <Button
          id="retry-mic-btn"
          onClick={onRetry}
          className="mt-4 w-full cursor-pointer rounded-full bg-[#6d3fd9] hover:bg-[#8b5cf6] py-6 font-sans text-xs font-semibold tracking-wider text-white shadow-[0_0_20px_rgba(109,63,217,0.3)] transition-all duration-300"
        >
          <RefreshCcw size={14} className="mr-2" />
          <span>TRY AGAIN</span>
        </Button>

        <p className="text-[9px] text-[#92929a]/40 mt-1 select-none">
          🔒 Your audio data is processed securely and is never stored permanently.
        </p>
      </motion.div>
    </div>
  );
}
