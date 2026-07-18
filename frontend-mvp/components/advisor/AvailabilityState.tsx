import type { StockStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const LABELS: Record<StockStatus, string> = {
  available: "Còn hàng",
  unavailable: "Hết hàng",
  unknown: "Chưa rõ tình trạng",
};

const STYLES: Record<StockStatus, string> = {
  available: "text-green-700",
  unavailable: "text-destructive",
  unknown: "text-muted-foreground",
};

export function AvailabilityState({ status }: { status: StockStatus }) {
  return (
    <span data-testid={`stock-${status}`} className={cn("text-xs font-medium", STYLES[status])}>
      {LABELS[status]}
    </span>
  );
}
