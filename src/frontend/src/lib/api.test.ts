import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after stubbing fetch
const { api, topicName, weekLabel } = await import("./api");

function jsonResponse(data: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? "OK" : "Error",
    json: () => Promise.resolve(data),
  };
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("api.stats", () => {
  it("calls the correct URL", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ articles_total: 10 }));
    const result = await api.stats();
    expect(result.articles_total).toBe(10);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/stats"));
  });
});

describe("api.topics", () => {
  it("returns topic array", async () => {
    const topics = [
      {
        topic_key: 1,
        topic_id: 0,
        model_version: "v1",
        topic_label: "Test",
        topic_summary: null,
        is_outlier: false,
        article_count: 5,
      },
    ];
    mockFetch.mockResolvedValueOnce(jsonResponse(topics));
    const result = await api.topics();
    expect(result).toHaveLength(1);
    expect(result[0].topic_label).toBe("Test");
    expect(result[0].article_count).toBe(5);
  });

  it("passes include_outliers through", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    await api.topics(false);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("include_outliers=false"));
  });
});

describe("api.articles", () => {
  it("builds query string from params", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ articles: [], total: 0, page: 1, pages: 0 }));
    await api.articles({ page: 2, limit: 5, topic: 3, search: "gaza" });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("page=2");
    expect(url).toContain("limit=5");
    expect(url).toContain("topic=3");
    expect(url).toContain("search=gaza");
  });

  it("omits null/undefined params", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ articles: [], total: 0, page: 1, pages: 0 }));
    await api.articles({ page: 1 });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).not.toContain("topic=");
    expect(url).not.toContain("search=");
  });

  it("keeps topic 0, which is a real cluster id", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ articles: [], total: 0, page: 1, pages: 0 }));
    await api.articles({ topic: 0 });
    expect(mockFetch.mock.calls[0][0] as string).toContain("topic=0");
  });
});

describe("api.topicDetail", () => {
  it("includes topic id in URL", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ topic_id: 5 }));
    await api.topicDetail(5);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("/topics/5"));
  });
});

describe("api.sources", () => {
  it("passes limit as query param", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    await api.sources(12);
    expect(mockFetch).toHaveBeenCalledWith(expect.stringContaining("limit=12"));
  });
});

describe("topicName", () => {
  it("prefers the LLM label", () => {
    expect(topicName({ topic_id: 3, topic_label: "Gaza" })).toBe("Gaza");
  });

  it("labels the outlier cluster", () => {
    expect(topicName({ topic_id: -1, topic_label: null })).toBe("غير مصنف");
  });

  it("falls back to the id", () => {
    expect(topicName({ topic_id: 7, topic_label: null })).toBe("Topic 7");
  });

  it("handles a missing topic", () => {
    expect(topicName({ topic_id: null })).toBe("—");
  });
});

describe("weekLabel", () => {
  it("zero-pads the week number", () => {
    expect(weekLabel({ iso_year: 2026, iso_week: 7, count: 1 })).toBe("2026-W07");
  });

  it("leaves two-digit weeks alone", () => {
    expect(weekLabel({ iso_year: 2026, iso_week: 42, count: 1 })).toBe("2026-W42");
  });
});

describe("error handling", () => {
  it("throws on non-OK response", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 500));
    await expect(api.stats()).rejects.toThrow("API 500");
  });

  it("throws on 404", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({}, 404));
    await expect(api.topicDetail(999)).rejects.toThrow("API 404");
  });
});
