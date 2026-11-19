import { describe, it, expect } from "vitest";
import { pivot } from "./trends";
import type { Topic, TopicTrends } from "./api";

// Recharts needs a measured container, which jsdom never gives it, so the
// chart itself is not asserted on. The reshape in front of it is where the
// logic lives: the API returns one point list per topic id, Recharts wants
// one row per week with a column per series.

function topic(id: number, label: string | null): Topic {
  return {
    topic_key: id + 1,
    topic_id: id,
    model_version: "v1",
    topic_label: label,
    topic_summary: null,
    is_outlier: id === -1,
    article_count: 10,
  };
}

const TRENDS: TopicTrends = {
  "0": [
    { iso_year: 2026, iso_week: 7, count: 12 },
    { iso_year: 2026, iso_week: 9, count: 4 },
  ],
  "3": [{ iso_year: 2026, iso_week: 9, count: 6 }],
};

describe("pivot", () => {
  it("produces one row per distinct week", () => {
    const { data } = pivot(TRENDS, [topic(0, "غزة"), topic(3, "السودان")]);
    expect(data.map((r) => r.week)).toEqual(["2026-W07", "2026-W09"]);
  });

  it("zero-fills weeks a topic has no points for", () => {
    const { data } = pivot(TRENDS, [topic(0, "غزة"), topic(3, "السودان")]);
    // السودان only reported W09, so its W07 cell must be 0, not undefined —
    // Recharts breaks the line on undefined.
    expect(data[0]["السودان"]).toBe(0);
    expect(data[1]["السودان"]).toBe(6);
  });

  it("sorts weeks chronologically across a year boundary", () => {
    const { data } = pivot(
      {
        "0": [
          { iso_year: 2027, iso_week: 2, count: 1 },
          { iso_year: 2026, iso_week: 51, count: 2 },
        ],
      },
      [topic(0, "غزة")],
    );
    expect(data.map((r) => r.week)).toEqual(["2026-W51", "2027-W02"]);
  });

  it("names each series after its topic label", () => {
    const { series } = pivot(TRENDS, [topic(0, "غزة"), topic(3, "السودان")]);
    expect(series.map((s) => s.key)).toEqual(["غزة", "السودان"]);
  });

  it("disambiguates topics that share a label", () => {
    // LLM-generated labels are not unique; identical column keys would make
    // one series overwrite the other.
    const { series } = pivot(TRENDS, [topic(0, "غزة"), topic(3, "غزة")]);
    expect(series.map((s) => s.key)).toEqual(["غزة", "غزة (#3)"]);
  });

  it("falls back to the id when a topic is missing from the list", () => {
    const { series } = pivot({ "9": [{ iso_year: 2026, iso_week: 1, count: 1 }] }, []);
    expect(series[0].key).toBe("Topic 9");
  });

  it("gives every series a colour", () => {
    const { series } = pivot(TRENDS, [topic(0, "غزة"), topic(3, "السودان")]);
    expect(series.every((s) => s.color.startsWith("hsl("))).toBe(true);
  });

  it("returns empty structures for empty trends", () => {
    const { data, series } = pivot({}, []);
    expect(data).toEqual([]);
    expect(series).toEqual([]);
  });
});
