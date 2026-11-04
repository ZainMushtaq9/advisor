import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto w-full max-w-6xl px-4 py-16 text-center">
      <h1 className="text-3xl font-bold text-navy-900 dark:text-white">
        Page not found
      </h1>
      <p className="mt-2 text-neutral-600 dark:text-neutral-300">
        This route does not exist in the Phase 2 foundation. No data is shown
        here.
      </p>
      <Link
        href="/"
        className="mt-6 inline-block font-medium text-accent-500 underline"
      >
        Back to Home
      </Link>
    </div>
  );
}
