"use client";
import { Button } from "@/components/ui/button";

export function MoreProductsAction({ hasMore, onMore }: { hasMore: boolean; onMore: () => void }) {
  if (!hasMore) return null;
  return (
    <Button data-testid="more-products-action" className="bg-muted text-foreground" onClick={onMore}>
      Xem thêm sản phẩm
    </Button>
  );
}
