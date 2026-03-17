"use client";

import { Play, Pause, Square, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { AgentStatusIndicator } from "./agent-status-indicator";
import { AgentStatus } from "@/types/agent";

interface AgentControlPanelProps {
  status: AgentStatus;
  onStart: () => void;
  onStop: () => void;
  onPause: () => void;
  onResume: () => void;
  isStarting?: boolean;
  isStopping?: boolean;
}

export function AgentControlPanel({
  status,
  onStart,
  onStop,
  onPause,
  onResume,
  isStarting,
  isStopping,
}: AgentControlPanelProps) {
  const appliedToday = status.applications_made_today ?? 0;
  const dailyLimit = status.applications_limit_today ?? 1;
  const queueSize = status.queue_size ?? 0;
  const progress = dailyLimit > 0 ? (appliedToday / dailyLimit) * 100 : 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-lg">Agent Control</CardTitle>
        <AgentStatusIndicator state={status.status} />
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Activity */}
        {status.current_task && (
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <p className="text-xs text-blue-600 font-medium mb-1">Currently Processing</p>
            <p className="text-sm text-blue-900">{status.current_task}</p>
          </div>
        )}

        {/* Progress */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Daily Progress</span>
            <span className="font-semibold text-foreground">
              {appliedToday} / {dailyLimit}
            </span>
          </div>
          <Progress value={progress} className="h-2.5" />
          <p className="text-xs text-muted-foreground">
            {dailyLimit - appliedToday} applications remaining today
          </p>
        </div>

        {/* Queue Info */}
        <div className="flex items-center justify-between p-3 bg-secondary rounded-lg">
          <span className="text-sm text-muted-foreground">Jobs in Queue</span>
          <span className="text-lg font-bold text-foreground">{queueSize}</span>
        </div>

        {/* Controls */}
        <div className="flex gap-3">
          {status.status === "idle" || status.status === "stopped" ? (
            <Button className="flex-1 gap-2" onClick={onStart} disabled={isStarting}>
              <Play className="w-4 h-4" />
              {isStarting ? "Starting..." : "Start Agent"}
            </Button>
          ) : status.status === "paused" ? (
            <>
              <Button className="flex-1 gap-2" onClick={onResume}>
                <RefreshCw className="w-4 h-4" />
                Resume
              </Button>
              <Button variant="outline" className="gap-2 text-red-600" onClick={onStop} disabled={isStopping}>
                <Square className="w-4 h-4" />
                Stop
              </Button>
            </>
          ) : (
            <>
              <Button variant="outline" className="flex-1 gap-2" onClick={onPause}>
                <Pause className="w-4 h-4" />
                Pause
              </Button>
              <Button variant="outline" className="gap-2 text-red-600" onClick={onStop} disabled={isStopping}>
                <Square className="w-4 h-4" />
                Stop
              </Button>
            </>
          )}
        </div>

        {/* Error Message */}
        {status.errors_count > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-xs text-red-600 font-medium mb-1">Errors</p>
            <p className="text-sm text-red-800">{status.errors_count} error(s) occurred during this session</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
