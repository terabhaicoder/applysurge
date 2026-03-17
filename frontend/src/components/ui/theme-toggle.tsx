'use client';

import { Moon, Sun } from 'lucide-react';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

interface ThemeToggleProps {
  className?: string;
}

export function ThemeToggle({ className }: ThemeToggleProps) {
  const { theme, toggleTheme } = useUIStore();
  const isDark = theme === 'dark';

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'relative inline-flex h-8 w-8 items-center justify-center rounded-lg',
        'text-muted-foreground hover:text-foreground hover:bg-secondary',
        'transition-colors duration-200',
        className
      )}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <Sun
        className={cn(
          'h-[18px] w-[18px] transition-all duration-300',
          isDark ? 'scale-0 rotate-90 opacity-0' : 'scale-100 rotate-0 opacity-100'
        )}
        style={{ position: isDark ? 'absolute' : 'relative' }}
      />
      <Moon
        className={cn(
          'h-[18px] w-[18px] transition-all duration-300',
          isDark ? 'scale-100 rotate-0 opacity-100' : 'scale-0 -rotate-90 opacity-0'
        )}
        style={{ position: isDark ? 'relative' : 'absolute' }}
      />
    </button>
  );
}
