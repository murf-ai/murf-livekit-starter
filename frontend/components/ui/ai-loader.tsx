'use client';

import React from 'react';
import { cn } from '@/lib/shadcn/utils';

/**
 * Live states of the RupeeGPT Voice agent. Each state drives the status label
 * rendered underneath the orb.
 */
export type AiLoaderStatus = 'ready' | 'connecting' | 'listening' | 'speaking' | 'ended';

export const AI_LOADER_LABELS: Record<AiLoaderStatus, string> = {
  ready: 'RupeeGPT',
  connecting: 'CONNECTING...',
  listening: 'LISTENING...',
  speaking: 'SPEAKING...',
  ended: 'ENDED',
};

const AI_LOADER_WORDS: Record<AiLoaderStatus, string> = {
  ready: 'Generating',
  connecting: 'Generating',
  listening: 'Generating',
  speaking: 'Generating',
  ended: 'Generating',
};

const AI_LOADER_SIZES = {
  sm: { orb: 'size-20', text: 'text-[11px]' },
  md: { orb: 'size-36 md:size-40', text: 'text-sm md:text-base' },
  lg: {
    orb: 'size-[220px] md:size-[280px] lg:size-[300px]',
    text: 'text-[22px] md:text-[24px] font-semibold',
  },
} as const;

export interface AiLoaderProps extends React.ComponentProps<'div'> {
  /**
   * The active voice agent state.
   *
   * @default 'ready'
   */
  status?: AiLoaderStatus;
  /**
   * Size of the glowing orb.
   *
   * @default 'md'
   */
  size?: keyof typeof AI_LOADER_SIZES;
  /**
   * Overrides the default label for the current `status`.
   */
  label?: string;
  /**
   * Hides the status label rendered beneath the orb.
   *
   * @default false
   */
  hideLabel?: boolean;
}

export function Component({
  status = 'ready',
  size = 'md',
  label,
  hideLabel = false,
  className,
  ...props
}: AiLoaderProps) {
  const word = AI_LOADER_WORDS[status];
  const statusLabel = label ?? AI_LOADER_LABELS[status];
  const { orb: orbSize, text: textSize } = AI_LOADER_SIZES[size];

  // Dynamic animation speeds & glow characteristics depending on connection state
  const stateStyles = React.useMemo(() => {
    switch (status) {
      case 'speaking':
        return {
          '--orb-speed': '8s',
          '--orb-glow-color': 'rgba(196, 167, 255, 0.18)',
          '--orb-glow-radius': '16px',
        } as React.CSSProperties;
      case 'listening':
        return {
          '--orb-speed': '10s',
          '--orb-glow-color': 'rgba(139, 92, 246, 0.14)',
          '--orb-glow-radius': '12px',
        } as React.CSSProperties;
      case 'connecting':
      default:
        return {
          '--orb-speed': '12s',
          '--orb-glow-color': 'rgba(139, 92, 246, 0.08)',
          '--orb-glow-radius': '10px',
        } as React.CSSProperties;
    }
  }, [status]);

  return (
    <div
      className={cn('ai-loader flex flex-col items-center justify-center gap-4', className)}
      {...props}
    >
      {/* Orb container */}
      <div
        className={cn('ai-loader-orb-wrap relative', orbSize)}
        style={stateStyles}
        role="status"
        aria-label={statusLabel}
      >
        <span className="ai-loader-orb-halo" aria-hidden="true" />
        <div className="ai-loader-orb">
          {/* Shift highlights layer */}
          <div className="loader" aria-hidden="true" />

          {/* Glowing and stationary text inside the purple orb */}
          {word && (
            <div className="loader-word" aria-hidden="true">
              <span
                className={cn(
                  'font-sans font-semibold tracking-widest text-[#d3d0da] drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)] select-none',
                  textSize
                )}
              >
                {word}
              </span>
            </div>
          )}
        </div>
      </div>

      {!hideLabel && (
        <p
          role="status"
          className="mt-1.5 font-sans text-[10px] font-semibold tracking-[0.25em] text-[#9a9a9a]/85 uppercase"
        >
          {statusLabel}
        </p>
      )}
    </div>
  );
}

export { Component as AiLoader };
