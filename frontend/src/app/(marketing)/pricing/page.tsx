'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Sparkles,
  Star,
  Crown,
} from 'lucide-react';
import { LogoAppIcon } from '@/components/ui/logo';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

const tiers = [
  {
    name: 'Beta',
    icon: Star,
    price: 0,
    originalPrice: null,
    description: 'Full access during beta',
    features: [
      '10 total applications',
      'AI-powered job matching',
      'LinkedIn Easy Apply',
      'AI screening answers',
      'Cover letter generation',
      'Application tracking',
    ],
    cta: 'Get Started Free',
    popular: true,
    beta: true,
    comingSoon: false,
  },
  {
    name: 'Pro',
    icon: Sparkles,
    price: 29,
    originalPrice: 29,
    description: 'For serious job seekers',
    features: [
      '50 applications per day',
      'AI-powered job matching',
      'All job platforms',
      'Cold email outreach',
      'Priority support',
      'Full history',
      'Resume optimization',
    ],
    cta: 'Coming Soon',
    popular: false,
    beta: false,
    comingSoon: true,
  },
  {
    name: 'Premium',
    icon: Crown,
    price: 79,
    originalPrice: 79,
    description: 'Maximum power for your search',
    features: [
      'Unlimited applications',
      'Advanced AI matching',
      'All platforms + custom portals',
      'Cold email + follow-ups',
      'Dedicated support',
      'Resume & cover letter AI',
      'Interview prep assistant',
      'Analytics dashboard',
    ],
    cta: 'Coming Soon',
    popular: false,
    beta: false,
    comingSoon: true,
  },
];

const faqs = [
  {
    q: 'What is the beta?',
    a: 'Apply Surge is currently in beta. You get full access to all features for free with a limit of 10 total applications. Paid plans with higher limits are coming soon.',
  },
  {
    q: 'What happens when I reach my beta limit?',
    a: 'The agent will stop applying once you reach 10 total applications. Paid plans with higher limits will be available soon.',
  },
  {
    q: 'Is my data secure?',
    a: 'All credentials are encrypted using AES-256. We never share your data with third parties.',
  },
  {
    q: 'When will paid plans launch?',
    a: 'Pro and Premium plans are coming soon. Join the beta now to be first in line and get an exclusive launch discount.',
  },
];

