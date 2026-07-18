import type { ProductCard, BadgeKind } from "./types";

// Render a product once even when it carries multiple badges. Merge badges by
// product_id, preserving first-seen order. UI guard only — never re-ranks.
export function dedupeProductCards(cards: ProductCard[]): ProductCard[] {
  const byId = new Map<string, ProductCard>();
  for (const card of cards) {
    const existing = byId.get(card.product_id);
    if (!existing) {
      byId.set(card.product_id, { ...card, badges: [...card.badges] });
      continue;
    }
    const merged: BadgeKind[] = [...existing.badges];
    for (const badge of card.badges) {
      if (!merged.includes(badge)) merged.push(badge);
    }
    existing.badges = merged;
  }
  return [...byId.values()];
}
