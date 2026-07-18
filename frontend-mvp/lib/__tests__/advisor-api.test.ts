import { afterEach, describe, expect, it, vi } from "vitest";
import type { AdvisorRequest } from "@/lib/types";

const request: AdvisorRequest = {
  session_id: "sess_test",
  request_id: "req_test",
  message: "mua máy lạnh",
};

const originalMode = process.env.NEXT_PUBLIC_ADVISOR_MODE;
const originalApiUrl = process.env.NEXT_PUBLIC_ADVISOR_API_URL;

afterEach(() => {
  if (originalMode === undefined) delete process.env.NEXT_PUBLIC_ADVISOR_MODE;
  else process.env.NEXT_PUBLIC_ADVISOR_MODE = originalMode;

  if (originalApiUrl === undefined) delete process.env.NEXT_PUBLIC_ADVISOR_API_URL;
  else process.env.NEXT_PUBLIC_ADVISOR_API_URL = originalApiUrl;

  vi.unstubAllGlobals();
  vi.resetModules();
});

describe("sendMessage live configuration", () => {
  it("fails before fetch when the live API URL is blank", async () => {
    process.env.NEXT_PUBLIC_ADVISOR_MODE = "live";
    process.env.NEXT_PUBLIC_ADVISOR_API_URL = "   ";
    const fetchSpy = vi.fn();
    vi.stubGlobal("fetch", fetchSpy);
    vi.resetModules();

    const { sendMessage } = await import("@/lib/advisor-api");

    await expect(sendMessage(request)).rejects.toThrow(
      "advisor_live_mode_missing_api_url",
    );
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it("trims the live API URL and removes trailing slashes", async () => {
    process.env.NEXT_PUBLIC_ADVISOR_MODE = "live";
    process.env.NEXT_PUBLIC_ADVISOR_API_URL = " https://advisor.example/// ";
    const fetchSpy = vi.fn().mockResolvedValue(
      new Response("{}", {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchSpy);
    vi.resetModules();

    const { sendMessage } = await import("@/lib/advisor-api");
    await sendMessage(request);

    expect(fetchSpy).toHaveBeenCalledWith(
      "https://advisor.example/api/v1/advisor/respond",
      expect.any(Object),
    );
  });
});
