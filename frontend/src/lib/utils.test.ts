import { describe, it, expect } from "vitest";
import {
  cn,
  getTopicColor,
  formatNumber,
  stripByPrefix,
  TOPIC_COLORS,
  CHART_TOOLTIP_STYLE,
} from "./utils";

describe("cn", () => {
  it("merges class names", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("handles conditional classes", () => {
    expect(cn("base", false && "hidden", "extra")).toBe("base extra");
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

describe("stripByPrefix", () => {
  it("removes 'By ' prefix", () => {
    expect(stripByPrefix("By Ahmed Ali")).toBe("Ahmed Ali");
  });

  it("is case-insensitive", () => {
    expect(stripByPrefix("by Sarah")).toBe("Sarah");
  });

  it("returns unchanged if no prefix", () => {
    expect(stripByPrefix("Ahmed Ali")).toBe("Ahmed Ali");
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
