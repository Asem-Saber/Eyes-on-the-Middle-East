import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useTopicTrends, useTopics } from "@/lib/queries";
import { getTopicColor } from "@/lib/utils";

const TopicTimeline = () => {
  const { data: topicTrends } = useTopicTrends();
  const { data: topics } = useTopics();

  if (!topicTrends || !topics) return null;

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
            <Tooltip
              contentStyle={{
                background: "hsl(240,8%,8%)",
                border: "1px solid hsl(240,10%,16%)",
                borderRadius: "8px",
                fontSize: "13px",
                fontFamily: "var(--font-body)",
              }}
              labelStyle={{ color: "hsl(40,20%,92%)" }}
            />
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
