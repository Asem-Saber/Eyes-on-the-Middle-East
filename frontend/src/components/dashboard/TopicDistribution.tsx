import { useNavigate } from "react-router-dom";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { useTopicDistribution, useTopics } from "@/lib/queries";
import { getTopicColor, CHART_TOOLTIP_STYLE } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const TopicDistribution = () => {
  const navigate = useNavigate();
  const { data: distData, isLoading: distLoading, isError: distError } = useTopicDistribution();
  const { data: topics, isLoading: topicsLoading, isError: topicsError } = useTopics();

  if (distLoading || topicsLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full flex flex-col">
        <Skeleton className="h-6 w-44 mb-2" />
        <Skeleton className="h-4 w-56 mb-4" />
        <div className="flex-1 flex items-center justify-center">
          <Skeleton className="h-[220px] w-[220px] rounded-full" />
        </div>
      </div>
    );
  }

  if (distError || topicsError || !distData || !topics) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6 h-full text-center">
        <p className="text-sm text-destructive font-body">Failed to load topic distribution.</p>
      </div>
    );
  }

  const data = distData.slice(0, 10).map((d, index) => {
    const topicIdx = topics.findIndex((t) => t.name === d.topic);
    const topic = topics[topicIdx];
    return {
      name: d.topic,
      value: d.count,
      color: topicIdx !== -1 ? getTopicColor(topicIdx) : getTopicColor(index),
      id: topic?.topic_id,
    };
  });

  return (
    <div className="bg-card border border-border rounded-lg p-6 h-full flex flex-col">
      <h2 className="text-xl font-display font-semibold text-foreground mb-1">
        Topic Distribution
      </h2>
      <p className="text-sm text-muted-foreground mb-4 font-body">
        Articles per topic — click a slice to explore
      </p>
      <div className="flex-1 flex flex-col xl:flex-row items-center gap-6 min-h-0">
        <div className="h-[220px] w-[220px] shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={105}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
                cursor="pointer"
                onClick={(entry) => {
                  const targetId = entry.id || (entry.payload && entry.payload.id);
                  if (targetId !== undefined) navigate(`/topic/${targetId}`);
                }}
              >
                {data.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                {...CHART_TOOLTIP_STYLE}
                formatter={(value: number, name: string) => [`${value} articles`, name]}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex-1 grid grid-cols-1 xs:grid-cols-2 xl:grid-cols-1 gap-x-4 gap-y-2 min-w-0 self-center">
          {data.map((entry) => (
            <button
              key={entry.name}
              onClick={() => {
                if (entry.id) navigate(`/topic/${entry.id}`);
              }}
              className="flex items-center gap-2 text-left hover:opacity-80 transition-opacity py-0.5 group"
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: entry.color }}
              />
              <span className="text-xs text-muted-foreground font-body truncate group-hover:text-foreground transition-colors">
                {entry.name}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TopicDistribution;
