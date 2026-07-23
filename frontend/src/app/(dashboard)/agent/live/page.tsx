'use client';

import { useEffect } from 'react';
import { ArrowLeft, Monitor, Zap, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useAgentStore } from '@/stores/agent-store';
import { useSocketContext } from '@/providers/socket-provider';
import { useAgent } from '@/hooks/use-agent';
import api from '@/lib/api';
import { cn } from '@/lib/utils';

export default function AgentLivePage() {
  const { status, logs, liveScreenshot, setLiveScreenshot, addLog, setLogs, clearLogs } = useAgentStore();
  const { socket } = useSocketContext();
  const { status: agentStatus } = useAgent();
  const isRunning = agentStatus?.is_running || status.is_running;

  // Load historical logs from Redis via API
  const { data: historicalLogs } = useQuery({
    queryKey: ['agent-logs-live'],
    queryFn: () => api.get('/agent/logs', { params: { limit: 50 } }).then((r) => r.data),
    refetchInterval: isRunning ? 3000 : 10000,
  });

  // Sync historical logs into store if no socket logs exist
  useEffect(() => {
    if (historicalLogs && historicalLogs.length > 0 && logs.length === 0) {
      const mapped = historicalLogs.map((l: any) => ({
        id: l.id,
        timestamp: l.timestamp,
        level: l.is_error ? 'error' : l.action?.includes('complete') ? 'success' : 'info',
        message: l.message,
      }));
      setLogs(mapped);
    }
  }, [historicalLogs, logs.length, setLogs]);

  useEffect(() => {
    if (!socket) return;

    socket.on('agent:screenshot', (data: { image: string }) => {
      setLiveScreenshot(data.image);
    });

    socket.on('agent:log', (log: { id: string; timestamp: string; level: string; message: string }) => {
      addLog({
        id: log.id,
        timestamp: log.timestamp,
        level: log.level as 'info' | 'warning' | 'error' | 'success',
        message: log.message,
      });
    });

    return () => {
      socket.off('agent:screenshot');
      socket.off('agent:log');
    };
  }, [socket, setLiveScreenshot, addLog]);

  const levelColors: Record<string, { dot: string }> = {
    info: { dot: 'bg-blue-400' },
    success: { dot: 'bg-emerald-400' },
    warning: { dot: 'bg-amber-400' },
    error: { dot: 'bg-red-400' },
  };

  // Use historical logs if store logs are empty
  const displayLogs = logs.length > 0 ? logs : (historicalLogs || []).map((l: any) => ({
    id: l.id,
    timestamp: l.timestamp,
    level: l.is_error ? 'error' : l.action?.includes('complete') ? 'success' : 'info',
    message: l.message,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Live View</h1>
            <p className="text-muted-foreground text-sm mt-1">Watch the agent work in real-time</p>
          </div>
        </div>
        <div className={cn(
          'flex items-center gap-2.5 px-4 py-2 rounded-xl border',
          isRunning ? 'bg-primary/5 border-primary/20' : 'bg-secondary/50 border-border'
        )}>
          <div className="relative">
            <div className={cn('w-2.5 h-2.5 rounded-full', isRunning ? 'bg-emerald-500' : 'bg-muted-foreground')} />
            {isRunning && <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping opacity-75" />}
          </div>
          <span className="text-sm font-medium text-foreground">{isRunning ? 'Running' : 'Stopped'}</span>
        </div>
      </div>

      {/* Browser Preview — full width, large */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="flex items-center gap-3 p-4 border-b border-border/50">
          <div className="w-8 h-8 rounded-lg bg-violet-400/10 flex items-center justify-center">
            <Monitor className="w-4 h-4 text-violet-400" />
          </div>
          <h2 className="font-semibold text-foreground">Browser Preview</h2>
          {isRunning && (
            <span className="ml-auto flex items-center gap-1.5 text-xs text-emerald-500">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </span>
          )}
        </div>
        <div className="aspect-[16/9] bg-black/30 flex items-center justify-center min-h-[400px]">
          {liveScreenshot ? (
            <img src={liveScreenshot} alt="Live browser view" className="w-full h-full object-contain" />
          ) : (
            <div className="text-center p-8">
              <Monitor className="w-12 h-12 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-sm text-muted-foreground">
                {isRunning ? 'Waiting for browser screenshot...' : 'Start the agent from the Dashboard to see live view'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Activity Logs — full width below */}
      <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-border/50">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
              <Zap className="w-4 h-4 text-blue-400" />
            </div>
            <h2 className="font-semibold text-foreground">Activity Logs</h2>
            <span className="text-xs text-muted-foreground bg-secondary px-2 py-0.5 rounded-full">{displayLogs.length}</span>
          </div>
          <button onClick={clearLogs} className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors" title="Clear logs">
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
        <div className="max-h-[350px] overflow-y-auto divide-y divide-border/30">
          {displayLogs.length > 0 ? (
            displayLogs.map((log: any) => {
              const colors = levelColors[log.level] || levelColors.info;
              return (
                <div key={log.id} className="px-5 py-3 hover:bg-secondary/30 transition-colors">
                  <div className="flex items-start gap-3">
                    <span className={cn('w-2 h-2 rounded-full mt-1.5 shrink-0', colors.dot)} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-foreground">{log.message}</p>
                      <p className="text-[11px] text-muted-foreground mt-0.5">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : ''}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="p-10 text-center">
              <Zap className="w-6 h-6 text-muted-foreground/30 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No activity yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
