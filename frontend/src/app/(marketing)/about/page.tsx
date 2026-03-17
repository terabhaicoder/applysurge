'use client';

import Link from 'next/link';
import {
  ArrowRight,
  ArrowUpRight,
  Sparkles,
  Users,
  Target,
  Heart,
} from 'lucide-react';
import { LogoAppIcon } from '@/components/ui/logo';
import { useEffect, useState } from 'react';

const steps = [
  {
    num: '01',
    title: 'Upload your resume and set preferences',
    description:
      'Tell us what roles you are looking for, your preferred locations, and salary expectations.',
  },
  {
    num: '02',
    title: 'Connect your accounts',
    description:
      'Link your LinkedIn account so the agent can apply on your behalf using your profile data.',
  },
  {
    num: '03',
    title: 'Start the AI agent',
    description:
      'The agent finds matching jobs, applies automatically, and sends follow-up emails to hiring managers.',
  },
  {
    num: '04',
    title: 'Track and optimize',
    description:
      'Monitor your applications, response rates, and interview conversions from the dashboard.',
  },
];

const values = [
  {
    icon: Target,
    title: 'Efficiency First',
    description:
      'We believe in automating repetitive tasks so you can focus on what truly matters: preparing for the roles you want.',
  },
  {
    icon: Users,
    title: 'Equal Access',
    description:
      'Everyone deserves the same opportunities regardless of how much time they can dedicate to job searching.',
  },
  {
    icon: Heart,
    title: 'Human Touch',
    description:
      'Automation with personalization. Quality over quantity in every application we submit on your behalf.',
  },
];

