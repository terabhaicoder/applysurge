'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpRight,
  Zap,
  Bot,
  Globe,
  Mail,
  BarChart3,
  Shield,
  Target,
  Clock,
  Sparkles,
  Check,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { LogoAppIcon } from '@/components/ui/logo';

const features = [
  {
    icon: Globe,
    title: 'Multi-Platform Discovery',
    description: 'Scrapes LinkedIn and job boards to surface roles that match your profile automatically.',
    accent: 'bg-blue-500/10 text-blue-500',
  },
  {
    icon: Bot,
    title: 'AI-Powered Applications',
    description: 'Fills out forms, uploads resumes, and submits applications with intelligent personalization.',
    accent: 'bg-violet-500/10 text-violet-500',
  },
  {
    icon: Mail,
    title: 'Cold Email Outreach',
    description: 'Finds hiring manager contacts and sends personalized messages with automated follow-ups.',
    accent: 'bg-rose-500/10 text-rose-500',
  },
  {
    icon: Target,
    title: 'Smart Job Matching',
    description: 'AI scores every job against your skills and preferences so you only apply to relevant roles.',
    accent: 'bg-primary/10 text-primary',
  },
  {
    icon: Shield,
    title: 'Screening Question AI',
    description: 'Answers pre-screening questions using your profile data. Never miss a qualifier again.',
    accent: 'bg-amber-500/10 text-amber-500',
  },
  {
    icon: Zap,
    title: 'Cover Letter Generation',
    description: 'Creates tailored cover letters highlighting the most relevant parts of your experience.',
    accent: 'bg-emerald-500/10 text-emerald-500',
  },
  {
    icon: BarChart3,
    title: 'Analytics Dashboard',
    description: 'Track application status, response rates, and interview conversions in one place.',
    accent: 'bg-cyan-500/10 text-cyan-500',
  },
  {
    icon: Clock,
    title: 'Autonomous Agent',
    description: 'Set it and forget it. The agent runs in the background while you focus on interview prep.',
    accent: 'bg-fuchsia-500/10 text-fuchsia-500',
  },
];

const valueProps = [
  {
    title: 'Apply at Scale',
    desc: 'Submit applications across multiple platforms without hours of manual form filling.',
  },
  {
    title: 'Personalized Quality',
    desc: 'Every application is tailored to the role with AI responses that reflect your real experience.',
  },
  {
    title: 'Focus on What Matters',
    desc: 'Spend your time on interview prep and networking instead of copy-pasting the same information.',
  },
];

