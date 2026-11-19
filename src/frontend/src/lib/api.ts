// Client for the v2 API (src/api), which reads the dbt marts rather than a
// single articles table. Differences from v1 that matter here:
//
//   * Articles carry `source_name` (dim_source) instead of `author`. The
//     pipeline no longer keeps a Publisher field.
//   * Topics have no `keywords`. dim_topic stores the LLM label and summary;
//     the c-TF-IDF terms stay in the BentoML service.
//   * Topics are model-scoped: `topic_key` derives from (model_version,
//     topic_id), so a retrain produces a fresh set of rows.
//   * Trends come back keyed by topic id with ISO year/week, not as a flat
//     array keyed by topic name.

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API = `${BASE}/api/v1`;

export interface Topic {
  topic_key: number;
  topic_id: number;
  model_version: string | null;
  topic_label: string | null;
  topic_summary: string | null;
  is_outlier: boolean;
  article_count: number;
}

export interface Article {
  article_id: string;
  headline: string;
  summary: string | null;
  url: string;
  published_date: string | null;
  source_name: string | null;
  topic_id: number | null;
  topic_label: string | null;
  word_count: number;
}

export interface ArticleDetail extends Article {
  full_content: string[];
  paragraph_count: number;
  topic_summary: string | null;
  model_version: string | null;
  is_outlier: boolean;
}

export interface PaginatedArticles {
  articles: Article[];
  total: number;
  page: number;
  pages: number;
}

export interface Stats {
  articles_total: number;
  topics_total: number;
  sources_total: number;
  outlier_articles: number;
  coverage_start: string | null;
  coverage_end: string | null;
  /** When the staging loader last wrote, not when the scraper last ran. */
  last_loaded_at: string | null;
}

export interface TopicDistribution {
  topic_id: number;
  topic_label: string | null;
  count: number;
}

export interface TopicTrendPoint {
  iso_year: number;
  iso_week: number;
  count: number;
}

/** Keyed by topic id — the API returns an object, not an array. */
export type TopicTrends = Record<string, TopicTrendPoint[]>;

export interface Source {
  source_key: number;
  source_name: string | null;
  domain: string | null;
  article_count: number;
}

export interface MonthlyVolume {
  month: string;
  count: number;
}

export interface TopicStats {
  article_count: number;
  first_published: string | null;
  last_published: string | null;
}

export interface TopicDetail extends Topic {
  stats: TopicStats;
  trend: TopicTrendPoint[];
  monthly_volume: MonthlyVolume[];
  articles: Article[];
}

// ── Helpers ─────────────────────────────────────────────────

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

/** "2026-W07" — stable sort key and axis label for the weekly charts. */
export function weekLabel(point: TopicTrendPoint): string {
  return `${point.iso_year}-W${String(point.iso_week).padStart(2, "0")}`;
}

/** Topic -1 has no label; everything else falls back to its id. */
export function topicName(topic: {
  topic_id: number | null;
  topic_label?: string | null;
}): string {
  if (topic.topic_label) return topic.topic_label;
  if (topic.topic_id === -1) return "غير مصنف";
  return topic.topic_id == null ? "—" : `Topic ${topic.topic_id}`;
}

// ── Endpoints ───────────────────────────────────────────────
// Trailing slashes match the FastAPI routes exactly, avoiding a 307 per call.

export const api = {
  stats: () => get<Stats>(`${API}/stats/`),

  topics: (includeOutliers = true) =>
    get<Topic[]>(`${API}/topics/?include_outliers=${includeOutliers}`),
  topicDistribution: (limit = 20) =>
    get<TopicDistribution[]>(`${API}/topics/distribution?limit=${limit}`),
  topicTrends: (topics = 5) => get<TopicTrends>(`${API}/topics/trends?topics=${topics}`),
  topicDetail: (id: number, articles = 20) =>
    get<TopicDetail>(`${API}/topics/${id}?articles=${articles}`),

  sources: (limit = 8) => get<Source[]>(`${API}/sources/?limit=${limit}`),

  articles: (
    params: {
      page?: number;
      limit?: number;
      topic?: number | null;
      search?: string;
      date_from?: string;
      date_to?: string;
    } = {},
  ) => {
    const qs = new URLSearchParams();
    if (params.page) qs.set("page", String(params.page));
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.topic != null) qs.set("topic", String(params.topic));
    if (params.search) qs.set("search", params.search);
    if (params.date_from) qs.set("date_from", params.date_from);
    if (params.date_to) qs.set("date_to", params.date_to);
    return get<PaginatedArticles>(`${API}/articles/?${qs.toString()}`);
  },

  articleDetail: (id: string) => get<ArticleDetail>(`${API}/articles/${id}`),
  recentArticles: (limit = 10) => get<Article[]>(`${API}/articles/recent?limit=${limit}`),
  monthlyVolume: () => get<MonthlyVolume[]>(`${API}/articles/monthly-volume`),
};
