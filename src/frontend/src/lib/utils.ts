import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const TOPIC_COLORS = [
  "hsl(38, 92%, 55%)",   // gold
  "hsl(14, 80%, 55%)",   // ember
  "hsl(180, 60%, 45%)",  // teal
  "hsl(260, 50%, 55%)",  // violet
  "hsl(330, 60%, 55%)",  // rose
  "hsl(90, 50%, 45%)",   // lime
  "hsl(200, 70%, 50%)",  // sky
  "hsl(45, 80%, 50%)",   // amber
  "hsl(0, 72%, 47%)",    // red
  "hsl(160, 55%, 40%)",  // emerald
] as const;

export function getTopicColor(index: number): string {
  return TOPIC_COLORS[index % TOPIC_COLORS.length];
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat("en-US").format(n);
}

/**
 * v1 stored the literal string "No Date"; the marts use a nullable date, so
 * every call site needs the same null guard.
 */
export function formatArticleDate(
  date: string | null | undefined,
  options: Intl.DateTimeFormatOptions = { month: "short", day: "numeric", year: "numeric" },
): string {
  if (!date) return "No Date";
  // A bare YYYY-MM-DD parses as UTC midnight, which renders a day early west of
  // Greenwich. Anchoring it to local midnight keeps the printed day honest.
  const local = /^\d{4}-\d{2}-\d{2}$/.test(date) ? `${date}T00:00:00` : date;
  const parsed = new Date(local);
  return Number.isNaN(parsed.getTime()) ? "No Date" : parsed.toLocaleDateString("en-US", options);
}

export const CHART_TOOLTIP_STYLE = {
  contentStyle: {
    background: "hsl(240,8%,8%)",
    border: "1px solid hsl(240,10%,16%)",
    borderRadius: "8px",
    fontSize: "13px",
    fontFamily: "var(--font-body)",
  },
  labelStyle: { color: "hsl(40,20%,92%)" },
} as const;
