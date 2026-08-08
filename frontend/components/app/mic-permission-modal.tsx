'use client';

import React from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { MicrophoneSlash, Lock, ArrowClockwise, WarningCircle } from '@phosphor-icons/react';
import { Button } from '@/components/ui/button';

interface MicPermissionModalProps {
  isOpen: boolean;
  onRetry: () => void;
  onClose?: () => void;
}

export function MicPermissionModal({ isOpen, onRetry, onClose }: MicPermissionModalProps) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.9, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 20 }}
          className="relative w-full max-w-md overflow-hidden rounded-3xl border border-rose-500/30 bg-slate-900/95 p-6 shadow-2xl shadow-rose-950/40 text-slate-100"
        >
          <div className="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400">
            <MicrophoneSlash className="size-8 animate-pulse" />
          </div>

          <h3 className="text-xl font-bold text-center text-white">
            Microphone Access Blocked
          </h3>

          <p className="mt-2 text-center text-sm text-slate-300">
            Jan Sahay needs access to your microphone so you can speak during the call.
          </p>

          <div className="my-5 rounded-2xl border border-slate-800 bg-slate-950/60 p-4 text-xs leading-relaxed text-slate-300">
            <div className="flex items-center gap-2 font-semibold text-rose-300 mb-2">
              <WarningCircle className="size-4" /> How to enable your microphone:
            </div>
            <ol className="list-decimal list-inside space-y-1.5 text-slate-400">
              <li>
                Click the <strong className="text-slate-200">lock icon <Lock className="inline size-3 text-emerald-400" /></strong> or site settings icon in your browser URL bar.
              </li>
              <li>
                Find <strong className="text-slate-200">Microphone</strong> in the permission list.
              </li>
              <li>
                Switch the permission setting to <strong className="text-emerald-400">Allow</strong>.
              </li>
              <li>
                Click the <strong className="text-slate-200">Try Again</strong> button below.
              </li>
            </ol>
          </div>

          <div className="flex items-center gap-3">
            {onClose && (
              <Button
                variant="outline"
                onClick={onClose}
                className="w-1/2 rounded-full border-slate-700 bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Dismiss
              </Button>
            )}
            <Button
              onClick={onRetry}
              className={`rounded-full bg-rose-600 text-white hover:bg-rose-500 font-semibold ${onClose ? 'w-1/2' : 'w-full'}`}
            >
              <ArrowClockwise className="size-4 mr-2" />
              Try Again
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
