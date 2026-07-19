export interface AgentRequest {
  session_id: string | null;
  message: string;
}

export interface AgentBadge {
  code: string;
  label: string;
}

export interface AgentHighlight {
  label: string;
  value: string | null;
}

export interface AgentPresentedProduct {
  sku: string;
  productidweb: string | null;
  name: string;
  brand: string | null;
  effective_price_vnd: number | null;
  list_price_vnd: number | null;
  discount_percent: number | null;
  promotion_text: string | null;
  badges: AgentBadge[];
  highlights: AgentHighlight[];
  image_url: string | null;
  product_url: string | null;
  rating: number | null;
  sold_count: number | null;
}

export interface AgentComparisonValue {
  sku: string;
  value: string | null;
}

export interface AgentComparisonRow {
  label: string;
  values: AgentComparisonValue[];
}

interface AgentPresentationBase {
  products: AgentPresentedProduct[];
  comparison_rows: AgentComparisonRow[];
  follow_up_questions: string[];
  warnings: string[];
}

export interface AgentTextPresentation extends AgentPresentationBase {
  type: "text";
  products: [];
  comparison_rows: [];
}

export interface AgentRecommendationPresentation extends AgentPresentationBase {
  type: "recommendation";
  comparison_rows: [];
}

export interface AgentComparisonPresentation extends AgentPresentationBase {
  type: "comparison";
}

export type AgentPresentation =
  | AgentTextPresentation
  | AgentRecommendationPresentation
  | AgentComparisonPresentation;

export interface AgentResponse {
  session_id: string;
  request_id: string | null;
  intent: string | null;
  text: string;
  flags: string[];
  presented_ids: string[];
  presentation?: AgentPresentation;
}
