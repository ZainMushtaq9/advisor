import { describe, expect, it } from "vitest";
import { DEFAULT_API_URL, getApiBaseUrl } from "@/lib/env";

describe("getApiBaseUrl", () => {
  it("defaults to the local backend when unset", () => {
    expect(getApiBaseUrl(undefined)).toBe(DEFAULT_API_URL);
    expect(getApiBaseUrl("")).toBe(DEFAULT_API_URL);
  });

  it("strips a trailing slash", () => {
    expect(getApiBaseUrl("http://localhost:8000/")).toBe(
      "http://localhost:8000",
    );
  });

  it("keeps a valid http(s) URL", () => {
    expect(getApiBaseUrl("https://api.example.invalid")).toBe(
      "https://api.example.invalid",
    );
  });

  it("falls back safely on a non-http value (never trusts raw input)", () => {
    expect(getApiBaseUrl("not-a-url")).toBe(DEFAULT_API_URL);
    expect(getApiBaseUrl("javascript:alert(1)")).toBe(DEFAULT_API_URL);
  });
});
