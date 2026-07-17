import type { RecommendationOutput } from "@/lib/types";
import { dedupeProductCards } from "@/lib/dedupe";
import { ProductCard } from "@/components/advisor/ProductCard";
import { PricePremiumPanel } from "@/components/advisor/PricePremiumPanel";

export function ComparisonView({ data }: { data: RecommendationOutput }) {
  const cards = dedupeProductCards(data.product_cards);
  return (
    <div data-testid="answer-comparison" className="flex flex-col gap-3">
      <p className="font-medium">So sánh sản phẩm</p>
      <div className="grid gap-3 md:grid-cols-2">
        {cards.map((c) => (
          <ProductCard key={c.product_id} card={c} citations={data.citations} />
        ))}
      </div>
      <PricePremiumPanel verdicts={data.price_premium_verdicts} />
      {data.next_question && <p className="text-sm">{data.next_question}</p>}
    </div>
  );
}
