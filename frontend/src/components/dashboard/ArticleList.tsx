import { useState } from "react";
import { format } from "date-fns";
import { ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import PaginationBar from "@/components/shared/PaginationBar";
import { useArticles, useTopics } from "@/lib/queries";
import { Article } from "@/lib/api";
import { getTopicColor } from "@/lib/utils";
import ArticleFilters from "./ArticleFilters";
import ArticleDrawer from "./ArticleDrawer";

const PAGE_SIZE = 8;

const ArticleList = () => {
  const [search, setSearch] = useState("");
  const [selectedTopic, setSelectedTopic] = useState<string>("all");
  const [dateFrom, setDateFrom] = useState<Date | undefined>();
  const [dateTo, setDateTo] = useState<Date | undefined>();
  const [page, setPage] = useState(1);
  const [drawerArticle, setDrawerArticle] = useState<Article | null>(null);

  const { data: topics } = useTopics();
  const { data: paginatedData, isFetching } = useArticles({
    page,
    limit: PAGE_SIZE,
    topic: selectedTopic !== "all" ? Number(selectedTopic) : null,
    search: search || undefined,
    date_from: dateFrom ? format(dateFrom, "yyyy-MM-dd") : undefined,
    date_to: dateTo ? format(dateTo, "yyyy-MM-dd") : undefined,
  });

  const articles = paginatedData?.articles || [];
  const totalPages = paginatedData?.pages || 1;
  const totalCount = paginatedData?.total || 0;

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-display font-semibold text-foreground mb-1">
        Recent Articles
      </h2>
      <p className="text-sm text-muted-foreground mb-5 font-body">
        Latest scraped articles with assigned topics {isFetching && "(Updating...)"}
      </p>

      <ArticleFilters
        search={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        selectedTopic={selectedTopic}
        onTopicChange={(v) => { setSelectedTopic(v); setPage(1); }}
        dateFrom={dateFrom}
        onDateFromChange={(v) => { setDateFrom(v); setPage(1); }}
        dateTo={dateTo}
        onDateToChange={(v) => { setDateTo(v); setPage(1); }}
      />

      {articles.length === 0 ? (
        <p className="text-sm text-muted-foreground py-8 text-center font-body">
          No articles match your filters.
        </p>
      ) : (
        <>
          <div className="divide-y divide-border">
            {articles.map((article) => {
              const topicIdx = topics ? topics.findIndex((t) => t.topic_id === article.topic_id) : -1;
              const topic = topicIdx !== -1 ? topics![topicIdx] : null;
              const tColor = topicIdx !== -1 ? getTopicColor(topicIdx) : "hsl(0,0%,50%)";

              return (
                <div
                  key={article.id}
                  className="py-4 first:pt-0 last:pb-0 group cursor-pointer"
                  onClick={() => setDrawerArticle(article)}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h3 className="text-base font-semibold text-foreground font-body leading-snug group-hover:text-primary transition-colors">
                        {article.headline}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2 font-body">
                        {article.summary}
                      </p>
                      <div className="flex items-center gap-3 mt-2 flex-wrap">
                        {topic && (
                          <span
                            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium"
                            style={{
                              backgroundColor: `${tColor}20`,
                              color: tColor,
                            }}
                          >
                            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: tColor }} />
                            {article.topic_label}
                          </span>
                        )}
                        <span className="text-xs text-muted-foreground font-body">{article.author}</span>
                        <span className="text-xs text-muted-foreground font-body">
                          {article.date === "No Date" ? "No Date" : new Date(article.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                        </span>
                      </div>
                    </div>
                    <ExternalLink className="w-4 h-4 text-muted-foreground shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              );
            })}
          </div>

          <PaginationBar page={page} totalPages={totalPages} pageSize={PAGE_SIZE} totalCount={totalCount} onPageChange={setPage} />
        </>
      )}

      <ArticleDrawer
        article={drawerArticle}
        open={!!drawerArticle}
        onClose={() => setDrawerArticle(null)}
      />
    </div>
  );
};

export default ArticleList;
