import type { RecommendationOutput } from "@/lib/types";
import { dedupeProductCards } from "@/lib/dedupe";
import { ProductCard } from "@/components/advisor/ProductCard";
import { RecommendationSummary } from "@/components/advisor/RecommendationSummary";
import { PricePremiumPanel } from "@/components/advisor/PricePremiumPanel";
import { MoreProductsAction } from "@/components/advisor/MoreProductsAction";
import { AssumptionBanner } from "@/components/advisor/AssumptionBanner";
import { ClarificationCard } from "@/components/advisor/ClarificationCard";
import { NoMatchState } from "@/components/advisor/NoMatchState";
import { GuardrailState } from "@/components/advisor/GuardrailState";
import { ComparisonView } from "@/components/advisor/ComparisonView";
import { ProductDetailView } from "@/components/advisor/ProductDetailView";

export function AnswerRenderer({
  data,
  onMore,
}: {
  data: RecommendationOutput;
  onMore: () => void;
}) {
  switch (data.answer_type) {
    case "clarification":
      return <ClarificationCard question={data.clarification_question} />;
    case "comparison":
      return <ComparisonView data={data} />;
    case "product_detail":
      return <ProductDetailView data={data} />;
    case "no_match":
      return <NoMatchState warnings={data.warnings} nextQuestion={data.next_question} />;
    case "guardrail_block":
      return <GuardrailState warnings={data.warnings} />;
    case "stop":
      return (
        <div data-testid="answer-stop" className="rounded-md border p-4">
          <p className="text-sm">Cảm ơn bạn. Hẹn gặp lại khi bạn cần tư vấn máy lạnh.</p>
        </div>
      );
    case "recommendation":
    case "more_products": {
      const cards = dedupeProductCards(data.product_cards);
      return (
        <div data-testid={`answer-${data.answer_type}`} className="flex flex-col gap-3">
          <AssumptionBanner assumptions={data.assumption_summary} />
          <RecommendationSummary roleWinners={data.role_winners} />
          <div className="flex flex-col gap-3">
            {cards.map((c) => (
              <ProductCard key={c.product_id} card={c} citations={data.citations} />
            ))}
          </div>
          <PricePremiumPanel verdicts={data.price_premium_verdicts} />
          <MoreProductsAction hasMore={data.has_more_products} onMore={onMore} />
          {data.next_question && <p className="text-sm">{data.next_question}</p>}
        </div>
      );
    }
  }
}
