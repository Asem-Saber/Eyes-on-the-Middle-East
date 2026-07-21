import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useTopicTrends, useTopics } from "@/lib/queries";
import { getTopicColor, CHART_TOOLTIP_STYLE } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const TopicTimeline = () => {
  const { data: topicTrends, isLoading: trendsLoading, isError: trendsError } = useTopicTrends();
  const { data: topics, isLoading: topicsLoading, isError: topicsError } = useTopics();

  if (trendsLoading || topicsLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-40 mb-2" />
        <Skeleton className="h-4 w-64 mb-6" />
        <Skeleton className="h-[340px] w-full rounded" />
      </div>
    );
  }

  if (trendsError || topicsError || !topicTrends || !topics) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6 text-center">
        <p className="text-sm text-destructive font-body">Failed to load topic trends.</p>
      </div>
    );
  }

  const topicKeys = Object.keys(topicTrends[0] || {}).filter((k) => k !== "week").slice(0, 5);

  const colorMap: Record<string, string> = {};
  topics.forEach((t, i) => {
    colorMap[t.name] = getTopicColor(i);
  });

  const defaultColors = [
    "hsl(38,92%,55%)", "hsl(14,80%,55%)", "hsl(180,60%,45%)",
    "hsl(260,50%,55%)", "hsl(330,60%,55%)",
  ];

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-display font-semibold text-foreground mb-1">
        Topics Over Time
      </h2>
      <p className="text-sm text-muted-foreground mb-6 font-body">
        Weekly article count by top 5 topics
      </p>
      <div className="h-[340px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={topicTrends} margin={{ left: 0, right: 16, top: 8, bottom: 0 }}>
            <XAxis dataKey="week" stroke="hsl(240,5%,55%)" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="hsl(240,5%,55%)" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip {...CHART_TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: "12px", fontFamily: "var(--font-body)" }} />
            {topicKeys.map((key, i) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={colorMap[key] || defaultColors[i % defaultColors.length]}
                strokeWidth={2.5}
                dot={{ r: 3, fill: colorMap[key] || defaultColors[i % defaultColors.length] }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TopicTimeline;
