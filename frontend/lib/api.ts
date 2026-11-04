import { getApiBaseUrl } from "./env";
import type { ApiHealth } from "./types";

/** Error thrown by the typed API client. Never carries credentials. */
export class ApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface ApiClientOptions {
  baseUrl?: string;
  /** Milliseconds before a request is aborted. Default 10_000. */
  timeoutMs?: number;
}

/**
 * Minimal typed fetch client for the (future) FastAPI backend.
 * Phase 2 foundation: only a `/health` probe is defined. No other endpoint
 * is assumed to exist, and no request sends credentials or secrets.
 */
export class ApiClient {
  readonly baseUrl: string;
  private readonly timeoutMs: number;

  constructor(options: ApiClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? getApiBaseUrl();
    this.timeoutMs = options.timeoutMs ?? 10_000;
  }

  async get<T>(path: string): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "GET",
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new ApiError(
          `API request failed: ${response.status} ${response.statusText}`,
          response.status,
        );
      }
      return (await response.json()) as T;
    } catch (error) {
      if (error instanceof ApiError) throw error;
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new ApiError("API request timed out", 408);
      }
      throw new ApiError(
        `API request failed: ${error instanceof Error ? error.message : "unknown error"}`,
        0,
      );
    } finally {
      clearTimeout(timer);
    }
  }

  /** Probe backend health. Returns null (not an exception) when unreachable. */
  async health(): Promise<ApiHealth | null> {
    try {
      return await this.get<ApiHealth>("/health");
    } catch {
      return null;
    }
  }
}

/** Default client, pointed at NEXT_PUBLIC_API_URL or the local default. */
export const api = new ApiClient();
