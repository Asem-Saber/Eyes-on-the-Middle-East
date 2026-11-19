import { useTopics, useArticleDetail } from "@/lib/queries";
import { Article, topicName } from "@/lib/api";
import { ExternalLink, Clock, Newspaper, Tag } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { getTopicColor, formatArticleDate } from "@/lib/utils";

interface ArticleDrawerProps {
  article: Article | null;
  open: boolean;
  onClose: () => void;
}

const ArticleDrawer = ({ article, open, onClose }: ArticleDrawerProps) => {
  const { data: topics } = useTopics();
  const { data: detail, isLoading } = useArticleDetail(open && article ? article.article_id : null);

  if (!article) return null;

  const topicIdx = topics ? topics.findIndex(t => t.topic_id === article.topic_id) : -1;
  const topic = topicIdx !== -1 ? topics![topicIdx] : null;
  const tColor = topicIdx !== -1 ? getTopicColor(topicIdx) : "hsl(0,0%,50%)";

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent className="w-full sm:max-w-lg overflow-y-auto p-0 bg-card border-border">
        <div className="p-6 space-y-5">
          <SheetHeader className="text-left space-y-3 p-0">
            {topic && (
              <span
                className="inline-flex self-start items-center gap-1.5 text-xs px-2.5 py-1 rounded-md font-medium"
                style={{ backgroundColor: `${tColor}20`, color: tColor }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: tColor }} />
                {topicName(topic)}
              </span>
            )}
            <SheetTitle className="text-lg font-display font-bold leading-snug text-foreground">
              {article.headline}
            </SheetTitle>
          </SheetHeader>

          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground font-body">
            {article.source_name && (
              <span className="inline-flex items-center gap-1.5">
                <Newspaper className="h-3 w-3" />
                {article.source_name}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 font-mono-data">
              <Clock className="h-3 w-3" />
              {formatArticleDate(article.published_date, { month: "long", day: "numeric", year: "numeric" })}
            </span>
          </div>

          <hr className="border-border" />

          <div className="text-sm leading-relaxed text-secondary-foreground space-y-4 font-body">
            <p className="font-semibold text-foreground">{article.summary}</p>
            {isLoading ? (
              <p className="text-muted-foreground animate-pulse">Loading content...</p>
            ) : detail?.full_content ? (
              detail.full_content.map((p, i) => (
                <p key={i}>{p}</p>
              ))
            ) : (
              <p className="text-muted-foreground italic">Full content not available.</p>
            )}
          </div>

          {topic?.topic_summary && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-muted-foreground font-body flex items-center gap-1.5">
                <Tag className="h-3 w-3" />
                About this topic
              </h4>
              <p className="text-xs leading-relaxed text-secondary-foreground font-body">
                {topic.topic_summary}
              </p>
            </div>
          )}

          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline transition-colors font-body"
          >
            Read on Al Jazeera
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default ArticleDrawer;
