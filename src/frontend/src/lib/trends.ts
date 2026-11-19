import { Topic, TopicTrends, topicName, weekLabel } from "./api";
import { getTopicColor } from "./utils";

export interface Series {
  key: string;
  color: string;
}

/**
 * The API returns one point list per topic id; Recharts wants one row per week
 * with a column per series. Weeks missing from a topic's list become 0 so the
 * lines stay continuous.
 *
 * Lives here rather than beside the chart so it can be tested without a DOM —
 * Recharts needs a measured container, which jsdom never provides.
 */
export function pivot(trends: TopicTrends, topics: Topic[]) {
  const byId = new Map(topics.map((t) => [t.topic_id, t]));
  const used = new Set<string>();
  const series: Series[] = [];
  const rows = new Map<string, Record<string, string | number>>();

  Object.entries(trends).forEach(([id, points], i) => {
    const topicId = Number(id);
    // Labels are LLM-generated and can repeat; the id keeps each column unique.
    let key = topicName(byId.get(topicId) ?? { topic_id: topicId });
    if (used.has(key)) key = `${key} (#${topicId})`;
    used.add(key);
    series.push({ key, color: getTopicColor(i) });

    points.forEach((p) => {
      const week = weekLabel(p);
      const row = rows.get(week) ?? { week };
      row[key] = p.count;
      rows.set(week, row);
    });
  });

  const data = [...rows.values()]
    .sort((a, b) => String(a.week).localeCompare(String(b.week)))
    .map((row) => {
      const filled = { ...row };
      series.forEach((s) => {
        if (filled[s.key] === undefined) filled[s.key] = 0;
      });
      return filled;
    });

  return { data, series };
}
