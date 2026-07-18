import type { PricePremiumVerdict, WorthPayingMore } from "@/lib/types";
import { formatVnd } from "@/lib/format";

const VERDICT_LABELS: Record<WorthPayingMore, string> = {
  yes: "Đáng để trả thêm",
  no: "Không đáng trả thêm",
  conditional: "Tùy nhu cầu",
  insufficient_data: "Chưa đủ dữ liệu",
};

export function PricePremiumPanel({ verdicts }: { verdicts: PricePremiumVerdict[] }) {
  if (verdicts.length === 0) return null;
  return (
    <div data-testid="price-premium-panel" className="rounded-md border p-3 text-sm">
      <p className="mb-1 font-medium">Có nên trả thêm tiền?</p>
      <ul className="flex flex-col gap-2">
        {verdicts.map((v, i) => (
          <li key={i} className="border-b pb-2 last:border-0">
            <p className="font-medium">{VERDICT_LABELS[v.worth_paying_more]} ({formatVnd(v.price_difference_vnd)})</p>
            <p>{v.what_you_get}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
