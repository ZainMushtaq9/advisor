/**
 * Public, non-secret environment configuration.
 *
 * NEXT_PUBLIC_API_URL is the only backend address the frontend needs.
 * It is a *public* base URL (never a key, token, or password) and defaults
 * to a local FastAPI dev server. No backend secret is ever hard-coded here.
 */
export const DEFAULT_API_URL = "http://localhost:8000";

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

/** Resolve the API base URL, falling back safely to the local default. */
export function getApiBaseUrl(
  raw: string | undefined = process.env.NEXT_PUBLIC_API_URL,
): string {
  const trimmed = (raw ?? "").trim().replace(/\/+$/, "");
  if (trimmed && isHttpUrl(trimmed)) return trimmed;
  return DEFAULT_API_URL;
}

/** App display name (public, non-secret). */
export const APP_NAME =
  process.env.NEXT_PUBLIC_APP_NAME?.trim() || "PSX Intelligence AI";
