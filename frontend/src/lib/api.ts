const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const API = `${BASE}/api/v1`;

export interface Topic {
  topic_id: number;
  name: string;
  keywords: string[];
  count: number;
}

export interface Article {
  id: string;
  headline: string;
  summary: string;
  topic_label: string;
  topic_id: number | null;
  author: string;
  date: string;
  link: string;
}

export interface ArticleDetail extends Article {
  full_content: string[] | null;
  topics: string[] | null;
  sources: string[] | null;
}

export interface PaginatedArticles {
  articles: Article[];
  total: number;
  page: number;
  pages: number;
}

export interface Stats {
  articles_scraped: number;
  topics_discovered: number;
  coverage_period: string;
  last_scraped: string;
}

export interface TopicDistribution {
  topic: string;
  count: number;
}

export interface TopicTrend {
  week: string;
  [topicName: string]: string | number;
}

export interface AuthorCount {
  author: string;
  count: number;
}

export interface MonthlyVolume {
  month: string;
  count: number;
}

export interface TopicContributor {
  author: string;
  count: number;
}

export interface TopicDetail {
  topic_id: number;
  name: string;
  keywords: string[];
  stats: {
    article_count: number;
    contributors_count: number;
    date_range: string;
  };
  contributors: TopicContributor[];
  trend: { week: string; count: number }[];
  monthly_volume: MonthlyVolume[];
}

// ── Fetch helpers ───────────────────────────────────────────

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export const api = {
  stats: () => get<Stats>(`${API}/stats`),

  topics: () => get<Topic[]>(`${API}/topics`),
  topicDistribution: () => get<TopicDistribution[]>(`${API}/topics/distribution`),
  topicTrends: () => get<TopicTrend[]>(`${API}/topics/trends`),
  topicDetail: (id: number) => get<TopicDetail>(`${API}/topics/${id}`),

  authors: (limit = 8) => get<AuthorCount[]>(`${API}/authors/top?limit=${limit}`),

  articles: (params: {
    page?: number;
    limit?: number;
    topic?: number | null;
    search?: string;
    date_from?: string;
    date_to?: string;
  } = {}) => {
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
