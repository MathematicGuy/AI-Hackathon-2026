// Direct TypeScript mirror of the Pydantic contract (ARCHITECTURE.md §5.6, §8.2, §8.3).
// Field names and optionality match the source so the live swap needs no type changes.

export type AnswerType =
  | "clarification"
  | "recommendation"
  | "comparison"
  | "more_products"
  | "product_detail"
  | "no_match"
  | "guardrail_block"
  | "stop";

export type StockStatus = "available" | "unavailable" | "unknown";

export type Role = "best_overall" | "best_value" | "cheapest_qualified";

export type BadgeKind = Role | "best_for_primary_priority";

export type WorthPayingMore = "yes" | "no" | "conditional" | "insufficient_data";

export interface Evidence {
  field: string;
  value: string;
  source_url?: string;
}

export interface RoleWinner {
  product_id: string;
  role: Role;
  score?: number;
  evidence: Evidence[];
  reason_codes: string[];
}

export interface RoleWinners {
  best_overall?: RoleWinner;
  best_value?: RoleWinner;
  cheapest_qualified?: RoleWinner;
}

export interface Assumption {
  field: string;
  assumed_value: string;
  reason?: string;
}

export interface AirConditionerNeed {
  room_area_m2?: number;
  budget_vnd?: number;
  region_code?: string;
  priorities?: string[];
}

export interface ProductCitation {
  product_id: string;
  field: string;
  source_url: string;
  snapshot_at?: string;
}

export interface PricePremiumVerdict {
  cheaper_product_id: string;
  premium_product_id: string;
  worth_paying_more: WorthPayingMore;
  price_difference_vnd?: number;
  what_you_get: string;
}

// Spec fields — subset of NormalizedAirConditioner (§5.6).
export interface ProductSpec {
  product_id: string;
  name: string;
  brand: string;
  model?: string;
  sale_price_vnd?: number;
  list_price_vnd?: number;
  discount_percent?: number;
  stock_status: StockStatus;
  horsepower_hp?: number;
  cooling_capacity_btu?: number;
  recommended_room_area_min_m2?: number;
  recommended_room_area_max_m2?: number;
  inverter?: boolean;
  cspf?: number;
  energy_label_stars?: number;
  indoor_noise_min_db?: number;
  indoor_noise_max_db?: number;
  warranty_months?: number;
  rating?: number;
  sold_count?: number;
  source_url: string;
}

// Explanation fields (§8.2).
export interface ProductExplanation {
  why_it_fits: string;
  main_selling_point: string;
  practical_benefit: string;
  price: string;
  trade_offs: string[];
  when_not_to_choose: string;
  evidence: Evidence[];
  alternative_comparison?: string;
}

export interface ProductCard extends ProductSpec, ProductExplanation {
  badges: BadgeKind[];
  selection_reason?: string;
}

export interface RecommendationOutput {
  answer_type: AnswerType;
  session_id: string;
  request_id: string;
  trace_id: string;
  intent: string;
  customer_need: AirConditionerNeed;
  assumption_summary: Assumption[];
  clarification_question?: string;
  role_winners?: RoleWinners;
  product_cards: ProductCard[];
  price_premium_verdicts: PricePremiumVerdict[];
  next_question?: string;
  citations: ProductCitation[];
  has_more_products: boolean;
  next_cursor?: number;
  warnings: string[];
}

export interface AdvisorRequest {
  session_id?: string;
  request_id?: string;
  user_id?: string;
  message: string;
  region_code?: string;
}

export interface AdvisorResponse {
  session_id: string;
  request_id: string;
  trace_id: string;
  data: RecommendationOutput;
}

export interface AdvisorError {
  session_id?: string;
  request_id?: string;
  trace_id?: string;
  error_code: string;
  message: string;
  retryable: boolean;
}
