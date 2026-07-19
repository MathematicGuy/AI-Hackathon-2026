import type {
  AgentBadge,
  AgentComparisonRow,
  AgentHighlight,
  AgentPresentation,
  AgentPresentedProduct,
  AgentRequest,
  AgentResponse,
} from "@/types/agent";

export const AGENT_RESPOND_PATH = "/api/v1/agent/respond";

const MAX_PRODUCTS = 10;
const MAX_COMPARISON_ROWS = 7;
const MAX_BADGES = 10;
const MAX_HIGHLIGHTS = 3;
const MAX_FOLLOW_UPS = 1;
const MAX_WARNINGS = 10;
const MAX_BADGE_CODE_LENGTH = 64;
const MAX_SKU_LENGTH = 128;
const MAX_NAME_LENGTH = 300;
const MAX_LABEL_LENGTH = 120;
const MAX_VALUE_LENGTH = 500;
const MAX_SESSION_ID_LENGTH = 256;
const MAX_RESPONSE_TEXT_LENGTH = 20_000;
const MAX_URL_LENGTH = 2_048;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(
  value: unknown,
  maxLength = MAX_VALUE_LENGTH,
): value is string {
  return (
    typeof value === "string" &&
    value.trim().length > 0 &&
    value.length <= maxLength
  );
}

function isNullableString(
  value: unknown,
  maxLength = MAX_VALUE_LENGTH,
): value is string | null {
  return value === null || isNonEmptyString(value, maxLength);
}

function isNullableNumberInRange(
  value: unknown,
  minimum: number,
  maximum: number,
): value is number | null {
  return (
    value === null ||
    (typeof value === "number" &&
      Number.isFinite(value) &&
      value >= minimum &&
      value <= maximum)
  );
}

function isNullableNonNegativeInteger(value: unknown): value is number | null {
  return (
    value === null ||
    (typeof value === "number" && Number.isSafeInteger(value) && value >= 0)
  );
}

function parseStringArray(
  value: unknown,
  maximumItems: number,
): string[] | undefined {
  if (
    !Array.isArray(value) ||
    value.length > maximumItems ||
    !value.every((item) => isNonEmptyString(item))
  ) {
    return undefined;
  }
  return [...new Set(value)];
}

function parseSafeUrl(value: unknown): string | null | undefined {
  if (value === null) {
    return null;
  }
  if (!isNonEmptyString(value, MAX_URL_LENGTH)) {
    return undefined;
  }
  const url = value.trim();
  if (url.startsWith("/") && !url.startsWith("//")) {
    return url;
  }
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:"
      ? url
      : null;
  } catch {
    return null;
  }
}

function parseBadge(value: unknown): AgentBadge | undefined {
  if (
    !isRecord(value) ||
    !isNonEmptyString(value.code, MAX_BADGE_CODE_LENGTH) ||
    !isNonEmptyString(value.label, MAX_LABEL_LENGTH)
  ) {
    return undefined;
  }
  return { code: value.code, label: value.label };
}

function parseHighlight(value: unknown): AgentHighlight | undefined {
  if (
    !isRecord(value) ||
    !isNonEmptyString(value.label, MAX_LABEL_LENGTH) ||
    !isNullableString(value.value, MAX_VALUE_LENGTH)
  ) {
    return undefined;
  }
  return { label: value.label, value: value.value };
}

function parseProduct(value: unknown): AgentPresentedProduct | undefined {
  if (!isRecord(value)) {
    return undefined;
  }
  const imageUrl = parseSafeUrl(value.image_url);
  const productUrl = parseSafeUrl(value.product_url);
  if (
    !isNonEmptyString(value.sku, MAX_SKU_LENGTH) ||
    !isNonEmptyString(value.name, MAX_NAME_LENGTH) ||
    !isNullableString(value.productidweb, MAX_SKU_LENGTH) ||
    !isNullableString(value.brand, MAX_LABEL_LENGTH) ||
    !isNullableNonNegativeInteger(value.effective_price_vnd) ||
    !isNullableNonNegativeInteger(value.list_price_vnd) ||
    !isNullableNumberInRange(value.discount_percent, 0, 100) ||
    !isNullableString(value.promotion_text, MAX_VALUE_LENGTH) ||
    !Array.isArray(value.badges) ||
    value.badges.length > MAX_BADGES ||
    !Array.isArray(value.highlights) ||
    value.highlights.length > MAX_HIGHLIGHTS ||
    imageUrl === undefined ||
    productUrl === undefined ||
    !isNullableNumberInRange(value.rating, 0, 5) ||
    !isNullableNonNegativeInteger(value.sold_count)
  ) {
    return undefined;
  }

  const badges = value.badges.map(parseBadge);
  const highlights = value.highlights.map(parseHighlight);
  if (
    badges.some((badge) => badge === undefined) ||
    highlights.some((highlight) => highlight === undefined) ||
    (value.discount_percent !== null &&
      value.discount_percent > 0 &&
      (value.effective_price_vnd === null ||
        value.list_price_vnd === null ||
        value.list_price_vnd <= value.effective_price_vnd))
  ) {
    return undefined;
  }

  const uniqueBadges = (badges as AgentBadge[]).filter(
    (badge, index, allBadges) =>
      allBadges.findIndex((candidate) => candidate.code === badge.code) === index,
  );

  return {
    sku: value.sku,
    productidweb: value.productidweb,
    name: value.name,
    brand: value.brand,
    effective_price_vnd: value.effective_price_vnd,
    list_price_vnd: value.list_price_vnd,
    discount_percent: value.discount_percent,
    promotion_text: value.promotion_text,
    badges: uniqueBadges,
    highlights: highlights as AgentHighlight[],
    image_url: imageUrl,
    product_url: productUrl,
    rating: value.rating,
    sold_count: value.sold_count,
  };
}

