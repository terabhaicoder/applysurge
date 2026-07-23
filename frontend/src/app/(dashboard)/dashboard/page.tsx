'use client';

import { useQuery } from '@tanstack/react-query';
import {
  Briefcase,
  Target,
  Calendar,
  Play,
  Square,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  Check,
  AlertCircle,
  Inbox,
  Zap,
  Clock,
  X,
  Monitor,
} from 'lucide-react';
import Link from 'next/link';
import { useAgent } from '@/hooks/use-agent';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { status: agentData, start, stop, unqueue, isLoading: agentLoading } = useAgent();
  const isAgentRunning = agentData?.is_running === true;
  const betaLimitReached = (agentData?.applications_total ?? 0) >= (agentData?.applications_limit_total ?? 10);

  const { data: stats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => api.get('/analytics/overview').then((r) => r.data),
  });

  const { data: recentApps } = useQuery({
    queryKey: ['recent-applications'],
    queryFn: () => api.get('/applications', { params: { limit: 5 } }).then((r) => r.data),
  });

  const { data: queue } = useQuery({
    queryKey: ['agent-queue'],
    queryFn: () => api.get('/jobs/queue').then((r) => r.data),
    refetchInterval: isAgentRunning ? 5000 : false,
  });

  const { data: logs } = useQuery({
    queryKey: ['agent-logs'],
    queryFn: () => api.get('/agent/logs', { params: { limit: 20 } }).then((r) => r.data),
    refetchInterval: isAgentRunning ? 5000 : false,
  });

  const { data: resumes } = useQuery({
    queryKey: ['setup-resumes'],
    queryFn: () => api.get('/resumes/').then((r) => r.data),
  });

  const { data: preferences } = useQuery({
    queryKey: ['setup-preferences'],
    queryFn: () => api.get('/preferences/').then((r) => r.data),
  });

  const { data: credentials } = useQuery({
    queryKey: ['setup-credentials'],
    queryFn: () => api.get('/credentials/').then((r) => r.data),
  });

  const hasResume = Array.isArray(resumes) ? resumes.length > 0 : Boolean(resumes?.items?.length);
  const hasPreferences = Boolean(preferences?.desired_titles?.length) || (typeof preferences?.desired_titles === 'string' && preferences.desired_titles.length > 2);
  const hasLinkedIn = Array.isArray(credentials)
    ? credentials.some((c: any) => c.platform === 'linkedin')
    : Boolean(credentials?.items?.some?.((c: any) => c.platform === 'linkedin'));

  const setupItems = [
    { label: 'Upload your resume', done: hasResume },
    { label: 'Set job preferences', done: hasPreferences },
    { label: 'Connect LinkedIn', done: hasLinkedIn },
  ];

  const completedCount = setupItems.filter((i) => i.done).length;

  const statCards = [
    { label: 'Applied Today', value: agentData?.applications_made_today ?? 0, icon: Briefcase, iconBg: 'bg-indigo-500/10 text-indigo-500' },
    { label: 'Total Applied', value: `${agentData?.applications_total ?? 0}/${agentData?.applications_limit_total ?? 10}`, icon: Target, iconBg: 'bg-emerald-500/10 text-emerald-500' },
    { label: 'In Queue', value: agentData?.queue_size ?? 0, icon: Clock, iconBg: 'bg-violet-500/10 text-violet-500' },
    { label: 'Interviews', value: stats?.interviews ?? 0, icon: Calendar, iconBg: 'bg-amber-500/10 text-amber-500' },
  ];

  const statusConfig: Record<string, { bg: string; text: string; dot: string }> = {
    applied: { bg: 'bg-blue-500/10', text: 'text-blue-500', dot: 'bg-blue-500' },
    interview_scheduled: { bg: 'bg-violet-500/10', text: 'text-violet-500', dot: 'bg-violet-500' },
    failed: { bg: 'bg-red-500/10', text: 'text-red-500', dot: 'bg-red-500' },
    pending: { bg: 'bg-secondary', text: 'text-muted-foreground', dot: 'bg-muted-foreground' },
  };

  const applications = recentApps?.items ?? [];
  const hasApplications = applications.length > 0;

  return (
    <div className="space-y-6">
      {/* Setup Progress Banner */}
      {completedCount < setupItems.length && (
        <div className="bg-card rounded-2xl border border-amber-500/20 p-4 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4">
            <div className="flex items-center gap-3 shrink-0">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <AlertCircle className="w-4 h-4 text-amber-500" />
              </div>
              <div>
                <h2 className="font-semibold text-foreground text-sm">Complete your setup</h2>
                <p className="text-xs text-muted-foreground">{completedCount}/{setupItems.length} done</p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2 flex-1">
              {setupItems.map((item, i) => (
                <span key={i} className={cn(
                  'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium',
                  item.done ? 'bg-emerald-500/10 text-emerald-500' : 'bg-secondary text-muted-foreground'
                )}>
                  {item.done ? <Check className="w-3 h-3" /> : <div className="w-1.5 h-1.5 rounded-full bg-current opacity-40" />}
                  {item.label}
                </span>
              ))}
            </div>
            <Link href="/settings" className="shrink-0 text-xs font-semibold text-primary hover:text-primary/80 flex items-center gap-1">
              Complete Setup <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Agent Control + Stats */}
      <div className={cn(
        'relative rounded-2xl border p-6 transition-all overflow-hidden',
        isAgentRunning ? 'bg-primary/[0.03] border-primary/20' : 'bg-card border-border/40'
      )}>
        {isAgentRunning && (
          <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/[0.04] via-transparent to-violet-500/[0.04] pointer-events-none" />
        )}
        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
            <div className="flex items-center gap-4">
              <div className="relative">
                <div className={cn('w-3 h-3 rounded-full', isAgentRunning ? 'bg-emerald-500' : 'bg-muted-foreground/40')} />
                {isAgentRunning && <div className="absolute inset-0 w-3 h-3 rounded-full bg-emerald-500 animate-ping opacity-75" />}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  {isAgentRunning ? 'Agent Running' : 'Agent Stopped'}
                </h2>
                <p className="text-sm text-muted-foreground/80">
                  {isAgentRunning ? 'Scanning LinkedIn and applying to matching jobs' : 'Start the agent to discover and apply to jobs'}
                </p>
              </div>
            </div>
            {isAgentRunning ? (
              <button onClick={stop} disabled={agentLoading} className="px-5 py-2.5 text-sm font-medium bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl flex items-center gap-2 transition-colors shrink-0 disabled:opacity-50">
                <Square className="w-4 h-4" /> Stop Agent
              </button>
            ) : (
              <button onClick={start} disabled={agentLoading || betaLimitReached} className={cn(
                "px-6 py-2.5 text-sm font-medium rounded-xl flex items-center gap-2 transition-all shrink-0 disabled:opacity-50",
                betaLimitReached ? "bg-secondary text-muted-foreground cursor-not-allowed" : "bg-primary hover:bg-primary/90 text-primary-foreground shadow-md shadow-primary/20"
              )}>
                <Play className="w-4 h-4" /> {betaLimitReached ? "Limit Reached" : "Start Agent"}
              </button>
            )}
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {statCards.map((stat) => (
              <div key={stat.label} className="bg-background/50 rounded-xl p-4 border border-border/30">
                <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center mb-2', stat.iconBg)}>
                  <stat.icon className="w-3.5 h-3.5" />
                </div>
                <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Queue + Activity Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Queue */}
        <div className="bg-card rounded-2xl border border-border/40 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border/30">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-violet-400/10 flex items-center justify-center">
                <Clock className="w-4 h-4 text-violet-400" />
              </div>
              <h3 className="font-semibold text-foreground">Application Queue</h3>
            </div>
            <span className="text-xs text-muted-foreground px-2.5 py-1 bg-secondary rounded-full">
              {queue?.length || 0} pending
            </span>
          </div>
          <div className="divide-y divide-border/30 max-h-72 overflow-y-auto">
            {(queue || []).slice(0, 8).map((item: any) => (
              <div key={item.id} className="p-4 flex items-center justify-between hover:bg-secondary/30 transition-colors">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 bg-secondary rounded-xl flex items-center justify-center shrink-0">
                    <span className="text-xs font-semibold text-foreground">{item.job?.company?.charAt(0) || 'J'}</span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-foreground truncate">{item.job?.title}</p>
                    <p className="text-xs text-muted-foreground truncate">{item.job?.company}</p>
                  </div>
                </div>
                <button onClick={() => unqueue(String(item.job?.id))} className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors shrink-0 ml-2" title="Remove">
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
            {(!queue || queue.length === 0) && (
              <div className="p-10 text-center">
                <Clock className="w-6 h-6 text-muted-foreground/40 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">Queue is empty</p>
              </div>
            )}
          </div>
        </div>

        {/* Activity Log */}
        <div className="bg-card rounded-2xl border border-border/40 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border/30">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <h3 className="font-semibold text-foreground">Activity Log</h3>
            </div>
            <Link href="/agent/live" className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1.5 px-3 py-1.5 bg-secondary rounded-lg transition-colors">
              <Monitor className="w-3.5 h-3.5" /> Live View <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-border/30 max-h-72 overflow-y-auto">
            {(logs || []).slice(0, 10).map((log: any, i: number) => (
              <div key={log.id || i} className="p-4 flex items-start gap-3 hover:bg-secondary/30 transition-colors">
                <div className={cn(
                  'w-2 h-2 rounded-full mt-2 shrink-0',
                  log.is_error ? 'bg-red-400' : log.action?.includes('complete') ? 'bg-emerald-400' : 'bg-blue-400'
                )} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-foreground">{log.message}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                  </p>
                </div>
              </div>
            ))}
            {(!logs || logs.length === 0) && (
              <div className="p-10 text-center">
                <Zap className="w-6 h-6 text-muted-foreground/40 mx-auto mb-2" />
                <p className="text-sm text-muted-foreground">No activity yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Applications */}
      {hasApplications && (
        <div className="bg-card rounded-2xl border border-border/40 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border/30">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-indigo-500" />
              </div>
              <h2 className="font-semibold text-foreground">Recent Applications</h2>
            </div>
            <Link href="/applications" className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors group">
              View all <ArrowUpRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Link>
          </div>
          <div className="divide-y divide-border/30">
            {applications.slice(0, 5).map((app: any) => {
              const config = statusConfig[app.status] || statusConfig.pending;
              return (
                <div key={app.id} className="flex items-center justify-between p-4 hover:bg-secondary/30 transition-colors">
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="w-10 h-10 bg-secondary/60 rounded-xl flex items-center justify-center shrink-0">
                      <span className="text-sm font-semibold text-foreground/80">{app.company_name?.charAt(0) || 'J'}</span>
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{app.job_title}</p>
                      <p className="text-xs text-muted-foreground/70 truncate">{app.company_name}</p>
                    </div>
                  </div>
                  <span className={cn('text-xs px-2.5 py-1 rounded-full font-medium flex items-center gap-1.5 shrink-0 ml-3', config.bg, config.text)}>
                    <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
                    {app.status?.replace(/_/g, ' ')}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
