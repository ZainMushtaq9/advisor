import { Suspense } from "react";
import { CompanyDetailClient } from "./detail-client";

// The client component reads useParams(), so it streams behind this
// Suspense boundary instead of prerendering (Cache Components mode).
export default function CompanyDetailPage() {
  return (
    <Suspense fallback={<p className="px-4 py-8 text-sm">Loading…</p>}>
      <CompanyDetailClient />
    </Suspense>
  );
}
