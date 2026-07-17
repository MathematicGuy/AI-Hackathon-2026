import type { AdvisorResponse } from "@/lib/types";
import { AnswerRenderer } from "@/components/advisor/AnswerRenderer";
import { Skeleton } from "@/components/ui/skeleton";

export interface Turn {
  user: string;
  response: AdvisorResponse;
}

export function MessageList({
  turns,
  loading,
  onMore,
}: {
  turns: Turn[];
  loading: boolean;
  onMore: (turnIndex: number) => void;
}) {
  return (
    <div className="flex flex-col gap-4">
      {turns.map((turn, i) => (
        <div key={i} className="flex flex-col gap-2">
          <p className="self-end rounded-md bg-primary px-3 py-2 text-sm text-primary-foreground">
            {turn.user}
          </p>
          <AnswerRenderer data={turn.response.data} onMore={() => onMore(i)} />
        </div>
      ))}
      {loading && (
        <div data-testid="loading-skeleton" className="flex flex-col gap-2">
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-24 w-full" />
        </div>
      )}
    </div>
  );
}
