import type { AnswerType } from "@/lib/types";

const has = (msg: string, terms: string[]): boolean =>
  terms.some((t) => msg.includes(t));

interface Matcher {
  answer_type: AnswerType;
  test: (msg: string) => boolean;
}

// Order matters: first match wins. Guardrail is checked early so injection /
// rude phrases are not swallowed by broader matchers. Clarification is the
// broad "phòng without budget" catch, placed last before the default.
const MATCHERS: Matcher[] = [
  { answer_type: "guardrail_block", test: (m) =>
      has(m, ["ngu", "đồ ngốc", "idiot", "stupid", "ignore previous", "bỏ qua hướng dẫn", "chính trị", "hack"]) },
  { answer_type: "comparison", test: (m) => has(m, ["so sánh", "compare"]) },
  { answer_type: "more_products", test: (m) => has(m, ["xem thêm", "thêm sản phẩm", "more"]) },
  { answer_type: "no_match", test: (m) =>
      has(m, ["5 triệu"]) && has(m, ["40m", "phòng khách lớn", "phòng lớn"]) },
  { answer_type: "product_detail", test: (m) => has(m, ["chi tiết", "detail"]) },
  { answer_type: "stop", test: (m) => has(m, ["cảm ơn", "cám ơn", "dừng", "stop", "thôi"]) },
  { answer_type: "clarification", test: (m) =>
      has(m, ["phòng"]) && !has(m, ["triệu", "ngân sách", "budget"]) },
];

export function resolveAnswerType(message: string): AnswerType {
  const msg = message.toLowerCase();
  for (const matcher of MATCHERS) {
    if (matcher.test(msg)) return matcher.answer_type;
  }
  return "recommendation";
}
