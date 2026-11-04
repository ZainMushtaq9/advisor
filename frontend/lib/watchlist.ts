"use client";

import { useCallback, useSyncExternalStore } from "react";

const KEY = "psx-intelligence-ai-watchlist-v1";

const listeners = new Set<() => void>();

// useSyncExternalStore requires getSnapshot() to return the SAME reference
// while the store is unchanged; a fresh array on every call causes React
// error #185 (maximum update depth exceeded). Cache by raw string.
let cachedRaw: string | null | undefined;
let cachedList: string[] = [];

function readWatchlist(): string[] {
  if (typeof window === "undefined") return [];
  const raw = window.localStorage.getItem(KEY);
  if (raw === cachedRaw) return cachedList;
  cachedRaw = raw;
  try {
    if (!raw) {
      cachedList = [];
    } else {
      const parsed: unknown = JSON.parse(raw);
      cachedList = Array.isArray(parsed)
        ? parsed.filter((t): t is string => typeof t === "string")
        : [];
    }
  } catch {
    cachedList = [];
  }
  return cachedList;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  const onStorage = () => listener();
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

function emit() {
  listeners.forEach((listener) => listener());
}

/**
 * Watchlist stored ONLY in this browser's localStorage. There is no user
 * account or server-side watchlist in this project, so a watchlist cannot
 * follow the user to another device. Tickers are validated against the
 * registry by the pages that use this hook; nothing here invents a symbol.
 * Implemented with useSyncExternalStore so reads stay consistent across
 * server render and hydration without effect-body setState.
 */
export function useWatchlist() {
  const tickers = useSyncExternalStore(subscribe, readWatchlist, () => []);

  const toggle = useCallback((ticker: string) => {
    const current = readWatchlist();
    const next = current.includes(ticker)
      ? current.filter((t) => t !== ticker)
      : [...current, ticker];
    try {
      window.localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      // Storage unavailable: keep the previous list.
      return;
    }
    emit();
  }, []);

  return { tickers, toggle };
}
