'use client';

import { ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { EmailSettingsForm } from '@/components/settings/email-settings-form';

export default function EmailSettingsPage() {
  return (
    <div className="max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          href="/settings"
          className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Email Configuration</h1>
          <p className="text-muted-foreground text-sm mt-1">Set up email sending for outreach campaigns</p>
        </div>
      </div>
      <EmailSettingsForm />
    </div>
  );
}
