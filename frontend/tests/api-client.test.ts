import { describe, expect, it, vi, afterEach } from "vitest";
import { ApiClient, ApiError } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

describe("ApiClient", () => {
  it("returns parsed JSON on success", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ok" }),
      }),
    );
    const client = new ApiClient({ baseUrl: "http://localhost:8000" });
    await expect(client.get("/health")).resolves.toEqual({ status: "ok" });
  });

  it("throws ApiError with the HTTP status on failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
      }),
    );
    const client = new ApiClient({ baseUrl: "http://localhost:8000" });
    await expect(client.get("/health")).rejects.toBeInstanceOf(ApiError);
  });

  it("health() returns null (not an exception) when unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("refused")));
    const client = new ApiClient({ baseUrl: "http://localhost:8000" });
    await expect(client.health()).resolves.toBeNull();
  });
});
