'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Briefcase,
  MessageSquare,
  Send,
  Calendar,
  Play,
  Pause,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Check,
  AlertCircle,
  Inbox,
} from 'lucide-react';
import Link from 'next/link';
import { useAgent } from '@/hooks/use-agent';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { status: agentData, start, stop, isLoading: agentLoading } = useAgent();
  const isAgentRunning = agentData?.is_running === true;

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/analytics/overview').then((r) => r.data),
  });

  const { data: recentApps } = useQuery({
    queryKey: ['recent-applications'],
    queryFn: () => api.get('/applications', { params: { limit: 5 } }).then((r) => r.data),
  });

  const { data: resumes } = useQuery({
    queryKey: ['setup-resumes'],
    queryFn: () => api.get('/resumes').then((r) => r.data),
  });

  const { data: preferences } = useQuery({
    queryKey: ['setup-preferences'],
    queryFn: () => api.get('/preferences').then((r) => r.data),
  });

  const { data: credentials } = useQuery({
    queryKey: ['setup-credentials'],
    queryFn: () => api.get('/credentials').then((r) => r.data),
  });

  const hasResume = Array.isArray(resumes) ? resumes.length > 0 : Boolean(resumes?.items?.length);
  const hasPreferences = Boolean(preferences?.desired_titles?.length);
  const hasLinkedIn = Array.isArray(credentials)
    ? credentials.some((c: any) => c.platform === 'linkedin')
    : Boolean(credentials?.items?.some?.((c: any) => c.platform === 'linkedin'));

  const setupItems = [
    { label: 'Upload your resume', done: hasResume, href: '/resume' },
    { label: 'Set job preferences', done: hasPreferences, href: '/preferences' },
    { label: 'Connect LinkedIn', done: hasLinkedIn, href: '/connections' },
  ];

  const completedCount = setupItems.filter((i) => i.done).length;

  const statCards = [
    {
      label: 'Applications',
      value: stats?.total_applications ?? 0,
      change: stats?.applications_change ?? 0,
      icon: Briefcase,
      gradient: 'from-indigo-500 to-indigo-600',
      iconBg: 'bg-indigo-500/10 text-indigo-500',
    },
    {
      label: 'Responses',
      value: stats?.total_responses ?? 0,
      change: stats?.responses_change ?? 0,
      icon: MessageSquare,
      gradient: 'from-emerald-500 to-emerald-600',
      iconBg: 'bg-emerald-500/10 text-emerald-500',
    },
    {
      label: 'Emails Sent',
      value: stats?.emails_sent ?? 0,
      change: stats?.emails_change ?? 0,
      icon: Send,
      gradient: 'from-violet-500 to-violet-600',
      iconBg: 'bg-violet-500/10 text-violet-500',
    },
    {
      label: 'Interviews',
      value: stats?.interviews ?? 0,
      change: stats?.interviews_change ?? 0,
      icon: Calendar,
      gradient: 'from-amber-500 to-amber-600',
      iconBg: 'bg-amber-500/10 text-amber-500',
    },
  ];

  const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
    applied: { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
    response_received: { bg: 'bg-emerald-500/10', text: 'text-emerald-500', dot: 'bg-emerald-500' },
    interview_scheduled: { bg: 'bg-violet-500/10', text: 'text-violet-500', dot: 'bg-violet-500' },
    failed: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
    pending: { bg: 'bg-secondary', text: 'text-muted-foreground', dot: 'bg-muted-foreground' },
  };

  const applications = recentApps?.items ?? [];
  const hasApplications = applications.length > 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground/80 text-sm mt-1">Your job search at a glance</p>
      </div>

      {/* Agent Status Card */}
      <div
        className={cn(
          'relative rounded-2xl border p-6 transition-all duration-300 overflow-hidden',
          isAgentRunning
            ? 'bg-primary/[0.03] border-primary/20 shadow-sm shadow-primary/5'
            : 'bg-card border-border/40 shadow-sm'
        )}
      >
        {/* Background gradient when running */}
        {isAgentRunning && (
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/[0.04] via-transparent to-violet-500/[0.04] pointer-events-none" />
        )}

        <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="relative flex items-center justify-center">
              <div
                className={cn(
                  'w-3 h-3 rounded-full transition-colors duration-300',
                  isAgentRunning ? 'bg-emerald-500' : 'bg-muted-foreground/40'
                )}
              />
              {isAgentRunning && (
                <div className="absolute inset-0 w-3 h-3 rounded-full bg-emerald-500 animate-ping opacity-75" />
              )}
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {isAgentRunning ? 'Agent Running' : 'Agent Stopped'}
              </h2>
              <p className="text-sm text-muted-foreground/80">
                {isAgentRunning
                  ? 'Actively searching and applying to jobs on your behalf'
                  : 'Start the agent to automatically discover and apply to jobs'}
              </p>
            </div>
          </div>

          {isAgentRunning ? (
            <button
              onClick={stop}
              disabled={agentLoading}
              className="px-5 py-2.5 text-sm font-medium border border-border/60 rounded-xl hover:bg-secondary/60 text-foreground flex items-center gap-2 transition-all duration-200 disabled:opacity-50 shrink-0"
            >
              <Pause className="w-4 h-4" />
              Pause
            </button>
          ) : (
            <button
              onClick={start}
              disabled={agentLoading}
              className="px-6 py-2.5 text-sm font-medium bg-primary hover:bg-primary/90 text-primary-foreground rounded-xl flex items-center gap-2 transition-all duration-200 shadow-md shadow-primary/20 hover:shadow-lg hover:shadow-primary/25 disabled:opacity-50 shrink-0"
            >
              <Play className="w-4 h-4" />
              Start Agent
            </button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <div
            key={stat.label}
            className="group bg-card rounded-2xl border border-border/40 p-5 shadow-sm hover:shadow-md transition-all duration-300"
          >
            <div className="flex items-center justify-between mb-4">
              <div
                className={cn(
                  'w-10 h-10 rounded-xl flex items-center justify-center transition-colors duration-200',
                  stat.iconBg
                )}
              >
                <stat.icon className="w-[18px] h-[18px]" />
              </div>
              {stat.change !== 0 && (
                <span
                  className={cn(
                    'text-xs font-medium flex items-center gap-1 px-2 py-1 rounded-full',
                    stat.change > 0
                      ? 'text-emerald-500 bg-emerald-500/10'
                      : 'text-red-500 bg-red-500/10'
                  )}
                >
                  {stat.change > 0 ? (
                    <TrendingUp className="w-3 h-3" />
                  ) : (
                    <TrendingDown className="w-3 h-3" />
                  )}
                  {Math.abs(stat.change)}%
                </span>
              )}
            </div>
            <div className="text-3xl font-bold text-foreground tracking-tight">{stat.value}</div>
            <div className="text-sm text-muted-foreground/70 mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Applications (2/3 or full width when setup complete) */}
        <div className={cn(completedCount === setupItems.length ? 'lg:col-span-3' : 'lg:col-span-2', 'bg-card rounded-2xl border border-border/40 overflow-hidden shadow-sm')}>
          <div className="flex items-center justify-between p-5 border-b border-border/30">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-indigo-500" />
              </div>
              <h2 className="font-semibold text-foreground">Recent Applications</h2>
            </div>
            {hasApplications && (
              <Link
                href="/applications"
                className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors duration-200 group"
              >
                View all
                <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform duration-200" />
              </Link>
            )}
          </div>

          {hasApplications ? (
            <div className="divide-y divide-border/30">
              {applications.slice(0, 5).map((app: any) => {
                const config = statusConfig[app.status] || statusConfig.pending;
                return (
                  <div
                    key={app.id}
                    className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors duration-200"
                  >
                    <div className="flex items-center gap-4 min-w-0">
                      <div className="w-10 h-10 bg-secondary/60 rounded-xl flex items-center justify-center shrink-0">
                        <span className="text-sm font-semibold text-foreground/80">
                          {app.company_name?.charAt(0) || 'J'}
                        </span>
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {app.job_title}
                        </p>
                        <p className="text-xs text-muted-foreground/70 truncate">
                          {app.company_name}
                        </p>
                      </div>
                    </div>
                    <span
                      className={cn(
                        'text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1.5 shrink-0 ml-3',
                        config.bg,
                        config.text
                      )}
                    >
                      <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
                      {app.status?.replace(/_/g, ' ')}
                    </span>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-14 flex flex-col items-center text-center">
              <div className="w-14 h-14 rounded-2xl bg-secondary/60 flex items-center justify-center mb-5">
                <Inbox className="w-7 h-7 text-muted-foreground/50" />
              </div>
              <h3 className="font-semibold text-foreground text-lg mb-2">No applications yet</h3>
              <p className="text-sm text-muted-foreground/70 max-w-xs">
                Start the agent to begin discovering and applying to jobs automatically.
              </p>
            </div>
          )}
        </div>

        {/* Setup Progress (1/3) - hidden when all items completed */}
        {completedCount < setupItems.length && <div className="bg-card rounded-2xl border border-border/40 p-5 shadow-sm">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-primary" />
            </div>
            <h2 className="font-semibold text-foreground">Setup Progress</h2>
          </div>

          <p className="text-xs text-muted-foreground/70 mb-5 ml-11">
            {completedCount}/{setupItems.length} completed
          </p>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-secondary/80 rounded-full mb-6 overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-500"
              style={{ width: `${(completedCount / setupItems.length) * 100}%` }}
            />
          </div>

          <div className="space-y-1">
            {setupItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 w-full p-3 rounded-xl text-sm transition-all duration-200 group',
                  item.done
                    ? 'text-muted-foreground'
                    : 'text-foreground hover:bg-secondary/40 border border-transparent hover:border-border/30'
                )}
              >
                <div
                  className={cn(
                    'w-6 h-6 rounded-full flex items-center justify-center shrink-0 transition-colors duration-200',
                    item.done
                      ? 'bg-emerald-500/10 text-emerald-500'
                      : 'bg-secondary/80 text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary'
                  )}
                >
                  {item.done ? (
                    <Check className="w-3.5 h-3.5" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-current opacity-40" />
                  )}
                </div>
                <span className={cn('font-medium', item.done && 'line-through opacity-60')}>
                  {item.label}
                </span>
                {!item.done && (
                  <ArrowUpRight className="w-3.5 h-3.5 ml-auto text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
                )}
              </Link>
            ))}
          </div>

          {completedCount === setupItems.length && (
            <div className="mt-5 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/15">
              <p className="text-xs text-emerald-500 font-medium flex items-center gap-2">
                <Check className="w-3.5 h-3.5" />
                All set! You are ready to start the agent.
              </p>
            </div>
          )}
        </div>}
      </div>
    </div>
  );
}
