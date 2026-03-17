'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import { Mail, Send, Eye, Reply, AlertCircle, Plus, FileText, ArrowUpRight, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import { formatDate } from '@/lib/utils';

const statusConfig: Record<string, { bg: string; text: string; icon: typeof Send }> = {
  sent: { bg: 'bg-blue-400/10', text: 'text-blue-400', icon: Send },
  opened: { bg: 'bg-violet-400/10', text: 'text-violet-400', icon: Eye },
  replied: { bg: 'bg-emerald-400/10', text: 'text-emerald-400', icon: Reply },
  bounced: { bg: 'bg-red-400/10', text: 'text-red-400', icon: AlertCircle },
  delivered: { bg: 'bg-blue-400/10', text: 'text-blue-400', icon: Send },
};

export default function EmailsPage() {
  const { data: emailStats } = useQuery({
    queryKey: ['email-stats'],
    queryFn: () => api.get('/analytics/overview').then((r) => r.data),
  });

  const { data: applications, isLoading } = useQuery({
    queryKey: ['email-applications'],
    queryFn: () => api.get('/applications', { params: { method: 'cold_email', page_size: 20 } }).then((r) => r.data),
  });

  const emails = applications?.items || [];

  const stats = [
    { label: 'Total Sent', value: emailStats?.emails_sent || 0, color: 'text-blue-400', bg: 'bg-blue-400/10', icon: Send },
    { label: 'Opened', value: emailStats?.emails_opened || 0, color: 'text-violet-400', bg: 'bg-violet-400/10', icon: Eye },
    { label: 'Replied', value: emailStats?.emails_replied || 0, color: 'text-emerald-400', bg: 'bg-emerald-400/10', icon: Reply },
    { label: 'Reply Rate', value: emailStats?.emails_sent > 0 ? `${((emailStats?.emails_replied || 0) / emailStats.emails_sent * 100).toFixed(1)}%` : '0%', color: 'text-primary', bg: 'bg-primary/10', icon: Mail },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Email Outreach</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage your cold email campaigns</p>
        </div>
        <Link
          href="/emails/templates"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border border-border/50 rounded-xl hover:bg-secondary text-foreground transition-colors"
        >
          <FileText className="w-4 h-4" />
          Templates
          <ArrowUpRight className="w-3.5 h-3.5 text-muted-foreground" />
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-card rounded-2xl border border-border/50 p-5">
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-3', stat.bg)}>
              <stat.icon className={cn('w-5 h-5', stat.color)} />
            </div>
            <div className={cn('text-2xl font-bold', stat.color)}>{stat.value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Email List */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="flex items-center justify-between p-5 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
              <Mail className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="font-semibold text-foreground">Sent Emails</h2>
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-16 text-muted-foreground">
            <Loader2 className="w-5 h-5 animate-spin mr-2" />
            Loading emails...
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {emails.map((email: any) => {
              const status = email.email_opened ? 'opened' : email.email_replied ? 'replied' : 'sent';
              const config = statusConfig[status] || statusConfig.sent;
              return (
                <div key={email.id} className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors">
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-secondary rounded-full flex items-center justify-center">
                      <span className="text-sm font-semibold text-foreground">
                        {(email.email_sent_to || email.company_name || '?')[0].toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{email.email_sent_to || 'Unknown'}</p>
                      <p className="text-xs text-muted-foreground">{email.company_name} - {email.job_title}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className={cn('text-xs px-3 py-1.5 rounded-full font-medium flex items-center gap-1.5 capitalize', config.bg, config.text)}>
                      <config.icon className="w-3 h-3" />
                      {status}
                    </span>
                    <span className="text-xs text-muted-foreground hidden sm:block">
                      {email.applied_at ? formatDate(email.applied_at) : ''}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!isLoading && emails.length === 0 && (
          <div className="p-16 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-secondary flex items-center justify-center">
              <Mail className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="font-semibold text-foreground mb-2">No emails sent yet</h3>
            <p className="text-sm text-muted-foreground">Start a campaign to send cold emails to hiring managers</p>
          </div>
        )}
      </div>
    </div>
  );
}
