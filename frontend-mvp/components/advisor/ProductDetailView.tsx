import type { RecommendationOutput } from "@/lib/types";
import { ProductCard } from "@/components/advisor/ProductCard";

export function ProductDetailView({ data }: { data: RecommendationOutput }) {
  return (
    <div data-testid="answer-product_detail" className="flex flex-col gap-3">
      <p className="font-medium">Chi tiết sản phẩm</p>
      {data.product_cards.map((c) => (
        <ProductCard key={c.product_id} card={c} citations={data.citations} />
      ))}
      {data.next_question && <p className="text-sm">{data.next_question}</p>}
    </div>
  );
}