export default function PricingPage() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* ── Navigation ── */}
      <nav
        className={cn(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
          isScrolled
            ? 'bg-background/80 backdrop-blur-xl border-b border-border shadow-sm'
            : 'bg-transparent'
        )}
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
              <Link
                href="/features"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium"
              >
                Features
              </Link>
              <Link
                href="/pricing"
                className="text-sm text-primary font-semibold"
              >
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

      {/* ── Hero ── */}
      <section className="relative pt-36 lg:pt-44 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-dot-pattern opacity-30 pointer-events-none" />
        <div className="absolute -top-40 left-1/4 w-[500px] h-[500px] bg-primary/[0.04] rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-20 right-1/4 w-[400px] h-[400px] bg-accent/[0.03] rounded-full blur-[80px] pointer-events-none" />

        <div className="max-w-5xl mx-auto relative z-10 text-center">
          <div className="opacity-0 animate-slide-up inline-flex items-center gap-2.5 bg-amber-500/[0.08] border border-amber-500/15 px-4 py-2 rounded-full mb-8">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
              Beta Access
            </span>
          </div>

          <h1 className="opacity-0 animate-slide-up-delay-1 font-display text-4xl sm:text-5xl lg:text-[4rem] font-extrabold tracking-tight leading-[1.1]">
            Free during{' '}
            <span className="text-gradient">beta.</span>
          </h1>

          <p className="opacity-0 animate-slide-up-delay-2 mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Get full access to AI-powered job automation for free. Paid plans
            with higher limits are coming soon.
          </p>
        </div>
      </section>

      {/* ── Pricing Cards ── */}
      <section className="pb-24 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5 lg:gap-6">
            {tiers.map((tier, i) => {
              const TierIcon = tier.icon;
              return (
                <div
                  key={i}
                  className={cn(
                    'relative bg-card border rounded-2xl p-7 transition-all duration-300',
                    tier.popular
                      ? 'border-primary/40 shadow-xl shadow-primary/[0.08] md:scale-105 z-10'
                      : 'border-border hover:border-primary/15 hover:shadow-md'
                  )}
                >
                  {tier.beta && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-primary text-primary-foreground text-xs font-bold rounded-full shadow-lg shadow-primary/25">
                        <Star className="w-3 h-3" />
                        Free Beta
                      </span>
                    </div>
                  )}
                  {tier.comingSoon && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                      <span className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-secondary border border-border text-muted-foreground text-xs font-bold rounded-full">
                        Coming Soon
                      </span>
                    </div>
                  )}

                  <div className="mb-6">
                    <div className="flex items-center gap-2 mb-1">
                      <TierIcon className="w-4 h-4 text-primary" />
                      <h3 className="font-display text-xl font-bold text-foreground">
                        {tier.name}
                      </h3>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {tier.description}
                    </p>
                  </div>

                  <div className="mb-6">
                    {tier.comingSoon && tier.originalPrice ? (
                      <div className="flex items-baseline gap-2">
                        <span className="font-display text-4xl font-extrabold text-muted-foreground/40 tracking-tight line-through">
                          ${tier.originalPrice}
                        </span>
                        <span className="text-muted-foreground text-sm">
                          /month
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-baseline gap-1">
                        <span className="font-display text-4xl font-extrabold text-foreground tracking-tight">
                          $0
                        </span>
                        <span className="text-muted-foreground text-sm">
                          during beta
                        </span>
                      </div>
                    )}
                  </div>

                  <ul className="space-y-3 mb-8">
                    {tier.features.map((feature, j) => (
                      <li
                        key={j}
                        className="flex items-center gap-2.5 text-sm text-muted-foreground"
                      >
                        <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                          <Check className="w-3 h-3 text-emerald-500" />
                        </div>
                        {feature}
                      </li>
                    ))}
                  </ul>

                  {tier.comingSoon ? (
                    <div className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm border border-border text-muted-foreground cursor-not-allowed opacity-60">
                      {tier.cta}
                    </div>
                  ) : (
                    <Link
                      href="/register"
                      className="w-full flex items-center justify-center gap-2 py-3 rounded-xl font-semibold text-sm transition-all duration-200 bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/20 hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]"
                    >
                      {tier.cta}
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── FAQ ── */}
      <section className="py-24 px-6 bg-secondary/30">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-14">
            <span className="text-xs font-bold text-primary uppercase tracking-[0.15em] mb-3 block">
              FAQ
            </span>
            <h2 className="font-display text-3xl md:text-[2.5rem] font-extrabold tracking-tight text-foreground">
              Frequently asked questions.
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div
                key={i}
                className="bg-card border border-border rounded-2xl p-6 hover:border-primary/15 transition-colors"
              >
                <h3 className="font-display font-bold text-foreground mb-2">
                  {faq.q}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {faq.a}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="relative py-24 px-6">
        <div className="absolute inset-0 bg-gradient-to-t from-primary/[0.03] via-transparent to-transparent pointer-events-none" />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-accent/10 border border-accent/20 px-4 py-2 rounded-full mb-8">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            <span className="text-xs font-bold text-accent uppercase tracking-wider">
              Get Started
            </span>
          </div>

          <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight mb-6 leading-tight text-foreground">
            Ready to automate
            <br />
            <span className="text-gradient">your job search?</span>
          </h2>

          <p className="text-muted-foreground text-lg mb-10 max-w-xl mx-auto leading-relaxed">
            Join the beta today and let AI handle your job applications.
          </p>

          <Link
            href="/register"
            className="group inline-flex items-center justify-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground px-9 py-4 rounded-xl text-base font-semibold transition-all duration-200 shadow-md shadow-primary/20 hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]"
          >
            Get Started Free
            <ArrowRight className="w-4.5 h-4.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
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
