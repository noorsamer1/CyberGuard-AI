import { Badge } from "@/components/ui/badge";
import type { Severity } from "@/lib/api/types";
import { cn } from "@/lib/utils";

const styles: Record<Severity, string> = {
  low: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  critical: "bg-red-600/20 text-red-300 border-red-500/40",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <Badge variant="outline" className={cn("font-medium capitalize", styles[severity])}>
      {severity}
    </Badge>
  );
}
