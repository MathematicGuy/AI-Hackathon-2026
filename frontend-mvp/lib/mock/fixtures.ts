import type {
  AnswerType,
  AdvisorResponse,
  RecommendationOutput,
} from "@/lib/types";
import {
  AC_DAIKIN,
  AC_PANASONIC,
  AC_LG,
  AC_SAMSUNG,
  MORE_PRODUCTS,
} from "@/lib/mock/products";

function base(
  answerType: AnswerType,
  sessionId: string,
  requestId: string,
): RecommendationOutput {
  return {
    answer_type: answerType,
    session_id: sessionId,
    request_id: requestId,
    trace_id: "trace_mock",
    intent: answerType,
    customer_need: { room_area_m2: 18, region_code: "SOUTH", priorities: ["tiết kiệm điện"] },
    assumption_summary: [],
    product_cards: [],
    price_premium_verdicts: [],
    citations: [],
    has_more_products: false,
    warnings: [],
  };
}

function recommendation(s: string, r: string): RecommendationOutput {
  return {
    ...base("recommendation", s, r),
    assumption_summary: [
      { field: "room_area_m2", assumed_value: "18 m²", reason: "Bạn chưa nêu diện tích nên tạm tính phòng ngủ tiêu chuẩn." },
      { field: "region_code", assumed_value: "Miền Nam", reason: "Suy ra từ khu vực mặc định." },
    ],
    role_winners: {
      best_overall: {
        product_id: AC_DAIKIN.product_id,
        role: "best_overall",
        score: 0.92,
        evidence: AC_DAIKIN.evidence,
        reason_codes: ["balanced_cspf_noise_price"],
      },
      best_value: {
        product_id: AC_DAIKIN.product_id,
        role: "best_value",
        score: 0.9,
        evidence: AC_DAIKIN.evidence,
        reason_codes: ["value_per_vnd"],
      },
      cheapest_qualified: {
        product_id: AC_PANASONIC.product_id,
        role: "cheapest_qualified",
        score: 0.8,
        evidence: AC_PANASONIC.evidence,
        reason_codes: ["lowest_price_meets_filters"],
      },
    },
    product_cards: [AC_DAIKIN, AC_PANASONIC, AC_LG, AC_SAMSUNG],
    price_premium_verdicts: [
      {
        cheaper_product_id: AC_PANASONIC.product_id,
        premium_product_id: AC_DAIKIN.product_id,
        worth_paying_more: "conditional",
        price_difference_vnd: 1500000,
        what_you_get: "Chạy êm hơn và tiết kiệm điện hơn (CSPF 5.2 so với 4.6).",
      },
    ],
    next_question: "Bạn muốn ưu tiên tiết kiệm điện hay độ ồn thấp hơn?",
    citations: [
      { product_id: AC_DAIKIN.product_id, field: "cspf", source_url: AC_DAIKIN.source_url },
      { product_id: AC_PANASONIC.product_id, field: "sale_price_vnd", source_url: AC_PANASONIC.source_url },
    ],
    has_more_products: true,
    next_cursor: 3,
  };
}

function comparison(s: string, r: string): RecommendationOutput {
  return {
    ...base("comparison", s, r),
    product_cards: [AC_DAIKIN, AC_PANASONIC],
    price_premium_verdicts: [
      {
        cheaper_product_id: AC_PANASONIC.product_id,
        premium_product_id: AC_DAIKIN.product_id,
        worth_paying_more: "yes",
        price_difference_vnd: 1500000,
        what_you_get: "Tiết kiệm điện và độ ồn thấp hơn cho phòng ngủ.",
      },
    ],
    citations: [
      { product_id: AC_DAIKIN.product_id, field: "cspf", source_url: AC_DAIKIN.source_url },
    ],
    next_question: "Bạn có muốn xem thêm phương án êm hơn không?",
  };
}

function moreProducts(s: string, r: string): RecommendationOutput {
  return {
    ...base("more_products", s, r),
    product_cards: MORE_PRODUCTS,
    citations: [
      { product_id: MORE_PRODUCTS[0].product_id, field: "warranty_months", source_url: MORE_PRODUCTS[0].source_url },
    ],
    has_more_products: false,
  };
}

function productDetail(s: string, r: string): RecommendationOutput {
  return {
    ...base("product_detail", s, r),
    product_cards: [AC_DAIKIN],
    citations: AC_DAIKIN.evidence.map((e) => ({
      product_id: AC_DAIKIN.product_id,
      field: e.field,
      source_url: e.source_url ?? AC_DAIKIN.source_url,
    })),
    next_question: "Bạn muốn kiểm tra tình trạng còn hàng ở khu vực nào?",
  };
}

function clarification(s: string, r: string): RecommendationOutput {
  return {
    ...base("clarification", s, r),
    clarification_question: "Ngân sách dự kiến của bạn khoảng bao nhiêu để mình lọc đúng nhóm máy?",
  };
}

function noMatch(s: string, r: string): RecommendationOutput {
  return {
    ...base("no_match", s, r),
    warnings: ["Không có máy lạnh nào đạt yêu cầu với ngân sách 5 triệu cho phòng 40m²."],
    next_question: "Bạn có thể nâng ngân sách hoặc giảm diện tích phòng không?",
  };
}

function guardrailBlock(s: string, r: string): RecommendationOutput {
  return {
    ...base("guardrail_block", s, r),
    warnings: ["Yêu cầu nằm ngoài phạm vi tư vấn máy lạnh hoặc vi phạm quy tắc sử dụng."],
  };
}

function stop(s: string, r: string): RecommendationOutput {
  return {
    ...base("stop", s, r),
    intent: "stop",
  };
}

const BUILDERS: Record<AnswerType, (s: string, r: string) => RecommendationOutput> = {
  recommendation,
  comparison,
  more_products: moreProducts,
  product_detail: productDetail,
  clarification,
  no_match: noMatch,
  guardrail_block: guardrailBlock,
  stop,
};

export function buildFixture(
  answerType: AnswerType,
  sessionId: string,
  requestId: string,
): AdvisorResponse {
  const data = BUILDERS[answerType](sessionId, requestId);
  return {
    session_id: sessionId,
    request_id: requestId,
    trace_id: data.trace_id,
    data,
  };
}
