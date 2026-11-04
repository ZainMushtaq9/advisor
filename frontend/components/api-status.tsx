"use client";

import { useEffect, useState } from "react";
import { ApiClient } from "@/lib/api";
import { getApiBaseUrl } from "@/lib/env";
import { Badge } from "./ui";

/**
 * Foundation backend-status indicator. It probes GET /health once and
 * reports "not connected" when nothing answers — the expected Phase 2
 * state while other teams build the backend. It never invents data.
 */
export function ApiStatus() {
  const [state, setState] = useState<"checking" | "up" | "down">("checking");
  const baseUrl = getApiBaseUrl();

  useEffect(() => {
    let cancelled = false;
    new ApiClient({ baseUrl }).health().then((health) => {
      if (!cancelled) setState(health ? "up" : "down");
    });
    return () => {
      cancelled = true;
    };
  }, [baseUrl]);

  if (state === "checking") {
    return <Badge>Checking backend…</Badge>;
  }
  return state === "up" ? (
    <Badge tone="info">Backend reachable</Badge>
  ) : (
    <Badge>Backend not connected yet</Badge>
  );
}
