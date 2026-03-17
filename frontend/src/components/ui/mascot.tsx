'use client';

import { cn } from '@/lib/utils';

type MascotMood = 'idle' | 'thinking' | 'celebrating' | 'waving' | 'working';
type MascotSize = 'sm' | 'md' | 'lg' | 'xl' | 'hero';

const sizes: Record<MascotSize, number> = {
  sm: 40,
  md: 64,
  lg: 96,
  xl: 140,
  hero: 200,
};

interface MascotProps {
  mood?: MascotMood;
  size?: MascotSize;
  className?: string;
}

export function Mascot({ mood = 'idle', size = 'md', className }: MascotProps) {
  const s = sizes[size];
  const glowIntensity = mood === 'celebrating' ? '0.3' : mood === 'working' ? '0.2' : '0.15';

  return (
    <div
      className={cn(
        'group relative inline-flex items-center justify-center select-none',
        'transition-transform duration-500 ease-out',
        'hover:scale-110',
        className
      )}
      style={{ width: s, height: s }}
    >
      <div
        className={cn(
          'absolute inset-0 rounded-full transition-opacity duration-700',
          'opacity-0 group-hover:opacity-100',
          mood === 'working' && 'opacity-60',
          mood === 'celebrating' && 'opacity-80',
        )}
        style={{
          background: `radial-gradient(circle, rgba(99,102,241,${glowIntensity}) 0%, rgba(139,92,246,${glowIntensity}) 40%, transparent 70%)`,
          transform: 'scale(2)',
          filter: 'blur(20px)',
        }}
      />

      <svg
        width={s}
        height={s}
        viewBox="0 0 200 200"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={cn(
          'relative z-10 transition-all duration-500',
          'drop-shadow-lg group-hover:drop-shadow-2xl',
        )}
      >
        <defs>
          <linearGradient id="surge-main" x1="0.2" y1="0" x2="0.8" y2="1">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="50%" stopColor="#8b5cf6" />
            <stop offset="100%" stopColor="#a78bfa" />
          </linearGradient>
          <linearGradient id="surge-bg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0f0e1a" />
            <stop offset="100%" stopColor="#080714" />
          </linearGradient>
          <linearGradient id="bolt-highlight" x1="0" y1="0" x2="0.5" y2="1">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
          </linearGradient>
          <radialGradient id="inner-glow" cx="0.5" cy="0.4" r="0.5">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.12" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </radialGradient>
          <filter id="bolt-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <circle cx="100" cy="100" r="92" fill="none" stroke="url(#surge-main)" strokeWidth="1" opacity="0.2" />
        <circle cx="100" cy="100" r="84" fill="url(#surge-bg)" />
        <circle cx="100" cy="100" r="84" fill="url(#inner-glow)" />
        <circle cx="100" cy="100" r="84" fill="none" stroke="url(#surge-main)" strokeWidth="1.5" opacity="0.35" />

        <g filter="url(#bolt-glow)">
          <path d="M112 38 L72 104 L94 104 L84 162 L132 88 L108 88 Z" fill="url(#surge-main)" />
          <path d="M112 38 L72 104 L94 104 L90 126 L118 76 L108 88 Z" fill="url(#bolt-highlight)" />
        </g>

        <ellipse
          cx="100" cy="100" rx="76" ry="76"
          stroke="url(#surge-main)"
          strokeWidth="0.5"
          fill="none"
          opacity="0.12"
          strokeDasharray="6 10"
        >
          {mood === 'working' && (
            <animateTransform
              attributeName="transform"
              type="rotate"
              values="0 100 100;360 100 100"
              dur="8s"
              repeatCount="indefinite"
            />
          )}
        </ellipse>

        <circle cx="32" cy="78" r="1.5" fill="#6366f1" opacity="0.25" />
        <circle cx="168" cy="122" r="1.5" fill="#8b5cf6" opacity="0.25" />
        <circle cx="50" cy="158" r="1" fill="#a78bfa" opacity="0.15" />
        <circle cx="152" cy="48" r="1" fill="#6366f1" opacity="0.15" />
      </svg>
    </div>
  );
}
