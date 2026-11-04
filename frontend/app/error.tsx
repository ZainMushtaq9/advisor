"use client";

import { ErrorState } from "@/components/ui";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-8">
      <ErrorState
        title="This page could not be loaded"
        description="Something went wrong while rendering this foundation page. No data is shown because none was loaded."
        onRetry={reset}
      />
    </div>
  );
}
