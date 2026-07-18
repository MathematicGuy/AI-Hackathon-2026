import type { RoleWinners, Role } from "@/lib/types";

const ROLE_LABELS: Record<Role, string> = {
  best_overall: "Tốt nhất tổng thể",
  best_value: "Đáng tiền nhất",
  cheapest_qualified: "Rẻ nhất đạt yêu cầu",
};

export function RecommendationSummary({ roleWinners }: { roleWinners?: RoleWinners }) {
  if (!roleWinners) return null;
  const roles: Role[] = ["best_overall", "best_value", "cheapest_qualified"];
  const present = roles.filter((r) => roleWinners[r]);
  if (present.length === 0) return null;
  return (
    <div data-testid="recommendation-summary" className="rounded-md border p-3 text-sm">
      <p className="mb-1 font-medium">Kết quả xếp hạng:</p>
      <ul className="list-disc pl-5">
        {present.map((r) => (
          <li key={r}>
            <span className="font-medium">{ROLE_LABELS[r]}:</span> {roleWinners[r]!.product_id}
          </li>
        ))}
      </ul>
    </div>
  );
}
