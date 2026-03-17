'use client';

import Link from 'next/link';
import { User, CreditCard, ChevronRight, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

const settingsLinks = [
  { href: '/settings/profile', label: 'Profile', description: 'Personal info, location, work authorization', icon: User, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  { href: '/settings/billing', label: 'Billing', description: 'Subscription plan and payment history', icon: CreditCard, color: 'text-cyan-400', bg: 'bg-cyan-500/10' },
];

export default function SettingsPage() {
  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-1">
          <div className="w-9 h-9 rounded-lg bg-muted flex items-center justify-center">
            <Settings className="w-4 h-4 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Settings</h1>
        </div>
        <p className="text-muted-foreground text-sm mt-1 ml-12">Account and billing</p>
      </div>

      <div className="space-y-3">
        {settingsLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="group bg-card rounded-2xl border border-border/50 p-5 hover:border-border transition-all flex items-center gap-4"
          >
            <div className={cn('w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0', link.bg)}>
              <link.icon className={cn('w-5 h-5', link.color)} />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors">{link.label}</h3>
              <p className="text-sm text-muted-foreground mt-0.5">{link.description}</p>
            </div>
            <ChevronRight className="w-5 h-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-all flex-shrink-0" />
          </Link>
        ))}
      </div>
    </div>
  );
}
