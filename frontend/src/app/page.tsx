'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';
import {
  ArrowRight,
  Upload,
  Bot,
  BarChart3,
  Terminal,
  CheckCircle2,
  Loader2,
  FileText,
  Zap,
  Shield,
  ChevronDown,
  Play,
} from 'lucide-react';
import { LogoFull } from '@/components/ui/logo';
import { ThemeToggle } from '@/components/ui/theme-toggle';
import { cn } from '@/lib/utils';

/* ─── FAQ Data ─── */
const faqs = [
  {
    q: 'How does Apply Surge automate job applications?',
    a: 'Apply Surge uses an AI-powered agent that scans job boards like LinkedIn, matches roles to your profile and preferences, fills out application forms, answers screening questions using your resume context, and submits applications automatically while you focus on interview prep.',
  },
  {
    q: 'Is my data safe and private?',
    a: 'Absolutely. Your resume, credentials, and personal data are encrypted at rest and in transit. We never share your information with third parties. You can delete your data at any time from your account settings.',
  },
  {
    q: 'What job boards does Apply Surge support?',
    a: 'Currently, Apply Surge supports LinkedIn Easy Apply with deep automation. We are actively working on expanding to additional platforms including Indeed, Glassdoor, and direct company career pages.',
  },
  {
    q: 'Can I control which jobs the agent applies to?',
    a: 'Yes. You set your preferences including target roles, locations, salary range, remote preferences, and a minimum match score. The agent only applies to jobs that meet your criteria. You can also review and approve jobs before the agent submits.',
  },
  {
    q: 'How accurate is the AI when answering screening questions?',
    a: 'The AI references your resume, work history, and stated preferences to generate tailored answers for standard screening questions. You can review past answers in your dashboard and fine-tune the AI\'s responses.',
  },
];

