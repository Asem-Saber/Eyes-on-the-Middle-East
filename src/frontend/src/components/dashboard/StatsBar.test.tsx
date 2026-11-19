import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import type { Stats } from "@/lib/api";

const useStats = vi.fn();
vi.mock("@/lib/queries", () => ({ useStats: () => useStats() }));

const StatsBar = (await import("./StatsBar")).default;

const STATS: Stats = {
  articles_total: 5154,
  topics_total: 85,
  sources_total: 1,
  outlier_articles: 499,
  coverage_start: "2026-05-23",
  coverage_end: "2026-11-09",
  last_loaded_at: "2026-11-19T09:30:00",
};

function loaded(stats: Partial<Stats>) {
  useStats.mockReturnValue({
    data: { ...STATS, ...stats },
    isLoading: false,
    isError: false,
  });
}

beforeEach(() => useStats.mockReset());

describe("StatsBar", () => {
  it("formats large counts with separators", () => {
    loaded({});
    render(<StatsBar />);
    expect(screen.getByText("5,154")).toBeInTheDocument();
    expect(screen.getByText("85")).toBeInTheDocument();
  });

  it("renders the coverage window as a month range", () => {
    loaded({});
    render(<StatsBar />);
    expect(screen.getByText("May 2026 – Nov 2026")).toBeInTheDocument();
  });

  it("collapses a single-month corpus to one label", () => {
    loaded({ coverage_start: "2026-05-01", coverage_end: "2026-05-28" });
    render(<StatsBar />);
    expect(screen.getByText("May 2026")).toBeInTheDocument();
  });

  it("shows a dash when the mart has no coverage dates yet", () => {
    loaded({ coverage_start: null, coverage_end: null, last_loaded_at: null });
    render(<StatsBar />);
    // Both the coverage period and the load timestamp fall back.
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  it("renders a skeleton while loading", () => {
    useStats.mockReturnValue({ data: undefined, isLoading: true, isError: false });
    const { container } = render(<StatsBar />);
    expect(screen.queryByText("Articles Loaded")).not.toBeInTheDocument();
    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("reports failure instead of rendering empty tiles", () => {
    useStats.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(<StatsBar />);
    expect(screen.getByText(/failed to load stats/i)).toBeInTheDocument();
  });
});
