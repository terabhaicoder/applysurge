import { cn } from "@/lib/utils";
import { AgentState } from "@/types/agent";

interface AgentStatusIndicatorProps {
  state: AgentState;
  showLabel?: boolean;
}

const stateConfig: Record<AgentState, { label: string; color: string; dot: string }> = {
  idle: { label: "Idle", color: "text-muted-foreground", dot: "bg-muted-foreground" },
  running: { label: "Running", color: "text-green-600", dot: "bg-green-500 animate-pulse" },
  paused: { label: "Paused", color: "text-amber-600", dot: "bg-amber-500" },
  error: { label: "Error", color: "text-red-600", dot: "bg-red-500" },
  stopped: { label: "Stopped", color: "text-muted-foreground", dot: "bg-muted-foreground" },
  enabled: { label: "Enabled", color: "text-primary", dot: "bg-primary" },
};

export function AgentStatusIndicator({ state, showLabel = true }: AgentStatusIndicatorProps) {
  const config = stateConfig[state];

  return (
    <div className="flex items-center gap-2">
      <span className={cn("w-2.5 h-2.5 rounded-full", config.dot)} />
      {showLabel && (
        <span className={cn("text-sm font-medium", config.color)}>{config.label}</span>
      )}
    </div>
  );
}
