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

export function stripByPrefix(name: string): string {
  return name.replace(/^By\s+/i, "");
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
