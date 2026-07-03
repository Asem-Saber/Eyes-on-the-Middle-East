import { useNavigate } from "react-router-dom";
import { Hash } from "lucide-react";
import { useTopics } from "@/lib/queries";
import { getTopicColor } from "@/lib/utils";

const TopicKeywords = () => {
  const navigate = useNavigate();
  const { data: topics } = useTopics();

  if (!topics) return null;

  const allKeywords = topics.flatMap((t, tIdx) =>
    t.keywords.map((kw, i) => ({
      word: kw,
      weight: t.count * (1 - i * 0.15),
      color: getTopicColor(tIdx),
      topicId: t.topic_id,
    }))
  );

  const uniqueKeywords = Object.values(
    allKeywords.reduce<Record<string, (typeof allKeywords)[0]>>((acc, kw) => {
      if (!acc[kw.word] || acc[kw.word].weight < kw.weight) {
        acc[kw.word] = kw;
      }
      return acc;
    }, {})
  ).sort((a, b) => b.weight - a.weight);

  const maxWeight = uniqueKeywords[0]?.weight || 1;
  const minWeight = uniqueKeywords[uniqueKeywords.length - 1]?.weight || 0;

  function scale(weight: number, minOut: number, maxOut: number) {
    const norm = (weight - minWeight) / (maxWeight - minWeight || 1);
    return minOut + norm * (maxOut - minOut);
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6 h-full">
      <div className="flex items-center gap-2 mb-1">
        <Hash className="w-5 h-5 text-primary" />
        <h2 className="text-xl font-display font-semibold text-foreground">
          Top Keywords
        </h2>
      </div>
      <p className="text-sm text-muted-foreground mb-5 font-body">
        Weighted terms from BERTopic c-TF-IDF
      </p>

      <div className="flex flex-wrap gap-x-4 gap-y-3 items-baseline justify-center text-center mt-6">
        {uniqueKeywords.slice(0, 50).map(({ word, weight, color, topicId }) => (
          <button
            key={word}
            onClick={() => navigate(`/topic/${topicId}`)}
            className="font-display font-bold hover:underline decoration-1 underline-offset-4 transition-all hover:scale-105"
            style={{
              fontSize: `${scale(weight, 0.8, 2.75)}rem`,
              opacity: scale(weight, 0.5, 1),
              color,
            }}
          >
            {word}
          </button>
        ))}
      </div>
    </div>
  );
};

export default TopicKeywords;
