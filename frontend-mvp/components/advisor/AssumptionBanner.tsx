import type { Assumption } from "@/lib/types";

export function AssumptionBanner({
  assumptions,
  summaryText,
}: {
  assumptions: Assumption[];
  summaryText?: string;
}) {
  if (assumptions.length === 0 && !summaryText) return null;
  return (
    <div data-testid="assumption-banner" className="rounded-md border bg-muted p-3 text-sm">
      <p className="mb-1 font-medium">Giả định đã dùng để tư vấn:</p>
      {summaryText && <p className="mb-1">{summaryText}</p>}
      <ul className="list-disc pl-5">
        {assumptions.map((a, i) => (
          <li key={`${a.field}-${i}`}>
            <span className="font-medium">{a.field}:</span> {a.assumed_value}
            {a.reason ? ` — ${a.reason}` : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}
