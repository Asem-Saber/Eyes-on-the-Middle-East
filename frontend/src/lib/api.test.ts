import { describe, it, expect, vi, beforeEach } from "vitest";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Import after stubbing fetch
const { api } = await import("./api");

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
    mockFetch.mockResolvedValueOnce(jsonResponse({ articles_scraped: 10 }));
    const result = await api.stats();
    expect(result.articles_scraped).toBe(10);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/stats")
    );
  });
});

describe("api.topics", () => {
  it("returns topic array", async () => {
    const topics = [{ topic_id: 0, name: "Test", keywords: [], count: 5 }];
    mockFetch.mockResolvedValueOnce(jsonResponse(topics));
    const result = await api.topics();
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Test");
  });
});

describe("api.articles", () => {
  it("builds query string from params", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ articles: [], total: 0, page: 1, pages: 0 })
    );
    await api.articles({ page: 2, limit: 5, topic: 3, search: "gaza" });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).toContain("page=2");
    expect(url).toContain("limit=5");
    expect(url).toContain("topic=3");
    expect(url).toContain("search=gaza");
  });

  it("omits null/undefined params", async () => {
    mockFetch.mockResolvedValueOnce(
      jsonResponse({ articles: [], total: 0, page: 1, pages: 0 })
    );
    await api.articles({ page: 1 });
    const url = mockFetch.mock.calls[0][0] as string;
    expect(url).not.toContain("topic=");
    expect(url).not.toContain("search=");
  });
});

describe("api.topicDetail", () => {
  it("includes topic id in URL", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse({ topic_id: 5 }));
    await api.topicDetail(5);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/topics/5")
    );
  });
});

describe("api.authors", () => {
  it("passes limit as query param", async () => {
    mockFetch.mockResolvedValueOnce(jsonResponse([]));
    await api.authors(12);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("limit=12")
    );
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
