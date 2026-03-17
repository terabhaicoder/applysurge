'use client';

import { useQuery } from '@tanstack/react-query';
import { Play, Pause, Square, Settings, Monitor, Clock, Zap, AlertCircle, Sparkles, Target, ArrowUpRight, X, Shield } from 'lucide-react';
import Link from 'next/link';
import { useAgent } from '@/hooks/use-agent';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

export default function AgentPage() {
  const { status, start, stop, unqueue, isLoading } = useAgent();
  const isActive = status?.is_running === true;
  const betaLimitReached = (status?.applications_total ?? 0) >= (status?.applications_limit_total ?? 10);

  const { data: settings } = useQuery({
    queryKey: ['agent-settings'],
    queryFn: () => api.get('/agent/settings').then((r) => r.data),
  });

  const { data: queue } = useQuery({
    queryKey: ['agent-queue'],
    queryFn: () => api.get('/jobs/queue').then((r) => r.data),
    refetchInterval: isActive ? 5000 : false,
  });

  const { data: logs } = useQuery({
    queryKey: ['agent-logs'],
    queryFn: () => api.get('/agent/logs', { params: { limit: 20 } }).then((r) => r.data),
    refetchInterval: isActive ? 10000 : false,
  });

  const stats = [
    { label: 'Applied Today', value: status?.applications_made_today || 0, icon: Target, color: 'text-blue-400', bg: 'bg-blue-400/10' },
    { label: 'App Limit', value: `${status?.applications_total ?? 0}/${status?.applications_limit_total ?? 10}`, icon: Shield, color: 'text-amber-400', bg: 'bg-amber-400/10' },
    { label: 'In Queue', value: status?.queue_size || 0, icon: Clock, color: 'text-violet-400', bg: 'bg-violet-400/10' },
    { label: 'Errors', value: status?.errors_count || 0, icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-400/10' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground tracking-tight">Agent Control</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage your automation agent</p>
        </div>
        <Link
          href="/settings/agent"
          className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border border-border/50 rounded-xl hover:bg-secondary text-foreground transition-colors"
        >
          <Settings className="w-4 h-4" />
          Settings
        </Link>
      </div>

      {/* Limit Banner */}
      {betaLimitReached && (
        <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-5 flex items-start gap-3">
          <Shield className="w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-sm font-semibold text-amber-400">Application Limit Reached</p>
            <p className="text-xs text-amber-400/70 mt-1">
              You have used all {status?.applications_limit_total} applications on the free plan. Upgrade to continue applying.
            </p>
          </div>
        </div>
      )}

      {/* Agent Status Card */}
      <div className="relative bg-card rounded-2xl border border-border/50 p-6 overflow-hidden">
        {/* Background effect for active state */}
        {isActive && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent" />
        )}

        <div className="relative z-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-4">
              <div className={cn(
                'relative w-14 h-14 rounded-2xl flex items-center justify-center transition-colors',
                isActive ? 'bg-primary/10' : 'bg-secondary'
              )}>
                <Sparkles className={cn(
                  'w-7 h-7 transition-colors',
                  isActive ? 'text-primary' : 'text-muted-foreground'
                )} />
                {isActive && (
                  <div className="absolute inset-0 rounded-2xl border-2 border-primary/30 animate-pulse" />
                )}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">
                  Agent is {isActive ? 'Running' : status?.is_paused ? 'Paused' : 'Stopped'}
                </h2>
                <p className="text-sm text-muted-foreground">
                  {isActive
                    ? 'Actively scanning and applying to jobs'
                    : 'Start the agent to begin automated applications'}
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              {isActive ? (
                <button
                  onClick={stop}
                  disabled={isLoading}
                  className="px-5 py-2.5 text-sm font-medium bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 rounded-xl flex items-center gap-2 transition-colors"
                >
                  <Square className="w-4 h-4" />
                  Stop Agent
                </button>
              ) : (
                <button
                  onClick={start}
                  disabled={isLoading || betaLimitReached}
                  className={cn(
                    "px-6 py-2.5 text-sm font-medium rounded-xl flex items-center gap-2 transition-all",
                    betaLimitReached
                      ? "bg-secondary text-muted-foreground cursor-not-allowed"
                      : "bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg shadow-primary/20 hover:shadow-primary/30"
                  )}
                >
                  <Play className="w-4 h-4" />
                  {betaLimitReached ? "Limit Reached" : "Start Agent"}
                </button>
              )}
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {stats.map((stat) => (
              <div key={stat.label} className="bg-secondary/50 rounded-xl p-4 border border-border/50">
                <div className="flex items-center gap-2 mb-2">
                  <div className={cn('w-7 h-7 rounded-lg flex items-center justify-center', stat.bg)}>
                    <stat.icon className={cn('w-3.5 h-3.5', stat.color)} />
                  </div>
                </div>
                <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Queue */}
        <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border/50">
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
          <div className="divide-y divide-border/50 max-h-80 overflow-y-auto scrollbar-hide">
            {(queue || []).slice(0, 10).map((item: any) => (
              <div key={item.id} className="p-4 flex items-center justify-between hover:bg-secondary/30 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-secondary rounded-xl flex items-center justify-center">
                    <span className="text-xs font-semibold text-foreground">
                      {item.job?.company?.charAt(0) || 'J'}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">{item.job?.title}</p>
                    <p className="text-xs text-muted-foreground">{item.job?.company}</p>
                  </div>
                </div>
                <span className={cn(
                  'text-xs px-2.5 py-1 rounded-full font-medium',
                  (item.job?.match_score || 0) >= 80 ? 'bg-emerald-400/10 text-emerald-400' :
                  (item.job?.match_score || 0) >= 60 ? 'bg-blue-400/10 text-blue-400' :
                  'bg-secondary text-muted-foreground'
                )}>
                  {Math.round(item.job?.match_score || 0)}% match
                </span>
                <button
                  onClick={(e) => { e.stopPropagation(); unqueue(String(item.job?.id)); }}
                  className="p-1.5 rounded-lg hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors"
                  title="Remove from queue"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
            {(!queue || queue.length === 0) && (
              <div className="p-12 text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-secondary flex items-center justify-center">
                  <Clock className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">Queue is empty</p>
              </div>
            )}
          </div>
        </div>

        {/* Activity Log */}
        <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-border/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <h3 className="font-semibold text-foreground">Activity Log</h3>
            </div>
            <Link
              href="/agent/live"
              className="text-xs text-muted-foreground hover:text-primary flex items-center gap-1.5 px-3 py-1.5 bg-secondary rounded-lg transition-colors"
            >
              <Monitor className="w-3.5 h-3.5" />
              Live View
              <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-border/50 max-h-80 overflow-y-auto scrollbar-hide">
            {(logs || []).slice(0, 10).map((log: any, i: number) => (
              <div key={log.id || i} className="p-4 flex items-start gap-3 hover:bg-secondary/30 transition-colors">
                <div className={cn(
                  'w-2 h-2 rounded-full mt-2 flex-shrink-0',
                  log.level === 'error' ? 'bg-red-400' : log.level === 'warning' ? 'bg-amber-400' : 'bg-emerald-400'
                )} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm text-foreground">{log.message}</p>
                  <p className="text-xs text-muted-foreground flex items-center gap-1.5 mt-1">
                    <Clock className="w-3 h-3" />
                    {new Date(log.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {(!logs || logs.length === 0) && (
              <div className="p-12 text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-secondary flex items-center justify-center">
                  <Zap className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">No activity yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