export default function FeaturesPage() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Navigation */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled
            ? 'bg-background/80 backdrop-blur-xl border-b border-border shadow-sm'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between items-center h-16 lg:h-[72px]">
            <Link href="/" className="flex items-center gap-2.5">
              <LogoAppIcon size={32} />
              <span className="text-lg font-display font-bold tracking-tight text-foreground">
                Apply Surge
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <Link href="/features" className="text-sm text-primary font-semibold">
                Features
              </Link>
              <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">
                Pricing
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/login"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors hidden sm:block"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="group text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 px-5 py-2.5 rounded-lg transition-all duration-200 flex items-center gap-1.5 shadow-sm"
              >
                Get Started
                <ArrowUpRight className="w-3.5 h-3.5 opacity-70 group-hover:opacity-100 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-36 lg:pt-44 pb-20 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-dot-pattern opacity-30 pointer-events-none" />
        <div className="absolute -top-40 left-1/4 w-[500px] h-[500px] bg-primary/[0.04] rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-20 right-1/4 w-[400px] h-[400px] bg-accent/[0.03] rounded-full blur-[80px] pointer-events-none" />

        <div className="max-w-5xl mx-auto relative z-10 text-center">
          <div className="opacity-0 animate-slide-up inline-flex items-center gap-2.5 bg-primary/[0.06] border border-primary/10 px-4 py-2 rounded-full mb-8">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-semibold text-primary uppercase tracking-wider">
              Powerful Automation
            </span>
          </div>

          <h1 className="opacity-0 animate-slide-up-delay-1 font-display text-4xl sm:text-5xl lg:text-[4rem] font-extrabold tracking-tight leading-[1.1]">
            Features that make
            <br />
            <span className="text-gradient">job searching effortless.</span>
          </h1>

          <p className="opacity-0 animate-slide-up-delay-2 mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Everything you need to automate your job applications and land more interviews.
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-24 px-6 bg-secondary/30">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((feature, i) => {
              const accentParts = feature.accent.split(' ');
              const bgColor = accentParts[0];
              const textColor = accentParts[1];

              return (
                <div
                  key={i}
                  className="group bg-card border border-border hover:border-primary/20 rounded-2xl p-6 transition-all duration-300 hover:shadow-lg hover:shadow-primary/[0.04] hover:-translate-y-[2px]"
                >
                  <div className={`w-11 h-11 rounded-xl ${bgColor} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                    <feature.icon className={`w-5 h-5 ${textColor}`} />
                  </div>
                  <h3 className="font-display text-[15px] font-bold text-foreground mb-1.5 tracking-tight group-hover:text-primary transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Why Apply Surge */}
      <section className="py-24 px-6 relative">
        <div className="absolute inset-0 bg-dot-pattern opacity-20 pointer-events-none" />
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="text-center mb-14">
            <span className="text-xs font-bold text-primary uppercase tracking-[0.15em] mb-3 block">
              Why Apply Surge
            </span>
            <h2 className="font-display text-3xl md:text-[2.5rem] font-extrabold tracking-tight text-foreground">
              Built for <span className="text-gradient">serious job seekers.</span>
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-5">
            {valueProps.map((item, i) => (
              <div
                key={i}
                className="bg-card border border-border rounded-2xl p-7 text-center hover:border-primary/20 hover:shadow-md transition-all duration-300"
              >
                <div className="w-10 h-10 mx-auto mb-4 rounded-xl bg-primary/[0.08] flex items-center justify-center">
                  <Check className="w-5 h-5 text-primary" />
                </div>
                <div className="font-display text-base font-bold text-foreground mb-2">
                  {item.title}
                </div>
                <p className="text-sm text-muted-foreground leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-24 px-6 bg-secondary/30">
        <div className="absolute inset-0 bg-gradient-to-t from-primary/[0.03] via-transparent to-transparent pointer-events-none" />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight mb-6 leading-tight text-foreground">
            Ready to automate
            <br />
            <span className="text-gradient">your job search?</span>
          </h2>

          <div className="mt-10">
            <Link
              href="/register"
              className="group inline-flex items-center justify-center gap-2 bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3.5 rounded-xl text-[15px] font-semibold transition-all duration-200 shadow-md shadow-primary/20 hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]"
            >
              Get Started
              <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-16 px-6 bg-secondary/20">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between gap-12">
            <div className="flex flex-col gap-4">
              <Link href="/" className="flex items-center gap-2.5">
                <LogoAppIcon size={32} />
                <span className="text-lg font-display font-bold text-foreground">
                  Apply Surge
                </span>
              </Link>
              <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">
                The autonomous AI agent that handles your entire job search
                pipeline.
              </p>
            </div>

            <div className="flex gap-16">
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                  Product
                </span>
                <Link href="/features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Features
                </Link>
                <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Pricing
                </Link>
              </div>
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                  Account
                </span>
                <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Sign in
                </Link>
                <Link href="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">
                  Get Started
                </Link>
              </div>
            </div>
          </div>

          <div className="mt-16 pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Apply Surge. All rights reserved.
            </p>
            <p className="text-xs text-muted-foreground">
              Built by{' '}
              <a
                href="https://paarthpanthri.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-foreground font-medium hover:text-primary transition-colors"
              >
                Paarth Panthri
              </a>
            </p>
            <div className="flex gap-6">
              <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
                Privacy
              </span>
              <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">
                Terms
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
