import type { AdvisorRequest, AdvisorResponse } from "@/lib/types";
import { ensureSessionId, ensureRequestId } from "@/lib/ids";
import { resolveAnswerType } from "@/lib/mock/scenarios";
import { buildFixture } from "@/lib/mock/fixtures";

const MODE = process.env.NEXT_PUBLIC_ADVISOR_MODE ?? "mock";
const API_URL = process.env.NEXT_PUBLIC_ADVISOR_API_URL ?? "";

// THE single swap point. Components import only this for data.
export async function sendMessage(req: AdvisorRequest): Promise<AdvisorResponse> {
  const session_id = ensureSessionId(req.session_id);
  const request_id = ensureRequestId(req.request_id);
  const filled: AdvisorRequest = { ...req, session_id, request_id };

  if (MODE === "live") {
    const res = await fetch(`${API_URL}/api/v1/advisor/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(filled),
    });
    if (!res.ok) throw new Error(`advisor_http_${res.status}`);
    return (await res.json()) as AdvisorResponse;
  }

  // mock: artificial delay so loading/skeleton states are visible.
  await new Promise((resolve) => setTimeout(resolve, 400));
  const answerType = resolveAnswerType(filled.message);
  return buildFixture(answerType, session_id, request_id);
}
