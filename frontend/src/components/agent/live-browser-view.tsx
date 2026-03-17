"use client";

import { Monitor, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAgentStore } from "@/stores/agent-store";

export function LiveBrowserView() {
  const { liveScreenshot, status } = useAgentStore();

  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <Monitor className="w-5 h-5 text-muted-foreground" />
          Live View
        </CardTitle>
        <div className="flex items-center gap-2">
          {status.status === "running" && (
            <span className="flex items-center gap-1.5 text-xs text-green-600">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              Live
            </span>
          )}
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {liveScreenshot ? (
          <div className="rounded-lg overflow-hidden border border-border">
            <img
              src={liveScreenshot}
              alt="Live browser view"
              className="w-full h-auto"
            />
          </div>
        ) : (
          <div className="h-64 bg-secondary rounded-lg flex flex-col items-center justify-center">
            <Monitor className="w-12 h-12 text-border mb-2" />
            <p className="text-sm text-muted-foreground">
              {status.status === "running"
                ? "Waiting for screenshot..."
                : "Start the agent to see live activity"}
            </p>
          </div>
        )}

        {status.current_task && (
          <div className="mt-3 p-2 bg-secondary rounded text-xs text-muted-foreground">
            Current step: <span className="font-medium">{status.current_task}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
