'use client';

import { useTheme } from 'next-themes';
import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { BharatPayWelcomeView } from '@/components/app/bharatpay-welcome-view';
import { BharatPaySessionView } from '@/components/app/bharatpay-session-view';
import { cn } from '@/lib/shadcn/utils';

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: {
    duration: 0.5,
    ease: 'linear',
  },
};

const FALLING_RUPEES = [
  // Left side particles
  {
    id: 1,
    left: '3%',
    duration: '12s',
    delay: '-0s',
    color: '#FFD34E',
    fontSize: '24px',
    textShadow: '0 0 8px rgba(255,211,78,0.45), 0 0 18px rgba(255,193,7,0.20)',
  },
  {
    id: 2,
    left: '8%',
    duration: '15s',
    delay: '-2s',
    color: '#F5C542',
    fontSize: '32px',
    textShadow: '0 0 10px rgba(245,197,66,0.50), 0 0 22px rgba(255,193,7,0.25)',
  },
  {
    id: 3,
    left: '12%',
    duration: '13s',
    delay: '-4s',
    color: '#FFC857',
    fontSize: '20px',
    textShadow: '0 0 6px rgba(255,200,87,0.40), 0 0 14px rgba(255,193,7,0.18)',
  },
  {
    id: 4,
    left: '5%',
    duration: '16s',
    delay: '-6s',
    color: '#FFD34E',
    fontSize: '28px',
    filter: 'blur(0.5px)',
    textShadow: '0 0 8px rgba(255,211,78,0.45), 0 0 18px rgba(255,193,7,0.20)',
  },
  {
    id: 5,
    left: '14%',
    duration: '11s',
    delay: '-8s',
    color: '#F5C542',
    fontSize: '22px',
    textShadow: '0 0 7px rgba(245,197,66,0.42), 0 0 16px rgba(255,193,7,0.20)',
  },
  {
    id: 6,
    left: '2%',
    duration: '14s',
    delay: '-10s',
    color: '#FFC857',
    fontSize: '26px',
    textShadow: '0 0 8px rgba(255,200,87,0.45), 0 0 18px rgba(255,193,7,0.22)',
  },
  // Right side particles
  {
    id: 7,
    right: '3%',
    duration: '13s',
    delay: '-1s',
    color: '#FFD34E',
    fontSize: '28px',
    textShadow: '0 0 8px rgba(255,211,78,0.45), 0 0 18px rgba(255,193,7,0.20)',
  },
  {
    id: 8,
    right: '9%',
    duration: '15s',
    delay: '-3s',
    color: '#FFC857',
    fontSize: '24px',
    textShadow: '0 0 8px rgba(255,200,87,0.45), 0 0 18px rgba(255,193,7,0.22)',
  },
  {
    id: 9,
    right: '13%',
    duration: '12s',
    delay: '-5s',
    color: '#F5C542',
    fontSize: '32px',
    textShadow: '0 0 10px rgba(245,197,66,0.50), 0 0 22px rgba(255,193,7,0.25)',
  },
  {
    id: 10,
    right: '6%',
    duration: '16s',
    delay: '-7s',
    color: '#FFD34E',
    fontSize: '20px',
    filter: 'blur(0.5px)',
    textShadow: '0 0 6px rgba(255,211,78,0.40), 0 0 14px rgba(255,193,7,0.18)',
  },
  {
    id: 11,
    right: '14%',
    duration: '11s',
    delay: '-9s',
    color: '#FFC857',
    fontSize: '26px',
    textShadow: '0 0 8px rgba(255,200,87,0.45), 0 0 18px rgba(255,193,7,0.22)',
  },
  {
    id: 12,
    right: '4%',
    duration: '14s',
    delay: '-11s',
    color: '#F5C542',
    fontSize: '22px',
    textShadow: '0 0 7px rgba(245,197,66,0.42), 0 0 16px rgba(255,193,7,0.20)',
  },
];

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();
  const { resolvedTheme } = useTheme();

  return (
    <div className="relative h-full w-full overflow-hidden bg-[#030303]">
      {/* Falling Rupees ambient animation background */}
      <div className="pointer-events-none absolute inset-0 z-40 overflow-hidden">
        {FALLING_RUPEES.map((p) => {
          // Responsive: hide half of the particles on small mobile screens
          const MOBILE_VISIBLE_IDS = [1, 2, 5, 7, 9, 11];
          const isMobileHidden = !MOBILE_VISIBLE_IDS.includes(p.id);
          return (
            <span
              key={p.id}
              className={cn(
                'falling-rupee absolute font-serif select-none',
                isMobileHidden && 'hidden md:block'
              )}
              style={
                {
                  left: p.left,
                  right: p.right,
                  fontSize: p.fontSize,
                  filter: (p as any).filter,
                  textShadow: p.textShadow,
                  color: p.color,
                  animationDelay: p.delay,
                  animationDuration: p.duration,
                } as React.CSSProperties
              }
            >
              ₹
            </span>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {/* Welcome view */}
        {!isConnected && (
          <motion.div key="welcome" {...VIEW_MOTION_PROPS} className="h-full w-full">
            <BharatPayWelcomeView
              startButtonText={appConfig.startButtonText}
              onStartCall={start}
            />
          </motion.div>
        )}

        {/* Session view */}
        {isConnected && (
          <motion.div key="session" {...VIEW_MOTION_PROPS} className="h-full w-full">
            <BharatPaySessionView
              supportsChatInput={appConfig.supportsChatInput}
              supportsVideoInput={appConfig.supportsVideoInput}
              supportsScreenShare={appConfig.supportsScreenShare}
              isPreConnectBufferEnabled={appConfig.isPreConnectBufferEnabled}
              audioVisualizerType={appConfig.audioVisualizerType}
              audioVisualizerColor={
                resolvedTheme === 'dark'
                  ? appConfig.audioVisualizerColorDark
                  : appConfig.audioVisualizerColor
              }
              audioVisualizerColorShift={appConfig.audioVisualizerColorShift}
              audioVisualizerBarCount={appConfig.audioVisualizerBarCount}
              audioVisualizerGridRowCount={appConfig.audioVisualizerGridRowCount}
              audioVisualizerGridColumnCount={appConfig.audioVisualizerGridColumnCount}
              audioVisualizerRadialBarCount={appConfig.audioVisualizerRadialBarCount}
              audioVisualizerRadialRadius={appConfig.audioVisualizerRadialRadius}
              audioVisualizerWaveLineWidth={appConfig.audioVisualizerWaveLineWidth}
              className="fixed inset-0"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
