import type { ProductCard as ProductCardType, ProductCitation, BadgeKind } from "@/lib/types";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AvailabilityState } from "@/components/advisor/AvailabilityState";
import { SourceDrawer } from "@/components/advisor/SourceDrawer";
import { formatVnd, display } from "@/lib/format";

const BADGE_LABELS: Record<BadgeKind, string> = {
  best_overall: "Tốt nhất tổng thể",
  best_value: "Đáng tiền nhất",
  cheapest_qualified: "Rẻ nhất đạt yêu cầu",
  best_for_primary_priority: "Hợp ưu tiên của bạn",
};

export function ProductCard({
  card,
  citations,
}: {
  card: ProductCardType;
  citations: ProductCitation[];
}) {
  const cardCitations = citations.filter((c) => c.product_id === card.product_id);
  return (
    <Card data-testid={`product-card-${card.product_id}`} className="w-full">
      <CardHeader>
        <div className="flex flex-wrap items-center gap-2">
          {card.badges.map((b) => (
            <Badge key={b}>{BADGE_LABELS[b]}</Badge>
          ))}
          <AvailabilityState status={card.stock_status} />
        </div>
        <CardTitle>{display(card.name)}</CardTitle>
        <p className="text-sm text-muted-foreground">
          {display(card.brand)} · {formatVnd(card.sale_price_vnd)}
        </p>
        {card.selection_reason && (
          <p data-testid="selection-reason" className="text-xs italic text-muted-foreground">
            Lý do đề xuất: {card.selection_reason}
          </p>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-2 text-sm">
        <p><span className="font-medium">Vì sao phù hợp:</span> {display(card.why_it_fits)}</p>
        <p><span className="font-medium">Điểm nổi bật:</span> {display(card.main_selling_point)}</p>
        <p><span className="font-medium">Lợi ích thực tế:</span> {display(card.practical_benefit)}</p>
        <div>
          <span className="font-medium">Đánh đổi:</span>
          <ul className="list-disc pl-5">
            {card.trade_offs.length > 0
              ? card.trade_offs.map((t, i) => <li key={i}>{t}</li>)
              : <li>không có</li>}
          </ul>
        </div>
        <p><span className="font-medium">Khi nào không nên chọn:</span> {display(card.when_not_to_choose)}</p>
        {card.alternative_comparison && (
          <p><span className="font-medium">So với lựa chọn khác:</span> {card.alternative_comparison}</p>
        )}
      </CardContent>
      <CardFooter>
        <SourceDrawer citations={cardCitations} />
      </CardFooter>
    </Card>
  );
}
