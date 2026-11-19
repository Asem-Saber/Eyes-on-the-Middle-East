import { describe, it, expect } from "vitest";
import {
  cn,
  getTopicColor,
  formatNumber,
  formatArticleDate,
  TOPIC_COLORS,
  CHART_TOOLTIP_STYLE,
} from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    const hidden = false;
    expect(cn("base", hidden && "hidden", "extra")).toBe("base extra");
  });

  it("deduplicates tailwind conflicts", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
  });
});

describe("getTopicColor", () => {
  it("returns color for valid index", () => {
    expect(getTopicColor(0)).toBe(TOPIC_COLORS[0]);
    expect(getTopicColor(3)).toBe(TOPIC_COLORS[3]);
  });

  it("cycles when index exceeds array length", () => {
    expect(getTopicColor(10)).toBe(TOPIC_COLORS[0]);
    expect(getTopicColor(11)).toBe(TOPIC_COLORS[1]);
  });
});

describe("formatNumber", () => {
  it("formats integers with commas", () => {
    expect(formatNumber(1000)).toBe("1,000");
    expect(formatNumber(1234567)).toBe("1,234,567");
  });

  it("handles zero", () => {
    expect(formatNumber(0)).toBe("0");
  });

  it("handles small numbers without commas", () => {
    expect(formatNumber(42)).toBe("42");
  });
});

describe("formatArticleDate", () => {
  it("formats an ISO date", () => {
    expect(formatArticleDate("2026-03-14")).toBe("Mar 14, 2026");
  });

  it("accepts custom options", () => {
    expect(formatArticleDate("2026-03-14", { month: "long", year: "numeric" })).toBe("March 2026");
  });

  it("falls back when the date is null", () => {
    expect(formatArticleDate(null)).toBe("No Date");
  });

  it("falls back when the date is unparseable", () => {
    expect(formatArticleDate("not-a-date")).toBe("No Date");
  });
});

describe("CHART_TOOLTIP_STYLE", () => {
  it("has contentStyle and labelStyle", () => {
    expect(CHART_TOOLTIP_STYLE).toHaveProperty("contentStyle");
    expect(CHART_TOOLTIP_STYLE).toHaveProperty("labelStyle");
  });

  it("contentStyle has expected properties", () => {
    expect(CHART_TOOLTIP_STYLE.contentStyle).toHaveProperty("background");
    expect(CHART_TOOLTIP_STYLE.contentStyle).toHaveProperty("borderRadius");
    expect(CHART_TOOLTIP_STYLE.contentStyle).toHaveProperty("fontSize");
  });
});