function parseComparisonRow(value: unknown): AgentComparisonRow | undefined {
  if (
    !isRecord(value) ||
    !isNonEmptyString(value.label, MAX_LABEL_LENGTH) ||
    !Array.isArray(value.values) ||
    value.values.length > MAX_PRODUCTS
  ) {
    return undefined;
  }

  const values = value.values.map((cell) => {
    if (
      !isRecord(cell) ||
      !isNonEmptyString(cell.sku, MAX_SKU_LENGTH) ||
      !isNullableString(cell.value, MAX_VALUE_LENGTH)
    ) {
      return undefined;
    }
    return { sku: cell.sku, value: cell.value };
  });
  if (values.some((cell) => cell === undefined)) {
    return undefined;
  }
  return { label: value.label, values: values as AgentComparisonRow["values"] };
}

function hasUniqueProductSkus(products: AgentPresentedProduct[]) {
  return new Set(products.map((product) => product.sku)).size === products.length;
}

function rowsAlignWithProducts(
  rows: AgentComparisonRow[],
  products: AgentPresentedProduct[],
) {
  const productSkus = new Set(products.map((product) => product.sku));
  return rows.every((row) => {
    const valueSkus = row.values.map((cell) => cell.sku);
    return (
      valueSkus.length === products.length &&
      new Set(valueSkus).size === products.length &&
      valueSkus.every((sku) => productSkus.has(sku))
    );
  });
}

export function parseAgentPresentation(
  value: unknown,
): AgentPresentation | undefined {
  if (
    !isRecord(value) ||
    !Array.isArray(value.products) ||
    value.products.length > MAX_PRODUCTS ||
    !Array.isArray(value.comparison_rows) ||
    value.comparison_rows.length > MAX_COMPARISON_ROWS
  ) {
    return undefined;
  }

  const products = value.products.map(parseProduct);
  const rows = value.comparison_rows.map(parseComparisonRow);
  const followUpQuestions = parseStringArray(
    value.follow_up_questions,
    MAX_FOLLOW_UPS,
  );
  const warnings = parseStringArray(value.warnings, MAX_WARNINGS);
  if (
    products.some((product) => product === undefined) ||
    rows.some((row) => row === undefined) ||
    followUpQuestions === undefined ||
    warnings === undefined
  ) {
    return undefined;
  }

  const parsedProducts = products as AgentPresentedProduct[];
  const parsedRows = rows as AgentComparisonRow[];
  const common = {
    products: parsedProducts,
    comparison_rows: parsedRows,
    follow_up_questions: followUpQuestions,
    warnings,
  };

  if (value.type === "text") {
    if (parsedProducts.length !== 0 || parsedRows.length !== 0) {
      return undefined;
    }
    return { ...common, type: "text", products: [], comparison_rows: [] };
  }

  if (value.type === "recommendation") {
    if (
      parsedProducts.length === 0 ||
      parsedRows.length !== 0 ||
      !hasUniqueProductSkus(parsedProducts)
    ) {
      return undefined;
    }
    return { ...common, type: "recommendation", comparison_rows: [] };
  }

  if (value.type === "comparison") {
    if (
      parsedProducts.length < 2 ||
      !hasUniqueProductSkus(parsedProducts) ||
      !rowsAlignWithProducts(parsedRows, parsedProducts)
    ) {
      return undefined;
    }
    return { ...common, type: "comparison" };
  }

  return undefined;
}

export function parseAgentResponse(value: unknown): AgentResponse {
  if (
    !isRecord(value) ||
    !isNonEmptyString(value.session_id, MAX_SESSION_ID_LENGTH) ||
    !isNonEmptyString(value.text, MAX_RESPONSE_TEXT_LENGTH)
  ) {
    throw new Error("Invalid agent response envelope");
  }

  const response: AgentResponse = {
    session_id: value.session_id,
    request_id:
      typeof value.request_id === "string" ? value.request_id : null,
    intent: typeof value.intent === "string" ? value.intent : null,
    text: value.text,
    flags: parseStringArray(value.flags, MAX_WARNINGS) ?? [],
    presented_ids: parseStringArray(value.presented_ids, MAX_PRODUCTS) ?? [],
  };
  const presentation = parseAgentPresentation(value.presentation);
  if (presentation) {
    response.presentation = presentation;
  }
  return response;
}

export async function requestAgentReply(
  request: AgentRequest,
  fetcher: typeof fetch = fetch,
): Promise<AgentResponse> {
  const response = await fetcher(AGENT_RESPOND_PATH, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    throw new Error(`Agent request failed with HTTP ${response.status}`);
  }
  return parseAgentResponse(await response.json());
}
