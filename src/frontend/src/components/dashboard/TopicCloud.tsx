// Replaces v1's TopicKeywords. dim_topic stores the LLM label and summary, not
// the c-TF-IDF terms, so the cloud is sized by article volume per topic rather
// than by keyword weight.
import { useNavigate } from "react-router-dom";
import { Hash } from "lucide-react";
import { useTopics } from "@/lib/queries";
import { topicName } from "@/lib/api";
import { getTopicColor } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const TopicCloud = () => {
  const navigate = useNavigate();
  const { data: topics, isLoading, isError } = useTopics(false);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6 h-full">
        <Skeleton className="h-6 w-36 mb-2" />
        <Skeleton className="h-4 w-56 mb-5" />
        <div className="flex flex-wrap gap-3 justify-center mt-6">
          {Array.from({ length: 15 }).map((_, i) => (
            <Skeleton key={i} className="h-8 rounded" style={{ width: `${60 + Math.random() * 80}px` }} />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !topics) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6 h-full text-center">
        <p className="text-sm text-destructive font-body">Failed to load topics.</p>
      </div>
    );
  }

  const ranked = [...topics].sort((a, b) => b.article_count - a.article_count);
  const maxCount = ranked[0]?.article_count ?? 1;
  const minCount = ranked[ranked.length - 1]?.article_count ?? 0;

  function scale(count: number, minOut: number, maxOut: number) {
    const norm = (count - minCount) / (maxCount - minCount || 1);
    return minOut + norm * (maxOut - minOut);
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 h-full">
      <div className="flex items-center gap-2 mb-1">
        <Hash className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-display font-semibold text-foreground">
          Topic Cloud
        </h2>
      </div>
      <p className="text-sm text-muted-foreground mb-5 font-body">
        BERTopic clusters sized by article volume
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-3 items-baseline justify-center text-center mt-6">
        {ranked.slice(0, 50).map((topic, i) => (
          <button
            key={topic.topic_key}
            onClick={() => navigate(`/topic/${topic.topic_id}`)}
            title={topic.topic_summary ?? undefined}
            className="font-display font-bold hover:underline decoration-1 underline-offset-4 transition-all hover:scale-105"
            style={{
              fontSize: `${scale(topic.article_count, 0.8, 2.75)}rem`,
              opacity: scale(topic.article_count, 0.5, 1),
              color: getTopicColor(i),
            }}
          >
            {topicName(topic)}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TopicCloud;
