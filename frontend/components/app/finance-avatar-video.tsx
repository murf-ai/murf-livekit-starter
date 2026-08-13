'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '@/lib/shadcn/utils';

interface FinanceAvatarVideoProps {
  /** When true, video plays; when false it freezes on the current frame. */
  isSpeaking?: boolean;
  /** Loop continuously (welcome / connecting / idle). */
  alwaysPlay?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'hero';
}

const VIDEOS = [
  '/finance_avatar/finance1.mp4',
  '/finance_avatar/finance2.mp4',
  '/finance_avatar/finance3.mp4',
  '/finance_avatar/finance4.mp4',
] as const;

/** Outer circular frame sizes */
const SIZE_CLASSES = {
  sm: 'size-28 md:size-32',
  md: 'size-36 md:size-44',
  lg: 'size-44 md:size-56',
  xl: 'size-56 md:size-72',
  hero: 'size-64 md:size-80',
} as const;

function shuffleOrder(length: number): number[] {
  const order = Array.from({ length }, (_, i) => i);
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  return order;
}

export function FinanceAvatarVideo({
  isSpeaking = false,
  alwaysPlay = false,
  className = '',
  size = 'lg',
}: FinanceAvatarVideoProps) {
  // Random playlist so we don't always start on finance1 and feel "stuck"
  const playlist = useMemo(() => shuffleOrder(VIDEOS.length), []);
  const [playlistPos, setPlaylistPos] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const shouldPlay = alwaysPlay || isSpeaking;

  const currentSrc = VIDEOS[playlist[playlistPos % playlist.length]];

  const advance = useCallback(() => {
    setPlaylistPos((pos) => (pos + 1) % playlist.length);
  }, [playlist.length]);

  // When clip changes, load + play the next file
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    video.pause();
    video.src = currentSrc;
    video.load();

    const onCanPlay = () => {
      if (shouldPlay) {
        video.play().catch(() => {});
      }
    };
    video.addEventListener('canplay', onCanPlay, { once: true });

    return () => {
      video.removeEventListener('canplay', onCanPlay);
    };
  }, [currentSrc, shouldPlay]);

  // Play / pause when speaking state flips (same clip)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (shouldPlay) {
      video.play().catch(() => {});
    } else {
      video.pause();
    }
  }, [shouldPlay]);

  // While speaking, jump to next clip occasionally for variety
  useEffect(() => {
    if (!isSpeaking) return;
    const id = window.setInterval(() => {
      advance();
    }, 6000);
    return () => window.clearInterval(id);
  }, [isSpeaking, advance]);

  return (
    <div className={cn('relative flex items-center justify-center', className)}>
      <div
        className={cn(
          'absolute inset-0 rounded-full bg-emerald-500/30 blur-2xl transition-all duration-700',
          isSpeaking || alwaysPlay ? 'scale-110 opacity-70' : 'scale-100 opacity-40',
          isSpeaking && 'animate-pulse'
        )}
      />

      <div
        className={cn(
          'relative overflow-hidden rounded-full bg-slate-950 shadow-[0_0_40px_-8px_rgba(16,185,129,0.5)] ring-1 ring-emerald-400/30',
          SIZE_CLASSES[size]
        )}
      >
        <video
          ref={videoRef}
          playsInline
          muted
          preload="auto"
          loop={false}
          onEnded={advance}
          className="h-full w-full origin-center scale-[2.15] object-cover object-center"
          aria-label="Jan Sahay"
        />
      </div>
    </div>
  );
}
