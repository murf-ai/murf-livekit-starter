'use client';

import React, { useRef, useState } from 'react';
import { cn } from '@/lib/shadcn/utils';

export function CardSpotlight({ children, className, ...props }: React.ComponentProps<'div'>) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={cn(
        'group relative overflow-hidden rounded-2xl border border-white/[0.06] bg-[#080808]/90 p-6 transition-all duration-300 hover:-translate-y-1 hover:border-purple-500/25 hover:shadow-[0_8px_30px_rgba(0,0,0,0.5)]',
        className
      )}
      {...props}
    >
      {/* Background Spotlight Glow */}
      <div
        className="pointer-events-none absolute -inset-px transition-opacity duration-300"
        style={{
          background: isHovered
            ? `radial-gradient(350px circle at ${coords.x}px ${coords.y}px, rgba(139, 92, 246, 0.05), transparent 80%)`
            : 'transparent',
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
