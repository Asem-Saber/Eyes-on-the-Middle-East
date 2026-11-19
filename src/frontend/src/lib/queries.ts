import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { api } from "./api";

export function useStats() {
  return useQuery({ queryKey: ["stats"], queryFn: api.stats, staleTime: 60_000 });
}

export function useTopics(includeOutliers = true) {
  return useQuery({
    queryKey: ["topics", includeOutliers],
    queryFn: () => api.topics(includeOutliers),
    staleTime: 60_000,
  });
}

export function useTopicDistribution(limit = 20) {
  return useQuery({
    queryKey: ["topicDistribution", limit],
    queryFn: () => api.topicDistribution(limit),
    staleTime: 60_000,
  });
}

export function useTopicTrends(topics = 5) {
  return useQuery({
    queryKey: ["topicTrends", topics],
    queryFn: () => api.topicTrends(topics),
    staleTime: 60_000,
  });
}

export function useTopicDetail(id: number) {
  return useQuery({
    queryKey: ["topicDetail", id],
    queryFn: () => api.topicDetail(id),
    staleTime: 60_000,
  });
}

export function useArticles(params: {
  page?: number;
  limit?: number;
  topic?: number | null;
  search?: string;
  date_from?: string;
  date_to?: string;
}) {
  return useQuery({
    queryKey: ["articles", params],
    queryFn: () => api.articles(params),
    staleTime: 30_000,
    placeholderData: keepPreviousData,
  });
}

export function useArticleDetail(id: string | null) {
  return useQuery({
    queryKey: ["articleDetail", id],
    queryFn: () => api.articleDetail(id!),
    enabled: !!id,
  });
}

export function useMonthlyVolume() {
  return useQuery({
    queryKey: ["monthlyVolume"],
    queryFn: api.monthlyVolume,
    staleTime: 60_000,
  });
}
