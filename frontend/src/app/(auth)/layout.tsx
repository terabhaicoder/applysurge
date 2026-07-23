'use client';

import { LogoFull } from '@/components/ui/logo';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Zap, Shield, Target } from 'lucide-react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => { setMounted(true); }, []);

  return (
    <div className="relative min-h-screen flex">
      {/* Left panel — branding & features */}
      <div className="hidden lg:flex lg:w-[45%] xl:w-[42%] relative overflow-hidden bg-gradient-to-br from-indigo-600 via-indigo-700 to-violet-800">
        {/* Decorative circles */}
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-white/[0.07] rounded-full blur-xl" />
        <div className="absolute bottom-20 -right-32 w-[500px] h-[500px] bg-violet-500/20 rounded-full blur-2xl" />
        <div className="absolute top-1/3 left-1/4 w-64 h-64 bg-indigo-400/10 rounded-full blur-2xl" />

        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.06]" style={{
          backgroundImage: 'linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }} />

        <div className={`relative z-10 flex flex-col justify-between p-10 xl:p-14 w-full transition-all duration-700 ${mounted ? 'opacity-100 translate-x-0' : 'opacity-0 -translate-x-4'}`}>
          {/* Logo */}
          <div>
            <Link href="/" className="inline-flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <span className="text-white font-bold text-lg">A</span>
              </div>
              <span className="text-white font-semibold text-xl tracking-tight">Apply Surge</span>
            </Link>
          </div>

          {/* Tagline */}
          <div className="space-y-8">
            <div>
              <h2 className="text-3xl xl:text-4xl font-bold text-white leading-tight">
                Land your dream job,<br />
                <span className="text-indigo-200">on autopilot.</span>
              </h2>
              <p className="mt-4 text-indigo-200/80 text-base max-w-sm leading-relaxed">
                AI-powered job applications that work while you sleep. Set your preferences, and let the agent do the rest.
              </p>
            </div>

            {/* Feature pills */}
            <div className="space-y-3">
              {[
                { icon: Zap, text: 'Auto-apply to matching jobs on LinkedIn' },
                { icon: Target, text: 'AI matches you to the right roles' },
                { icon: Shield, text: 'Your credentials stay encrypted' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 text-indigo-100/90">
                  <div className="w-8 h-8 rounded-lg bg-white/10 backdrop-blur-sm flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-4 h-4" />
                  </div>
                  <span className="text-sm">{item.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <p className="text-indigo-300/50 text-xs">
            &copy; {new Date().getFullYear()} Augustinnovate Pvt. Ltd.
          </p>
        </div>
      </div>

      {/* Right panel — auth form */}
      <div className="flex-1 relative flex flex-col items-center justify-center bg-gradient-to-br from-slate-50 via-white to-indigo-50/30 dark:from-zinc-950 dark:via-zinc-900 dark:to-zinc-950">
        {/* Subtle dot pattern */}
        <div className="absolute inset-0 bg-dot-pattern opacity-[0.03] dark:opacity-[0.02]" />

        {/* Top-right glow */}
        <div className="absolute top-0 right-0 w-[400px] h-[300px] bg-indigo-500/[0.04] rounded-full blur-[100px] pointer-events-none" />

        {/* Theme toggle */}
        <div className="absolute top-5 right-5 z-20">
          <ThemeToggle />
        </div>

        {/* Mobile logo (hidden on lg) */}
        <div className={`lg:hidden flex justify-center mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'}`}>
          <Link href="/">
            <LogoFull iconSize={28} textClassName="text-xl" />
          </Link>
        </div>

        {/* Card */}
        <div className={`relative z-10 w-full max-w-[420px] mx-auto px-6 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-3'}`}>
          <div className="bg-card/80 backdrop-blur-sm border border-border/40 rounded-2xl p-8 shadow-lg shadow-black/[0.03] dark:shadow-black/20">
            {children}
          </div>
        </div>

        {/* Footer (mobile / no left panel) */}
        <div className={`lg:hidden relative z-10 mt-8 mb-6 text-center transition-all duration-700 delay-200 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
          <p className="text-xs text-muted-foreground/50">
            &copy; {new Date().getFullYear()} Augustinnovate Pvt. Ltd.
          </p>
        </div>
      </div>
    </div>
  );
}
