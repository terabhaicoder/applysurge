'use client';

import { useEffect } from 'react';
import { ArrowLeft, Monitor, Zap, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useAgentStore } from '@/stores/agent-store';
import { useSocketContext } from '@/providers/socket-provider';
import { cn } from '@/lib/utils';

export default function AgentLivePage() {
  const { status, logs, liveScreenshot, setLiveScreenshot, addLog, clearLogs } = useAgentStore();
  const { socket } = useSocketContext();

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

  const levelColors: Record<string, { bg: string; text: string; dot: string }> = {
    info: { bg: 'bg-blue-400/10', text: 'text-blue-400', dot: 'bg-blue-400' },
    success: { bg: 'bg-emerald-400/10', text: 'text-emerald-400', dot: 'bg-emerald-400' },
    warning: { bg: 'bg-amber-400/10', text: 'text-amber-400', dot: 'bg-amber-400' },
    error: { bg: 'bg-red-400/10', text: 'text-red-400', dot: 'bg-red-400' },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <Link
            href="/agent"
            className="p-2 rounded-xl hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-foreground tracking-tight">Live Browser View</h1>
            <p className="text-muted-foreground text-sm mt-1">Watch the AI agent apply to jobs in real-time</p>
          </div>
        </div>

        {/* Status Indicator */}
        <div className={cn(
          'flex items-center gap-3 px-4 py-2 rounded-xl border transition-colors',
          status.is_running
            ? 'bg-primary/5 border-primary/20'
            : status.is_paused
            ? 'bg-amber-400/5 border-amber-400/20'
            : 'bg-secondary/50 border-border'
        )}>
          <div className="relative">
            <div className={cn(
              'w-2.5 h-2.5 rounded-full',
              status.is_running ? 'bg-primary' :
              status.is_paused ? 'bg-amber-400' : 'bg-muted-foreground'
            )} />
            {status.is_running && (
              <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-primary animate-ping opacity-75" />
            )}
          </div>
          <span className="text-sm font-medium text-foreground capitalize">
            {status.is_running ? 'Running' : status.is_paused ? 'Paused' : 'Stopped'}
          </span>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Live Browser View */}
        <div className="bg-card rounded-2xl border border-border/50 overflow-hidden">
          <div className="flex items-center gap-3 p-4 border-b border-border/50">
            <div className="w-8 h-8 rounded-lg bg-violet-400/10 flex items-center justify-center">
              <Monitor className="w-4 h-4 text-violet-400" />
            </div>
            <h2 className="font-semibold text-foreground">Browser Preview</h2>
            {status.is_running && (
              <span className="ml-auto flex items-center gap-1.5 text-xs text-primary">
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Live
              </span>
            )}
          </div>
          <div className="aspect-video bg-black/50 flex items-center justify-center">
            {liveScreenshot ? (
              <img
                src={liveScreenshot}
                alt="Live browser view"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="text-center p-8">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-secondary flex items-center justify-center">
                  <Monitor className="w-8 h-8 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">
                  {status.is_running ? 'Waiting for screenshot...' : 'Start the agent to see live view'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Activity Logs */}
        <div className="bg-card rounded-2xl border border-border/50 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between p-4 border-b border-border/50">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
                <Zap className="w-4 h-4 text-blue-400" />
              </div>
              <h2 className="font-semibold text-foreground">Activity Logs</h2>
            </div>
            <button
              onClick={clearLogs}
              className="p-2 rounded-lg hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
              title="Clear logs"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 max-h-[400px] overflow-y-auto divide-y divide-border/50 scrollbar-hide">
            {logs.length > 0 ? (
              logs.map((log) => {
                const colors = levelColors[log.level] || levelColors.info;
                return (
                  <div key={log.id} className="p-3 hover:bg-secondary/30 transition-colors">
                    <div className="flex items-start gap-2">
                      <span className={cn('w-1.5 h-1.5 rounded-full mt-2 flex-shrink-0', colors.dot)} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-foreground font-mono">{log.message}</p>
                        <p className="text-[10px] text-muted-foreground mt-1">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-12 text-center">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-secondary flex items-center justify-center">
                  <Zap className="w-6 h-6 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">No logs yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
