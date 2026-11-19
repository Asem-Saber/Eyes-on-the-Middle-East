import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { Topic } from "@/lib/api";

const useTopics = vi.fn();
const navigate = vi.fn();
vi.mock("@/lib/queries", () => ({ useTopics: () => useTopics() }));
vi.mock("react-router-dom", () => ({ useNavigate: () => navigate }));

const DiscoveredTopics = (await import("./DiscoveredTopics")).default;

function topic(over: Partial<Topic> & { topic_id: number }): Topic {
  return {
    topic_key: over.topic_id + 100,
    model_version: "v1",
    topic_label: null,
    topic_summary: null,
    is_outlier: false,
    article_count: 0,
    ...over,
  };
}

const TOPICS = [
  topic({ topic_id: 0, topic_label: "تطورات الحرب في غزة", article_count: 1077 }),
  topic({ topic_id: -1, is_outlier: true, article_count: 499 }),
  topic({ topic_id: 3, topic_label: "تطورات الصراع في السودان", article_count: 160 }),
];

beforeEach(() => {
  useTopics.mockReset();
  navigate.mockReset();
  useTopics.mockReturnValue({ data: TOPICS, isLoading: false, isError: false });
});

describe("DiscoveredTopics", () => {
  it("lists topic labels with their article counts", () => {
    render(<DiscoveredTopics />);
    expect(screen.getByText("تطورات الحرب في غزة")).toBeInTheDocument();
    expect(screen.getByText("1,077")).toBeInTheDocument();
  });

  it("labels the outlier cluster rather than showing a bare -1", () => {
    render(<DiscoveredTopics />);
    expect(screen.getByText("غير مصنف")).toBeInTheDocument();
    expect(screen.queryByText("Topic -1")).not.toBeInTheDocument();
  });

  it("reports the full cluster count in the subtitle", () => {
    render(<DiscoveredTopics />);
    expect(screen.getByText(/top 10 of 3 clusters/i)).toBeInTheDocument();
  });

  it("caps the list so it cannot outgrow the row it shares", () => {
    useTopics.mockReturnValue({
      data: Array.from({ length: 40 }, (_, i) =>
        topic({ topic_id: i, topic_label: `موضوع ${i}`, article_count: 40 - i }),
      ),
      isLoading: false,
      isError: false,
    });
    render(<DiscoveredTopics />);
    expect(screen.getAllByRole("button")).toHaveLength(10);
  });

  it("navigates to the topic page on click", () => {
    render(<DiscoveredTopics />);
    fireEvent.click(screen.getByText("تطورات الصراع في السودان"));
    expect(navigate).toHaveBeenCalledWith("/topic/3");
  });

  it("does not advertise filtering it does not do", () => {
    render(<DiscoveredTopics />);
    expect(screen.queryByText(/click to filter/i)).not.toBeInTheDocument();
  });

  it("reports failure instead of an empty list", () => {
    useTopics.mockReturnValue({ data: undefined, isLoading: false, isError: true });
    render(<DiscoveredTopics />);
    expect(screen.getByText(/failed to load topics/i)).toBeInTheDocument();
  });
});
