import { cn, getMatchScoreColor } from "@/lib/utils";

interface MatchScoreBadgeProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function MatchScoreBadge({ score, size = "md" }: MatchScoreBadgeProps) {
  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-0.5",
    lg: "text-base px-3 py-1",
  };

  return (
    <span className={cn("rounded-full font-semibold border", getMatchScoreColor(score), sizeClasses[size])}>
      {score}% match
    </span>
  );
}
