'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrendingUp, Briefcase, MessageSquare, Calendar, Send, ChevronRight, BarChart3 } from 'lucide-react';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const { data: overview } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: () => api.get('/analytics/overview').then((r) => r.data),
  });

  const { data: daily } = useQuery({
    queryKey: ['analytics-daily', period],
    queryFn: () => api.get('/analytics/daily', { params: { days: period === '7d' ? 7 : period === '30d' ? 30 : 90 } }).then((r) => r.data),
  });

  const { data: sources } = useQuery({
    queryKey: ['analytics-sources'],
    queryFn: () => api.get('/analytics/sources').then((r) => r.data),
  });

  const stats = [
    { label: 'Total Applications', value: overview?.total_applications || 0, icon: Briefcase, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'Response Rate', value: `${overview?.response_rate || 0}%`, icon: MessageSquare, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
    { label: 'Interviews', value: overview?.interviews || 0, icon: Calendar, color: 'text-violet-400', bg: 'bg-violet-400/10' },
    { label: 'Emails Sent', value: overview?.emails_sent || 0, icon: Send, color: 'text-pink-400', bg: 'bg-pink-400/10' },
    { label: 'Open Rate', value: `${overview?.email_open_rate || 0}%`, icon: TrendingUp, color: 'text-primary', bg: 'bg-primary/10' },
  ];

  const sourceData = [
    { source: 'LinkedIn Easy Apply', count: sources?.linkedin || 0, color: 'bg-blue-400' },
    { source: 'Naukri Apply', count: sources?.naukri || 0, color: 'bg-emerald-400' },
    { source: 'Cold Email', count: sources?.cold_email || 0, color: 'bg-violet-400' },
    { source: 'Startup Outreach', count: sources?.startup || 0, color: 'bg-amber-400' },
  ];

  const total = sourceData.reduce((acc, s) => acc + s.count, 0) || 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Analytics</h1>
          <p className="text-muted-foreground text-sm mt-1">Track your job search performance</p>
        </div>
        <div className="flex gap-1 bg-card border border-border/50 p-1 rounded-xl">
          {(['7d', '30d', '90d'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'px-4 py-2 text-sm rounded-lg font-medium transition-all',
                period === p
                  ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {p === '7d' ? '7 Days' : p === '30d' ? '30 Days' : '90 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-card rounded-2xl border border-border/50 p-5">
            <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center mb-3', stat.bg)}>
              <stat.icon className={cn('w-5 h-5', stat.color)} />
            </div>
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Charts Area */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Applications Over Time */}
        <div className="bg-card rounded-2xl border border-border/50 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-blue-400" />
            </div>
            <h3 className="font-semibold text-foreground">Applications Over Time</h3>
          </div>
          <div className="h-48 flex items-end gap-1">
            {(daily?.items || Array.from({ length: 14 })).map((day: any, i: number) => {
              const value = day?.applications_successful || Math.floor(Math.random() * 10);
              const maxVal = Math.max(...(daily?.items || []).map((d: any) => d?.applications_successful || 0), 10);
              const height = Math.max(8, (value / maxVal) * 100);
              return (
                <div key={i} className="flex-1 flex flex-col items-center group">
                  <div
                    className="w-full bg-gradient-to-t from-primary to-primary/80 rounded-t hover:from-primary/80 hover:to-primary/70 transition-all cursor-pointer"
                    style={{ height: `${height}%` }}
                    title={`${value} applications`}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-3 text-xs text-muted-foreground">
            <span>{period === '7d' ? '7 days ago' : period === '30d' ? '30 days ago' : '90 days ago'}</span>
            <span>Today</span>
          </div>
        </div>

        {/* Source Breakdown */}
        <div className="bg-card rounded-2xl border border-border/50 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 rounded-lg bg-violet-400/10 flex items-center justify-center">
              <Briefcase className="w-4 h-4 text-violet-400" />
            </div>
            <h3 className="font-semibold text-foreground">Applications by Source</h3>
          </div>
          <div className="space-y-4">
            {sourceData.map((item) => {
              const pct = Math.round((item.count / total) * 100);
              return (
                <div key={item.source}>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-foreground">{item.source}</span>
                    <span className="text-muted-foreground">{item.count} ({pct}%)</span>
                  </div>
                  <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <div className={cn('h-full rounded-full transition-all', item.color)} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Response Funnel */}
      <div className="bg-card rounded-2xl border border-border/50 p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-8 h-8 rounded-lg bg-emerald-400/10 flex items-center justify-center">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <h3 className="font-semibold text-foreground">Response Funnel</h3>
        </div>
        <div className="flex items-center justify-between">
          {[
            { label: 'Applied', value: overview?.total_applications || 0, color: 'text-blue-400', bg: 'bg-blue-400/10' },
            { label: 'Responses', value: overview?.total_responses || 0, color: 'text-emerald-400', bg: 'bg-emerald-400/10' },
            { label: 'Interviews', value: overview?.interviews || 0, color: 'text-violet-400', bg: 'bg-violet-400/10' },
            { label: 'Offers', value: overview?.offers || 0, color: 'text-primary', bg: 'bg-primary/10' },
          ].map((step, i) => (
            <div key={step.label} className="flex items-center gap-4 flex-1">
              <div className="flex-1 text-center">
                <div className={cn('inline-block px-6 py-4 rounded-2xl', step.bg)}>
                  <div className={cn('text-2xl font-bold', step.color)}>{step.value}</div>
                  <div className="text-xs text-muted-foreground mt-1">{step.label}</div>
                </div>
              </div>
              {i < 3 && (
                <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
