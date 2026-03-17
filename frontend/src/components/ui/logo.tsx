'use client';

import { cn } from '@/lib/utils';

interface LogoIconProps {
  size?: number;
  className?: string;
  variant?: 'auto' | 'onDark';
}

export function LogoIcon({ size = 20, className, variant = 'auto' }: LogoIconProps) {
  const id = `logo-${Math.random().toString(36).slice(2, 8)}`;

  if (variant === 'onDark') {
    return (
      <svg width={size} height={size} viewBox="0 0 40 40" fill="none" className={className}>
        {/* Clean geometric "A" mark */}
        <path
          d="M20 2L4 38h9l3-7h8l3 7h9L20 2zM16.5 26L20 10l3.5 16h-7z"
          fill="white"
          fillRule="evenodd"
          opacity="0.95"
        />
      </svg>
    );
  }

  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" className={className}>
      <defs>
        <linearGradient id={`${id}-grad`} x1="0" y1="0" x2="0.5" y2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
      {/* Clean geometric "A" mark */}
      <path
        d="M20 2L4 38h9l3-7h8l3 7h9L20 2zM16.5 26L20 10l3.5 16h-7z"
        fill={`url(#${id}-grad)`}
        fillRule="evenodd"
      />
    </svg>
  );
}

interface LogoAppIconProps {
  size?: number;
  className?: string;
}

export function LogoAppIcon({ size = 28, className }: LogoAppIconProps) {
  const id = `appicon-${Math.random().toString(36).slice(2, 8)}`;

  return (
    <svg width={size} height={size} viewBox="0 0 40 40" fill="none" className={className}>
      <defs>
        <linearGradient id={`${id}-bg`} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#8b5cf6" />
        </linearGradient>
      </defs>
      {/* Rounded rect background */}
      <rect width="40" height="40" rx="10" fill={`url(#${id}-bg)`} />
      {/* Clean geometric "A" mark */}
      <path
        d="M20 5L7 35h7.5l2.5-6h6l2.5 6H33L20 5zM17.5 24.5L20 13l2.5 11.5h-5z"
        fill="white"
        fillRule="evenodd"
        opacity="0.95"
      />
    </svg>
  );
}

interface LogoFullProps {
  iconSize?: number;
  className?: string;
  textClassName?: string;
  variant?: 'auto' | 'onDark';
}

export function LogoFull({
  iconSize = 28,
  className,
  textClassName,
  variant = 'auto',
}: LogoFullProps) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      {variant === 'onDark' ? (
        <div className="flex-shrink-0 w-9 h-9 bg-white/10 backdrop-blur-sm rounded-xl flex items-center justify-center">
          <LogoIcon size={iconSize * 0.72} variant="onDark" />
        </div>
      ) : (
        <LogoAppIcon size={iconSize + 8} className="flex-shrink-0" />
      )}
      <span
        className={cn(
          'font-display font-bold tracking-tight',
          variant === 'onDark' ? 'text-white' : 'text-foreground',
          textClassName
        )}
      >
        Apply Surge
      </span>
    </div>
  );
}
