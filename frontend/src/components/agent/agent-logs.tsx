"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Trash2 } from "lucide-react";
import { AgentLog } from "@/types/agent";
import { cn } from "@/lib/utils";

interface AgentLogsProps {
  logs: AgentLog[];
  onClear: () => void;
}

const levelColors: Record<string, string> = {
  info: "text-blue-600",
  warning: "text-amber-600",
  error: "text-red-600",
  success: "text-green-600",
};

export function AgentLogs({ logs, onClear }: AgentLogsProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Logs</CardTitle>
        <Button variant="ghost" size="sm" onClick={onClear} className="gap-1 text-muted-foreground">
          <Trash2 className="w-3.5 h-3.5" />
          Clear
        </Button>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-64">
          {logs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">No logs yet</p>
          ) : (
            <div className="space-y-1 font-mono text-xs">
              {logs.map((log) => (
                <div key={log.id} className="flex gap-2 py-1">
                  <span className="text-muted-foreground flex-shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className={cn("uppercase font-bold flex-shrink-0 w-14", levelColors[log.level])}>
                    [{log.level}]
                  </span>
                  <span className="text-foreground">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
