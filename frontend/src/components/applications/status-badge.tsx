import { Badge } from "@/components/ui/badge";
import { getStatusColor, formatStatus } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge variant="outline" className={getStatusColor(status)}>
      {formatStatus(status)}
    </Badge>
  );
}