export default function AboutPage() {
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
              <Link href="/features" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">
                Features
              </Link>
              <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors font-medium">
                Pricing
              </Link>
              <Link href="/about" className="text-sm text-primary font-semibold">
                About
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

      {/* Hero Section */}
      <section className="relative pt-36 lg:pt-44 pb-24 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-dot-pattern opacity-30 pointer-events-none" />
        <div className="absolute -top-40 right-1/4 w-[500px] h-[500px] bg-primary/[0.04] rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute -bottom-20 left-1/4 w-[400px] h-[400px] bg-accent/[0.03] rounded-full blur-[80px] pointer-events-none" />

        <div className="max-w-4xl mx-auto relative z-10 text-center">
          <div className="opacity-0 animate-slide-up inline-flex items-center gap-2.5 bg-primary/[0.06] border border-primary/10 px-4 py-2 rounded-full mb-8">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span className="text-xs font-semibold text-primary uppercase tracking-wider">
              Our Story
            </span>
          </div>

          <h1 className="opacity-0 animate-slide-up-delay-1 font-display text-4xl sm:text-5xl lg:text-[4rem] font-extrabold tracking-tight leading-[1.1]">
            About{' '}
            <span className="text-gradient">Apply Surge</span>
          </h1>

          <p className="opacity-0 animate-slide-up-delay-2 mt-6 text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            We are building tools to make job searching less painful and more productive for everyone.
          </p>
        </div>
      </section>

      {/* Story */}
      <section className="py-20 px-6 bg-secondary/30">
        <div className="max-w-3xl mx-auto">
          <div className="bg-card border border-border rounded-2xl p-8 md:p-10">
            <p className="text-base md:text-lg text-muted-foreground leading-relaxed mb-6">
              Apply Surge started from a simple frustration. As job seekers ourselves, we spent
              hours every day scrolling through job boards, filling out repetitive forms, and
              sending cold emails that rarely got responses. The process felt broken.
            </p>
            <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
              We built Apply Surge to automate the tedious parts of job searching while keeping
              the human touch where it matters. Our AI agent applies to jobs on your behalf,
              generates personalized cover letters, answers screening questions, and sends
              follow-up emails to hiring managers so you can focus on what actually matters:
              preparing for interviews.
            </p>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-24 px-6 relative">
        <div className="absolute inset-0 bg-dot-pattern opacity-20 pointer-events-none" />
        <div className="max-w-3xl mx-auto relative z-10 text-center">
          <span className="text-xs font-bold text-primary uppercase tracking-[0.15em] mb-3 block">
            Our Mission
          </span>
          <h2 className="font-display text-3xl md:text-[2.5rem] font-extrabold tracking-tight text-foreground mb-8">
            Leveling the playing field.
          </h2>
          <div className="bg-gradient-to-br from-primary/[0.06] to-accent/[0.03] border border-primary/10 rounded-2xl p-8 md:p-10">
            <p className="text-base md:text-lg text-muted-foreground leading-relaxed">
              Everyone deserves access to opportunities regardless of how much time
              they can spend on job searching. Apply Surge gives every
              job seeker the tools to apply at scale with the quality of a personal assistant.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-24 px-6 bg-secondary/30">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-14">
            <span className="text-xs font-bold text-primary uppercase tracking-[0.15em] mb-3 block">
              Our Values
            </span>
            <h2 className="font-display text-3xl md:text-[2.5rem] font-extrabold tracking-tight text-foreground">
              What we stand for.
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {values.map((value, i) => (
              <div
                key={i}
                className="group bg-card border border-border hover:border-primary/20 rounded-2xl p-7 text-center transition-all duration-300 hover:shadow-lg hover:shadow-primary/[0.04] hover:-translate-y-[2px]"
              >
                <div className="w-12 h-12 mx-auto mb-5 rounded-xl bg-primary/[0.08] flex items-center justify-center group-hover:bg-primary/[0.12] transition-colors">
                  <value.icon className="w-6 h-6 text-primary" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground mb-2 tracking-tight">
                  {value.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-6 relative">
        <div className="absolute inset-0 bg-dot-pattern opacity-20 pointer-events-none" />
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="text-center mb-14">
            <span className="text-xs font-bold text-primary uppercase tracking-[0.15em] mb-3 block">
              How It Works
            </span>
            <h2 className="font-display text-3xl md:text-[2.5rem] font-extrabold tracking-tight text-foreground">
              Four simple steps.
            </h2>
          </div>

          <div className="space-y-4">
            {steps.map((step, i) => (
              <div
                key={i}
                className="group flex gap-5 md:gap-6 items-start bg-card border border-border hover:border-primary/20 rounded-2xl p-6 transition-all duration-300 hover:shadow-md"
              >
                <div className="w-14 h-14 rounded-xl bg-primary/[0.06] border border-primary/10 flex items-center justify-center flex-shrink-0 group-hover:bg-primary/[0.1] transition-colors">
                  <span className="font-display text-lg font-bold text-primary">{step.num}</span>
                </div>
                <div>
                  <h3 className="font-display text-base font-bold text-foreground mb-1 tracking-tight">
                    {step.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
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
            Get started with 10 free applications. No credit card required.
          </p>

          <Link
            href="/register"
            className="group inline-flex items-center justify-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground px-9 py-4 rounded-xl text-base font-semibold transition-all duration-200 shadow-md shadow-primary/20 hover:shadow-lg hover:shadow-primary/25 hover:-translate-y-[1px]"
          >
            Get Started Free
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
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
                The autonomous AI agent that handles your entire job search pipeline.
              </p>
            </div>

            <div className="flex gap-16">
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                  Product
                </span>
                <Link href="/features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</Link>
                <Link href="/pricing" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Pricing</Link>
                <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors">About</Link>
              </div>
              <div className="flex flex-col gap-3">
                <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
                  Account
                </span>
                <Link href="/login" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Sign in</Link>
                <Link href="/register" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Get Started</Link>
              </div>
            </div>
          </div>

          <div className="mt-16 pt-8 border-t border-border flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Apply Surge. All rights reserved.
            </p>
            <div className="flex gap-6">
              <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">Privacy</span>
              <span className="text-xs text-muted-foreground hover:text-foreground cursor-pointer transition-colors">Terms</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
