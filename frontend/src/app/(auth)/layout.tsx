'use client';

import { LogoFull } from '@/components/ui/logo';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50/50 via-background to-violet-50/30 dark:from-zinc-950 dark:via-background dark:to-zinc-950">
      {/* Dot pattern overlay */}
      <div className="absolute inset-0 bg-dot-pattern opacity-[0.04] dark:opacity-[0.03]" />

      {/* Subtle glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-primary/[0.06] rounded-full blur-[120px] pointer-events-none" />

      {/* Theme toggle */}
      <div className="absolute top-5 right-5 z-20">
        <ThemeToggle />
      </div>

      {/* Centered card */}
      <div
        className={`relative z-10 w-full max-w-md mx-auto px-6 transition-all duration-700 ${
          mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'
        }`}
      >
        {/* Logo */}
        <div className="flex justify-center mb-10">
          <Link href="/">
            <LogoFull iconSize={28} textClassName="text-xl" />
          </Link>
        </div>

        {/* Card panel */}
        <div className="bg-card/80 backdrop-blur-sm border border-border/50 rounded-2xl p-8 shadow-sm">
          {children}
        </div>
      </div>

      {/* Footer */}
      <div
        className={`relative z-10 mt-8 mb-6 text-center transition-all duration-700 delay-200 ${
          mounted ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <p className="text-xs text-muted-foreground/50">
          &copy; {new Date().getFullYear()} Apply Surge. All rights reserved.
        </p>
      </div>
    </div>
  );
}
