'use client';

import Link from 'next/link';
import { ArrowRight, ArrowUpRight, Check, Sparkles, Star } from 'lucide-react';
import { LogoAppIcon } from '@/components/ui/logo';
import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

const tiers = [
  {
    name: 'Free',
    price: 0,
    description: 'Get started with LinkedIn automation',
    features: [
      '10 applications per month',
      'AI-powered job matching',
      'LinkedIn Easy Apply',
      'AI screening answers',
      'Application tracking',
    ],
    cta: 'Get Started Free',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: 29,
    description: 'For serious job seekers',
    features: [
      'Unlimited applications',
      'Advanced AI matching',
      'Priority job discovery',
      'Cover letter generation',
      'Resume optimization',
      'Priority support',
      'Full analytics dashboard',
    ],
    cta: 'Coming Soon',
    highlighted: true,
    comingSoon: true,
  },
];

const faqs = [
  {
    q: 'How does Apply Surge work?',
    a: 'Apply Surge uses an AI agent to scan LinkedIn for matching jobs, fill out Easy Apply forms, answer screening questions using your resume, and submit applications automatically.',
  },
  {
    q: 'What happens when I reach my free limit?',
    a: 'The agent will pause once you reach 10 applications per month. The Pro plan with unlimited applications is coming soon.',
  },
  {
    q: 'Is my data secure?',
    a: 'All credentials are encrypted using AES-256 encryption. We never share your data with third parties. Your LinkedIn credentials are only used for Easy Apply automation.',
  },
  {
    q: 'When will the Pro plan launch?',
    a: 'The Pro plan is coming soon. Start with the free plan now and you will get early access when Pro launches.',
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
      {/* Navigation */}
      <nav className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        isScrolled ? 'bg-background/80 backdrop-blur-xl border-b border-border shadow-sm' : 'bg-transparent'
      )}>
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <Link href="/" className="flex items-center gap-2.5">
              <LogoAppIcon size={28} />
              <span className="text-lg font-display font-bold tracking-tight text-foreground">Apply Surge</span>
            </Link>
            <div className="hidden md:flex items-center gap-8">
              <a href="/#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">Features</a>
              <a href="/#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">How It Works</a>
              <Link href="/pricing" className="text-sm text-primary font-semibold">Pricing</Link>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/login" className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors hidden sm:block">Sign In</Link>
              <Link href="/register" className="text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 px-5 py-2 rounded-lg transition-all shadow-sm flex items-center gap-1.5">
                Get Started <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative pt-36 lg:pt-44 pb-20 px-6">
        <div className="absolute -top-40 left-1/4 w-[500px] h-[500px] bg-primary/[0.04] rounded-full blur-[100px] pointer-events-none" />
        <div className="max-w-4xl mx-auto relative z-10 text-center">
          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1]">
            Simple, transparent <span className="text-gradient">pricing.</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-xl mx-auto leading-relaxed">
            Start automating your job search for free. Upgrade when you need more.
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-24 px-6">
        <div className="max-w-3xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {tiers.map((tier, i) => (
              <div
                key={i}
                className={cn(
                  'relative bg-card border rounded-2xl p-8 transition-all duration-300',
                  tier.highlighted
                    ? 'border-primary/40 shadow-xl shadow-primary/[0.08]'
                    : 'border-border hover:border-primary/15 hover:shadow-md'
                )}
              >
                {tier.highlighted && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-primary text-primary-foreground text-xs font-bold rounded-full shadow-lg shadow-primary/25">
                      <Sparkles className="w-3 h-3" /> Popular
                    </span>
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="font-display text-xl font-bold text-foreground">{tier.name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">{tier.description}</p>
                </div>

                <div className="mb-8">
                  <div className="flex items-baseline gap-1">
                    <span className="font-display text-5xl font-extrabold text-foreground tracking-tight">
                      ${tier.price}
                    </span>
                    {tier.price > 0 && <span className="text-muted-foreground text-sm">/month</span>}
                  </div>
                </div>

                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, j) => (
                    <li key={j} className="flex items-center gap-2.5 text-sm text-muted-foreground">
                      <div className="w-5 h-5 rounded-full bg-emerald-500/10 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-emerald-500" />
                      </div>
                      {feature}
                    </li>
                  ))}
                </ul>

                {tier.comingSoon ? (
                  <div className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm border border-border text-muted-foreground cursor-not-allowed opacity-60">
                    Coming Soon
                  </div>
                ) : (
                  <Link
                    href="/register"
                    className="w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm transition-all bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/20 hover:shadow-lg"
                  >
                    {tier.cta} <ArrowRight className="w-4 h-4" />
                  </Link>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-6 bg-secondary/30">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-14">
            <h2 className="font-display text-3xl md:text-4xl font-extrabold tracking-tight text-foreground">
              Frequently asked questions
            </h2>
          </div>
          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <div key={i} className="bg-card border border-border rounded-2xl p-6 hover:border-primary/15 transition-colors">
                <h3 className="font-display font-bold text-foreground mb-2">{faq.q}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-24 px-6">
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight mb-6 text-foreground">
            Ready to automate <span className="text-gradient">your job search?</span>
          </h2>
          <p className="text-muted-foreground text-lg mb-10 max-w-xl mx-auto leading-relaxed">
            Start applying to jobs on autopilot. Free to get started.
          </p>
          <Link
            href="/register"
            className="group inline-flex items-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground px-9 py-4 rounded-xl text-base font-semibold transition-all shadow-md shadow-primary/20 hover:shadow-lg"
          >
            Get Started Free <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} Augustinnovate Pvt. Ltd. All rights reserved.
          </p>
          <div className="flex gap-6">
            <a href="/#features" className="text-xs text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <Link href="/pricing" className="text-xs text-muted-foreground hover:text-foreground transition-colors">Pricing</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
