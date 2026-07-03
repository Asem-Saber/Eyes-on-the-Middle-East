import { useTopics, useArticleDetail } from "@/lib/queries";
import { Article } from "@/lib/api";
import { format } from "date-fns";
import { ExternalLink, Clock, User, Tag } from "lucide-react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { getTopicColor } from "@/lib/utils";

interface ArticleDrawerProps {
  article: Article | null;
  open: boolean;
  onClose: () => void;
}

const ArticleDrawer = ({ article, open, onClose }: ArticleDrawerProps) => {
  const { data: topics } = useTopics();
  const { data: detail, isLoading } = useArticleDetail(open && article ? article.id : null);

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
                {topic.name}
              </span>
            )}
            <SheetTitle className="text-lg font-display font-bold leading-snug text-foreground">
              {article.headline}
            </SheetTitle>
          </SheetHeader>

          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground font-body">
            <span className="inline-flex items-center gap-1.5">
              <User className="h-3 w-3" />
              {article.author}
            </span>
            <span className="inline-flex items-center gap-1.5 font-mono-data">
              <Clock className="h-3 w-3" />
              {article.date === "No Date" ? "No Date" : format(new Date(article.date), "MMMM d, yyyy")}
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

          {topic && topic.keywords && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-muted-foreground font-body flex items-center gap-1.5">
                <Tag className="h-3 w-3" />
                Related Keywords
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {topic.keywords.map(kw => (
                  <span key={kw} className="text-xs px-2 py-0.5 rounded-md bg-secondary text-secondary-foreground font-mono-data">
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          )}

          <a
            href={article.link}
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
