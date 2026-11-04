import Link from "next/link";
import { NAV_ITEMS } from "@/lib/nav";
import { ThemeToggle } from "./theme-toggle";

export function SiteHeader() {
  return (
    <header className="border-b border-neutral-200 bg-white dark:border-navy-700 dark:bg-navy-900">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-4">
        <Link
          href="/"
          className="text-lg font-bold tracking-tight text-navy-900 dark:text-white"
        >
          PSX Intelligence AI
        </Link>
        <nav aria-label="Primary" className="flex flex-wrap gap-x-4 gap-y-2">
          {NAV_ITEMS.filter((item) => item.href !== "/").map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-sm font-medium text-neutral-600 hover:text-navy-600 hover:underline dark:text-neutral-300 dark:hover:text-accent-400"
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="ml-auto">
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
