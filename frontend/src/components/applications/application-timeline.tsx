"use client";

import { CheckCircle2, Clock, AlertCircle, Send, Eye } from "lucide-react";
import { ApplicationLog } from "@/types/application";
import { formatDate } from "@/lib/utils";

interface ApplicationTimelineProps {
  logs: ApplicationLog[];
}

const getLogIcon = (action: string) => {
  if (action.includes("applied") || action.includes("submit")) return { icon: Send, color: "text-blue-600 bg-blue-50" };
  if (action.includes("viewed")) return { icon: Eye, color: "text-purple-600 bg-purple-50" };
  if (action.includes("error") || action.includes("fail")) return { icon: AlertCircle, color: "text-red-600 bg-red-50" };
  if (action.includes("success") || action.includes("complete")) return { icon: CheckCircle2, color: "text-green-600 bg-green-50" };
  return { icon: Clock, color: "text-muted-foreground bg-secondary" };
};

export function ApplicationTimeline({ logs }: ApplicationTimelineProps) {
  if (logs.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-4">No activity logs yet.</p>;
  }

  return (
    <div className="space-y-4">
      {logs.map((log, index) => {
        const { icon: Icon, color } = getLogIcon(log.action);
        return (
          <div key={log.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${color}`}>
                <Icon className="w-4 h-4" />
              </div>
              {index < logs.length - 1 && <div className="w-px h-full bg-border mt-1" />}
            </div>
            <div className="pb-4">
              <p className="text-sm font-medium text-foreground">{log.action}</p>
              {log.details && <p className="text-xs text-muted-foreground mt-0.5">{log.details}</p>}
              <p className="text-xs text-muted-foreground mt-1">{formatDate(log.created_at, "MMM d, yyyy h:mm a")}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