/* ─── Main Page ─── */
export default function LandingPage() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* ─── Navigation ─── */}
      <nav
        className={cn(
          'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
          isScrolled
            ? 'bg-background/70 backdrop-blur-xl border-b border-border/50 shadow-sm'
            : 'bg-transparent'
        )}
      >
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex justify-between items-center h-16">
            <Link href="/">
              <LogoFull iconSize={26} />
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <Link
                href="/features"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Features
              </Link>
              <Link
                href="/pricing"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                Pricing
              </Link>
              <Link
                href="/about"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                About
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <ThemeToggle />
              <Link
                href="/login"
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors hidden sm:block"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="text-sm font-semibold text-primary-foreground bg-primary hover:bg-primary/90 px-5 py-2 rounded-lg transition-all duration-200 shadow-sm shadow-primary/20"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative pt-36 lg:pt-48 pb-24 lg:pb-32 px-6">
        {/* Background effects */}
        <div className="absolute inset-0 bg-dot-pattern opacity-[0.03] pointer-events-none" />
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[600px] bg-primary/[0.05] rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-20 right-[10%] w-[400px] h-[400px] bg-accent/[0.04] rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-5xl mx-auto relative z-10">
          <div className="flex flex-col items-center text-center">
            {/* Headline */}
            <h1 className="opacity-0 animate-slide-up-delay-1 font-display text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold leading-[1.03] tracking-tight max-w-5xl">
              Your job search,{' '}
              <span className="text-gradient-hero">fully automated.</span>
            </h1>

            <p className="opacity-0 animate-slide-up-delay-2 mt-7 text-lg md:text-xl text-muted-foreground max-w-2xl leading-relaxed font-body">
              Apply Surge discovers matching jobs, fills out applications, and
              answers screening questions so you can focus on interview
              prep.
            </p>

            {/* CTA buttons */}
            <div className="opacity-0 animate-slide-up-delay-3 mt-12 flex flex-col sm:flex-row items-center gap-4">
              <Link
                href="/register"
                className="group inline-flex items-center gap-2.5 bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3.5 rounded-xl text-[15px] font-semibold transition-all duration-200 shadow-lg shadow-primary/25 hover:shadow-xl hover:shadow-primary/30 hover:-translate-y-0.5"
              >
                Get Started Free
                <ArrowRight className="w-4.5 h-4.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <Link
                href="#demo"
                className="group inline-flex items-center gap-2.5 border border-border hover:border-primary/30 text-foreground px-9 py-4 rounded-xl text-base font-medium transition-all duration-200 hover:bg-primary/[0.04]"
              >
                <Play className="w-4 h-4 text-primary" />
                See It in Action
              </Link>
            </div>

            {/* Dashboard Mockup */}
            <div className="opacity-0 animate-slide-up-delay-4 mt-20 w-full max-w-4xl">
              <div className="rounded-2xl border border-border/60 bg-card shadow-2xl shadow-black/[0.08] dark:shadow-black/30 overflow-hidden">
                {/* Browser chrome */}
                <div className="flex items-center gap-3 px-5 py-3 border-b border-border/50 bg-secondary/30">
                  <div className="flex gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-400/60" />
                    <div className="w-3 h-3 rounded-full bg-yellow-400/60" />
                    <div className="w-3 h-3 rounded-full bg-green-400/60" />
                  </div>
                  <div className="flex-1 mx-4">
                    <div className="h-7 rounded-md bg-secondary/80 flex items-center justify-center">
                      <span className="text-xs text-muted-foreground/60 font-mono">
                        app.applysurge.com/dashboard
                      </span>
                    </div>
                  </div>
                </div>
                {/* Dashboard content mockup */}
                <div className="p-6 bg-gradient-to-br from-primary/[0.02] to-accent/[0.03] min-h-[280px] md:min-h-[340px]">
                  <div className="grid grid-cols-3 gap-4 mb-6">
                    {[
                      { label: 'Applications', value: '47', color: 'bg-primary/10 text-primary' },
                      { label: 'Interviews', value: '12', color: 'bg-emerald-500/10 text-emerald-600' },
                      { label: 'Match Rate', value: '94%', color: 'bg-accent/10 text-accent' },
                    ].map((stat, i) => (
                      <div
                        key={i}
                        className="rounded-xl bg-card border border-border/40 p-4"
                      >
                        <div className={cn('text-2xl md:text-3xl font-display font-bold', stat.color)}>
                          {stat.value}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {stat.label}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-3">
                    {[
                      { role: 'Senior Frontend Engineer', company: 'Vercel', status: 'Applied', statusColor: 'bg-primary/10 text-primary' },
                      { role: 'Full Stack Developer', company: 'Linear', status: 'Interview', statusColor: 'bg-emerald-500/10 text-emerald-600' },
                      { role: 'Software Engineer', company: 'Stripe', status: 'Applied', statusColor: 'bg-primary/10 text-primary' },
                    ].map((job, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between rounded-lg bg-card border border-border/30 px-4 py-3"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
                            <span className="text-xs font-bold text-muted-foreground">
                              {job.company[0]}
                            </span>
                          </div>
                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {job.role}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              {job.company}
                            </div>
                          </div>
                        </div>
                        <span className={cn('text-xs font-medium px-2.5 py-1 rounded-full', job.statusColor)}>
                          {job.status}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section className="py-24 lg:py-32 px-6 relative">
        <div className="absolute inset-0 bg-dot-pattern opacity-[0.02] pointer-events-none" />
        <div className="max-w-5xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight text-foreground">
              Everything you need to{' '}
              <span className="text-gradient">land interviews</span>
            </h2>
            <p className="mt-5 text-muted-foreground max-w-xl mx-auto text-lg">
              From discovery to submission, the agent handles the entire
              application pipeline.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Zap,
                title: 'One-click automated applications',
                desc: 'Hit start and the agent applies to dozens of matching jobs on LinkedIn. No manual form filling, no copy-pasting your resume.',
              },
              {
                icon: Shield,
                title: 'AI answers screening questions',
                desc: 'The agent reads each question, references your resume and preferences, and writes tailored answers that pass screening filters.',
              },
              {
                icon: BarChart3,
                title: 'Track & optimize everything',
                desc: "Every application is logged with status, match score, and timeline. See what's working and adjust your strategy in real time.",
              },
            ].map((item, i) => (
              <div
                key={i}
                className="group bg-card border border-border/50 rounded-2xl p-8 hover:border-primary/20 hover:shadow-xl hover:shadow-primary/[0.06] transition-all duration-300 hover:-translate-y-1"
              >
                <div className="w-12 h-12 bg-primary/[0.08] rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary/[0.14] transition-colors">
                  <item.icon className="w-5.5 h-5.5 text-primary" />
                </div>
                <h3 className="font-display text-lg font-bold text-foreground mb-3 tracking-tight">
                  {item.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section className="py-24 lg:py-32 px-6 bg-secondary/30 relative">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight text-foreground">
              How it works
            </h2>
            <p className="mt-5 text-muted-foreground max-w-lg mx-auto text-lg">
              Three steps. Five minutes of setup. Then let the agent work.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connecting line (desktop only) */}
            <div className="hidden md:block absolute top-[3.5rem] left-[20%] right-[20%] h-px bg-gradient-to-r from-primary/10 via-primary/30 to-primary/10" />

            {[
              {
                icon: Upload,
                step: '01',
                title: 'Upload resume & set preferences',
                desc: 'Add your resume, target roles, locations, and salary expectations. The agent learns exactly what you want.',
              },
              {
                icon: Bot,
                step: '02',
                title: 'Agent discovers & applies',
                desc: 'It scans LinkedIn for matching jobs, fills out every field, and answers screening questions automatically.',
              },
              {
                icon: BarChart3,
                step: '03',
                title: 'Track & land interviews',
                desc: 'Monitor every application in your dashboard. You handle the interviews, the agent handles the pipeline.',
              },
            ].map((item, i) => (
              <div
                key={i}
                className="group relative bg-card border border-border/50 rounded-2xl p-8 hover:border-primary/20 hover:shadow-xl hover:shadow-primary/[0.06] transition-all duration-300 hover:-translate-y-1"
              >
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-12 h-12 bg-primary/[0.08] rounded-xl flex items-center justify-center group-hover:bg-primary/[0.14] transition-colors relative z-10">
                    <item.icon className="w-5 h-5 text-primary" />
                  </div>
                  <span className="font-display text-5xl font-extrabold text-primary/[0.08] select-none">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-display text-lg font-bold text-foreground mb-3 tracking-tight">
                  {item.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {item.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Terminal Demo ─── */}
      <section id="demo" className="py-24 lg:py-32 px-6 bg-secondary/30 relative">
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="text-center mb-14">
            <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight text-foreground">
              See the agent in action
            </h2>
            <p className="mt-5 text-muted-foreground max-w-lg mx-auto text-lg">
              Watch Apply Surge scan jobs, fill forms, and submit applications
              in real time.
            </p>
          </div>

          <TerminalDemo />
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section className="py-24 lg:py-32 px-6 relative">
        <div className="max-w-3xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-5xl font-extrabold tracking-tight text-foreground">
              Frequently asked questions
            </h2>
            <p className="mt-5 text-muted-foreground text-lg">
              Everything you need to know about Apply Surge.
            </p>
          </div>

          <div className="space-y-3">
            {faqs.map((faq, i) => (
              <div
                key={i}
                className="border border-border/50 rounded-xl overflow-hidden bg-card transition-colors hover:border-primary/10"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left"
                >
                  <span className="font-display font-semibold text-foreground text-[15px]">
                    {faq.q}
                  </span>
                  <ChevronDown
                    className={cn(
                      'w-5 h-5 text-muted-foreground shrink-0 transition-transform duration-200',
                      openFaq === i && 'rotate-180'
                    )}
                  />
                </button>
                <div
                  className={cn(
                    'overflow-hidden transition-all duration-300 ease-in-out',
                    openFaq === i ? 'max-h-60 opacity-100' : 'max-h-0 opacity-0'
                  )}
                >
                  <p className="px-6 pb-5 text-sm text-muted-foreground leading-relaxed">
                    {faq.a}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Final CTA ─── */}
      <section className="py-24 lg:py-32 px-6 relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/[0.06] via-accent/[0.04] to-transparent pointer-events-none" />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-primary/[0.05] rounded-full blur-[120px] pointer-events-none" />

        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight mb-6 text-foreground">
            Stop applying manually.
          </h2>
          <p className="text-muted-foreground mb-10 max-w-xl mx-auto text-lg leading-relaxed">
            Let the agent handle the grind. You focus on preparing for the
            interviews that land.
          </p>
          <Link
            href="/register"
            className="group inline-flex items-center gap-2.5 bg-white text-indigo-600 hover:bg-white/90 font-semibold text-base px-10 py-4 rounded-xl transition-all duration-200 shadow-xl shadow-black/10 hover:-translate-y-0.5"
          >
            Get Started Free
            <ArrowRight className="w-4.5 h-4.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-border/50 pt-16 pb-10 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-10 mb-14">
            {/* Brand */}
            <div className="col-span-2">
              <LogoFull iconSize={24} />
              <p className="mt-4 text-sm text-muted-foreground max-w-xs leading-relaxed">
                AI-powered job application automation. Apply to hundreds of
                matching roles while you focus on what matters.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-display font-semibold text-sm text-foreground mb-4">
                Product
              </h4>
              <ul className="space-y-3">
                {['Features', 'Pricing', 'Changelog'].map((item) => (
                  <li key={item}>
                    <Link
                      href={`/${item.toLowerCase()}`}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="font-display font-semibold text-sm text-foreground mb-4">
                Company
              </h4>
              <ul className="space-y-3">
                {['About', 'Blog', 'Careers'].map((item) => (
                  <li key={item}>
                    <Link
                      href={`/${item.toLowerCase()}`}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-display font-semibold text-sm text-foreground mb-4">
                Legal
              </h4>
              <ul className="space-y-3">
                {['Privacy', 'Terms'].map((item) => (
                  <li key={item}>
                    <Link
                      href={`/${item.toLowerCase()}`}
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {item}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="border-t border-border/50 pt-8 flex flex-col sm:flex-row justify-between items-center gap-4">
            <p className="text-xs text-muted-foreground">
              &copy; {new Date().getFullYear()} Apply Surge. All rights
              reserved. Built by{' '}
              <a
                href="https://paarthpanthri.com"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
              >
                Paarth Panthri
              </a>
              .
            </p>
            <div className="flex items-center gap-6">
              {/* Twitter / X */}
              <a
                href="https://twitter.com/applysurge"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="Twitter"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
              </a>
              {/* GitHub */}
              <a
                href="https://github.com/applysurge"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="GitHub"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  />
                </svg>
              </a>
              {/* LinkedIn */}
              <a
                href="https://linkedin.com/company/applysurge"
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
                aria-label="LinkedIn"
              >
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

/* ─── Terminal Demo Component ─── */
function TerminalDemo() {
  const [step, setStep] = useState(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const lines = [
    { type: 'cmd', text: '$ applysurge start --resume resume.pdf' },
    { type: 'info', text: 'Scanning LinkedIn for matching roles...' },
    { type: 'success', text: 'Found 23 jobs matching your profile' },
    { type: 'apply', text: 'Applying -> Senior Frontend Engineer at Vercel' },
    { type: 'detail', text: '  Filling form fields... done' },
    { type: 'detail', text: '  Answering screening questions... done' },
    { type: 'success', text: 'Application submitted' },
    { type: 'apply', text: 'Applying -> Full Stack Developer at Linear' },
    { type: 'detail', text: '  Filling form fields... done' },
    { type: 'success', text: 'Application submitted' },
    { type: 'info', text: 'Session complete: 2 of 23 applications sent' },
  ];

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      setStep((prev) => (prev >= lines.length - 1 ? 0 : prev + 1));
    }, 1600);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [lines.length]);

  const visibleLines = lines.slice(0, step + 1);

  return (
    <div className="rounded-2xl border border-border/60 bg-card overflow-hidden shadow-2xl shadow-black/[0.12] dark:shadow-black/40">
      {/* Terminal header */}
      <div className="flex items-center gap-3 px-5 py-3.5 border-b border-border/50 bg-secondary/40">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-400/60" />
          <div className="w-3 h-3 rounded-full bg-yellow-400/60" />
          <div className="w-3 h-3 rounded-full bg-green-400/60" />
        </div>
        <div className="flex items-center gap-2 ml-2">
          <Terminal className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="terminal-text text-xs text-muted-foreground">
            apply-surge
          </span>
        </div>
      </div>

      {/* Terminal body */}
      <div className="p-6 terminal-text text-[13px] leading-relaxed min-h-[300px] max-h-[360px] overflow-hidden">
        {visibleLines.map((line, i) => (
          <div
            key={`${i}-${line.text}`}
            className="flex items-start gap-2.5 mb-1.5 animate-in fade-in-0"
            style={{ animationDuration: '300ms' }}
          >
            {line.type === 'cmd' && (
              <span className="text-foreground">{line.text}</span>
            )}
            {line.type === 'info' && (
              <>
                <Loader2 className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0 animate-spin" />
                <span className="text-muted-foreground">{line.text}</span>
              </>
            )}
            {line.type === 'success' && (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" />
                <span className="text-emerald-500">{line.text}</span>
              </>
            )}
            {line.type === 'apply' && (
              <>
                <FileText className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                <span className="text-foreground font-medium">{line.text}</span>
              </>
            )}
            {line.type === 'detail' && (
              <span className="text-muted-foreground/70 ml-6">
                {line.text}
              </span>
            )}
          </div>
        ))}
        {/* Blinking cursor */}
        {step < lines.length - 1 && (
          <div className="flex items-center gap-2 mt-1">
            <span className="text-primary font-bold">$</span>
            <span className="w-2 h-4 bg-primary/70 animate-terminal-cursor" />
          </div>
        )}
      </div>
    </div>
  );
}
