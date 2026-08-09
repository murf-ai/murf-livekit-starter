'use client';

import React, { useEffect, useMemo, useState } from 'react';
import type { AiLoaderStatus } from '@/components/ui/ai-loader';
import { cn } from '@/lib/shadcn/utils';

// ── Palette ──────────────────────────────────────────────────────────
const C_INDIGO = { r: 37, g: 16, b: 79 }; // #25104F deep indigo
const C_PURPLE = { r: 91, g: 45, b: 184 }; // #5B2DB8 purple
const C_VIOLET = { r: 139, g: 92, b: 246 }; // #8B5CF6 violet
const C_LAVENDER = { r: 191, g: 160, b: 255 }; // #BFA0FF lavender

const STOP_POINTS = [C_INDIGO, C_PURPLE, C_VIOLET, C_LAVENDER];

interface Rgb {
  r: number;
  g: number;
  b: number;
}

function hex(rgb: Rgb): string {
  const c = (n: number) =>
    Math.max(0, Math.min(255, Math.round(n)))
      .toString(16)
      .padStart(2, '0');
  return `#${c(rgb.r)}${c(rgb.g)}${c(rgb.b)}`;
}

function mix(a: Rgb, b: Rgb, t: number): Rgb {
  return {
    r: a.r + (b.r - a.r) * t,
    g: a.g + (b.g - a.g) * t,
    b: a.b + (b.b - a.b) * t,
  };
}

function sampleGradient(t: number): Rgb {
  const clamped = Math.max(0, Math.min(1, t));
  const scaled = clamped * (STOP_POINTS.length - 1);
  const idx = Math.min(STOP_POINTS.length - 2, Math.floor(scaled));
  return mix(STOP_POINTS[idx], STOP_POINTS[idx + 1], scaled - idx);
}

// Deterministic pseudo-random so bars stay stable between renders.
function jitter(i: number, salt: number): number {
  const x = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return x - Math.floor(x);
}

// ── State parameters ─────────────────────────────────────────────────
interface StateParams {
  energy: number; // multiplies bar height amplitude
  brightness: number; // lightens color toward lavender
  glow: number; // glow alpha
  durationMul: number; // slower connecting, snappier speaking
}

const STATE_PARAMS: Record<Exclude<AiLoaderStatus, 'ready'>, StateParams> = {
  connecting: { energy: 0.55, brightness: 0.9, glow: 0.18, durationMul: 1.55 },
  listening: { energy: 0.9, brightness: 1.0, glow: 0.3, durationMul: 1.05 },
  speaking: { energy: 1.28, brightness: 1.22, glow: 0.62, durationMul: 0.82 },
  ended: { energy: 0, brightness: 0.5, glow: 0, durationMul: 1 },
};

