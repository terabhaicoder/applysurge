"use client";

import { X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MatchScoreBadge } from "@/components/jobs/match-score-badge";
import { QueueItem } from "@/types/agent";

interface ApplicationQueueProps {
  queue: QueueItem[];
  onRemove?: (jobId: string) => void;
}

export function ApplicationQueue({ queue, onRemove }: ApplicationQueueProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg">Queue</CardTitle>
        <Badge variant="secondary">{queue.length} jobs</Badge>
      </CardHeader>
      <CardContent>
        {queue.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">Queue is empty</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {queue.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-secondary"
              >
                <div>
                  <p className="text-sm font-medium text-foreground">{item.job_title}</p>
                  <p className="text-xs text-muted-foreground">{item.company}</p>
                </div>
                <div className="flex items-center gap-2">
                  <MatchScoreBadge score={item.match_score} size="sm" />
                  {item.status === "processing" && (
                    <Badge variant="info" className="text-xs">Processing</Badge>
                  )}
                  {onRemove && (
                    <button
                      onClick={() => onRemove(item.job_id)}
                      className="p-1 rounded hover:bg-red-500/10 text-muted-foreground hover:text-red-400 transition-colors"
                      title="Remove from queue"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
