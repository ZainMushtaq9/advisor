"use client";

import { useEffect, useState } from "react";
import { ApiClient, ApiError } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/env";

export type ApiState<T> =
  | { state: "loading"; data: null; error: null }
  | { state: "ready"; data: T; error: null }
  | { state: "error"; data: null; error: string };

const LOADING: ApiState<never> = { state: "loading", data: null, error: null };

/**
 * Fetch one GET endpoint and report loading / ready / error states.
 * GET-only: the backend CORS policy allows GET and this hook never writes.
 *
 * Loading for a new path is derived during render (snapshot path mismatch),
 * never by calling setState inside the effect body, so a stale response for
 * a previous path is never shown for the current one.
 */
export function useApi<T>(path: string | null): ApiState<T> {
  const [snapshot, setSnapshot] = useState<{
    path: string | null;
    result: ApiState<T>;
  }>({ path: null, result: LOADING });

  useEffect(() => {
    if (path === null) return;
    let cancelled = false;
    const client = new ApiClient({ baseUrl: getApiBaseUrl() });
    client
      .get<T>(path)
      .then((data) => {
        if (!cancelled) {
          setSnapshot({ path, result: { state: "ready", data, error: null } });
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        const message =
          error instanceof ApiError
            ? `Backend request failed (${error.status}): ${error.message}`
            : "Backend request failed.";
        setSnapshot({ path, result: { state: "error", data: null, error: message } });
      });
    return () => {
      cancelled = true;
    };
  }, [path]);

  if (path === null) {
    return { state: "error", data: null, error: "No request made." };
  }
  if (snapshot.path !== path) {
    return LOADING;
  }
  return snapshot.result;
}
