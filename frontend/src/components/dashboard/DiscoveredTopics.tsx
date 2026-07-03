import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart3, ChevronRight } from "lucide-react";
import { useTopics } from "@/lib/queries";
import { getTopicColor, formatNumber } from "@/lib/utils";

const DiscoveredTopics = () => {
  const navigate = useNavigate();
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const { data: topics } = useTopics();

  if (!topics) return null;

  const topicData = topics.slice(0, 15);

  return (
    <div className="bg-card border border-border rounded-lg p-6 h-full">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary" />
          <h2 className="text-xl font-display font-semibold text-foreground">
            Discovered Topics
          </h2>
        </div>
        <span className="text-xs text-muted-foreground font-body">Click to filter</span>
      </div>
      <p className="text-sm text-muted-foreground mb-4 font-body">
        Showing top 15 of {topics.length} clusters identified via BERTopic
      </p>
      <div className="space-y-1">
        {topicData.map((topic, index) => (
          <div key={topic.topic_id} className="relative">
            <button
              onClick={() => navigate(`/topic/${topic.topic_id}`)}
              onMouseEnter={() => setHoveredId(topic.topic_id)}
              onMouseLeave={() => setHoveredId(null)}
              className="w-full flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-secondary/60 transition-colors group text-left"
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: getTopicColor(index) }}
              />
              <span className="flex-1 text-sm font-body text-foreground group-hover:text-primary transition-colors truncate">
                {topic.name}
              </span>
              <span className="text-xs font-semibold text-primary font-body tabular-nums">
                {formatNumber(topic.count)}
              </span>
              <ChevronRight className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
            </button>
            {hoveredId === topic.topic_id && topic.keywords && (
              <div className="absolute left-full top-0 ml-2 z-50 bg-popover border border-border rounded-lg p-3 shadow-xl w-56 pointer-events-none">
                <p className="text-xs font-semibold text-foreground font-body mb-2">{topic.name}</p>
                <div className="flex flex-wrap gap-1">
                  {topic.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-muted-foreground font-mono-data"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default DiscoveredTopics;