// ── Responsive bar count ─────────────────────────────────────────────
function useBarCount(): number {
  const [count, setCount] = useState(() =>
    typeof window === 'undefined'
      ? 40
      : window.innerWidth < 640
        ? 20
        : window.innerWidth < 1024
          ? 30
          : 40
  );

  useEffect(() => {
    const update = () => {
      const w = window.innerWidth;
      let min = 15;
      let max = 25;
      if (w >= 640) {
        min = 25;
        max = 35;
      }
      if (w >= 1024) {
        min = 35;
        max = 45;
      }
      const c = Math.round(min + jitter(performance.now(), 1) * (max - min));
      setCount((prev) => (prev >= min && prev <= max ? prev : c));
    };

    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  return count;
}

// ── Component ────────────────────────────────────────────────────────
export interface VoiceBarVisualizerProps {
  status: AiLoaderStatus;
  className?: string;
}

export function VoiceBarVisualizer({ status, className }: VoiceBarVisualizerProps) {
  const barCount = useBarCount();
  const stateKey = status === 'ready' ? 'connecting' : status;
  const params = STATE_PARAMS[stateKey];

  const bars = useMemo(() => {
    const out: Array<{
      width: number;
      heightPct: number;
      dur: number;
      delay: number;
      opacity: number;
      color: string;
      glow: string;
    }> = [];

    for (let i = 0; i < barCount; i++) {
      const n = barCount - 1;
      const x = n === 0 ? 0.5 : i / n;
      // Triangle profile: center bars taller, edges shorter, with organic jitter.
      const central = 1 - Math.pow(Math.abs(2 * x - 1), 1.6);
      const jitterH = (jitter(i, 3) - 0.5) * 0.22;
      const silhouette = 0.3 + (central + jitterH) * 0.72;
      const heightPct = Math.max(0.05, Math.min(1, silhouette * params.energy));

      // Color: gradient across the row, brightest in the middle.
      const colorT = Math.max(0, Math.min(1, 1 - Math.pow(Math.abs(2 * x - 1), 1.3)));
      const base = sampleGradient(colorT);
      const lit = mix(base, C_LAVENDER, params.brightness * (0.08 + central * 0.3));
      const color = hex(lit);

      const glowAlpha = params.glow * (0.55 + central * 0.45);
      const opacity = Math.max(
        0.32,
        Math.min(0.98, 0.42 + central * 0.5 + (jitter(i, 7) - 0.5) * 0.12)
      );

      // Duration 1.2s–2.1s; negative delays create a flowing left→right phase.
      const dur = (1.2 + jitter(i, 5) * 0.9) * params.durationMul;
      const delay = -i * 0.09 * params.durationMul;

      out.push({
        width: 3 + (jitter(i, 9) < 0.4 ? 1 : 0) + (jitter(i, 11) < 0.15 ? 1 : 0),
        heightPct,
        dur,
        delay,
        opacity,
        color,
        glow: `rgba(139, 92, 246, ${glowAlpha.toFixed(3)})`,
      });
    }
    return out;
  }, [barCount, params]);

  const isEnded = status === 'ended';

  return (
    <div
      className={cn('relative flex flex-col items-center', className)}
      role="status"
      aria-live="polite"
    >
      {/* Faint blurred depth layer behind the bars */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-40 blur-[10px]"
        style={{ filter: 'blur(10px)' }}
      >
        {bars.map((b, i) => (
          <div key={`blur-${i}`} className="vbv-bar" style={buildBarStyle(b, isEnded)} />
        ))}
      </div>

      {/* Main bars */}
      <div className="vbv-bars flex h-[150px] items-center justify-center md:h-[200px] lg:h-[235px]">
        {bars.map((b, i) => (
          <div key={i} className="vbv-bar" style={buildBarStyle(b, isEnded)} />
        ))}
      </div>
    </div>
  );
}

function buildBarStyle(
  b: {
    heightPct: number;
    dur: number;
    delay: number;
    opacity: number;
    color: string;
    glow: string;
    width: number;
  },
  isEnded: boolean
): React.CSSProperties {
  const sheen = mix(hexToRgb(b.color), { r: 255, g: 255, b: 255 }, 0.28);
  return {
    width: `${b.width}px`,
    height: `${Math.max(4, b.heightPct * 100)}%`,
    opacity: isEnded ? 0 : b.opacity,
    background: `linear-gradient(to bottom, ${hex(sheen)} 0%, ${b.color} 22%, ${b.color} 78%, rgba(0,0,0,0.28) 100%)`,
    boxShadow: isEnded ? 'none' : `0 0 12px ${b.glow}`,
    borderRadius: '999px',
    animationName: 'vbv-bar',
    animationDuration: `${b.dur}s`,
    animationDelay: `${b.delay}s`,
    animationTimingFunction: 'cubic-bezier(0.37, 0, 0.63, 1)',
    animationIterationCount: 'infinite',
    transform: isEnded ? 'scaleY(0)' : undefined,
    transition: isEnded ? 'transform 1.2s ease-in, opacity 1.2s ease-in' : undefined,
    ['--vbv-lo' as string]: `${Math.max(0, b.heightPct * 0.3)}`,
    ['--vbv-mid' as string]: `${Math.max(0, b.heightPct * 0.6)}`,
    ['--vbv-hi' as string]: `${Math.max(0, b.heightPct * 0.95)}`,
    willChange: 'transform',
  };
}

function hexToRgb(hexColor: string): Rgb {
  const clean = hexColor.replace('#', '');
  return {
    r: parseInt(clean.slice(0, 2), 16),
    g: parseInt(clean.slice(2, 4), 16),
    b: parseInt(clean.slice(4, 6), 16),
  };
}
