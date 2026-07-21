import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ExternalLink, TrendingUp, Users, Calendar as CalendarIcon } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import { useTopicDetail, useArticles } from "@/lib/queries";
import { Article } from "@/lib/api";
import { getTopicColor, formatNumber, CHART_TOOLTIP_STYLE } from "@/lib/utils";
import ArticleDrawer from "@/components/dashboard/ArticleDrawer";
import PaginationBar from "@/components/shared/PaginationBar";

const TopicDetail = () => {
  const { id } = useParams();
  const topicId = Number(id);
  
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 8;
  const { data: topic } = useTopicDetail(topicId);
  const { data: articlesData } = useArticles({ topic: topicId, page, limit: PAGE_SIZE });
  const [drawerArticle, setDrawerArticle] = useState<Article | null>(null);

  if (!topic) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-display font-bold text-foreground mb-2">Loading or Topic not found</h1>
          <Link to="/" className="text-primary hover:underline font-body text-sm">← Back to dashboard</Link>
        </div>
      </div>
    );
  }

  const topicArticles = articlesData?.articles || [];
  const totalPages = articlesData?.pages || 1;
  const totalCount = articlesData?.total || 0;
  const color = getTopicColor(0); // Primary color for this topic page

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors font-body mb-4">
            <ArrowLeft className="w-4 h-4" /> Back to dashboard
          </Link>
          <div className="flex items-center gap-3 mt-2">
            <span className="w-4 h-4 rounded-full shrink-0" style={{ backgroundColor: color }} />
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-foreground">{topic.name}</h1>
          </div>
          <div className="flex flex-wrap gap-1.5 mt-3">
            {topic.keywords?.map((kw) => (
              <span key={kw} className="px-2.5 py-1 text-xs rounded-md bg-secondary text-secondary-foreground font-mono-data">{kw}</span>
            ))}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { icon: TrendingUp, label: "Articles", value: formatNumber(topic.stats.article_count) },
            { icon: Users, label: "Contributors", value: formatNumber(topic.stats.contributors_count) },
            { icon: CalendarIcon, label: "Date Range", value: topic.stats.date_range },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="bg-card border border-border rounded-lg p-4 flex items-center gap-3">
              <div className="p-2 rounded-md bg-secondary">
                <Icon className="w-4 h-4 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground font-body">{label}</p>
                <p className="text-sm font-semibold text-foreground font-body">{value}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trend over time */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-lg font-display font-semibold text-foreground mb-1">Topic Trend</h2>
            <p className="text-sm text-muted-foreground mb-4 font-body">Weekly article frequency</p>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={topic.trend} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                  <XAxis dataKey="week" stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip {...CHART_TOOLTIP_STYLE} />
                  <Line type="monotone" dataKey="count" stroke={color} strokeWidth={2.5} dot={{ r: 3, fill: color }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top authors for this topic */}
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-lg font-display font-semibold text-foreground mb-1">Top Contributors</h2>
            <p className="text-sm text-muted-foreground mb-4 font-body">Most active authors on this topic</p>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topic.contributors} layout="vertical" margin={{ left: 0, right: 16, top: 0, bottom: 0 }}>
                  <XAxis type="number" stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis type="category" dataKey="author" width={80} stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip
                    {...CHART_TOOLTIP_STYLE}
                    formatter={(value: number, _: string, props: any) => [`${value} articles`, props.payload.author]}
                  />
                  <Bar dataKey="count" fill={color} radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Monthly volume */}
        {topic.monthly_volume?.length > 1 && (
          <div className="bg-card border border-border rounded-lg p-6">
            <h2 className="text-lg font-display font-semibold text-foreground mb-1">Monthly Volume</h2>
            <p className="text-sm text-muted-foreground mb-4 font-body">Articles per month for this topic</p>
            <div className="h-[180px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topic.monthly_volume} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                  <XAxis dataKey="month" stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <YAxis stroke="hsl(240,5%,55%)" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip {...CHART_TOOLTIP_STYLE} />
                  <Bar dataKey="count" fill={color} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Keywords word cloud style */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-display font-semibold text-foreground mb-1">Top Keywords</h2>
          <p className="text-sm text-muted-foreground mb-4 font-body">c-TF-IDF weighted terms for this cluster</p>
          <div className="flex flex-wrap gap-2">
            {topic.keywords?.map((kw, i) => {
              const sizes = ["text-2xl", "text-xl", "text-lg", "text-base", "text-sm"];
              const opacities = ["opacity-100", "opacity-90", "opacity-80", "opacity-70", "opacity-60"];
              return (
                <span
                  key={kw}
                  className={`font-display font-bold ${sizes[i] || "text-sm"} ${opacities[i] || "opacity-50"} transition-colors`}
                  style={{ color }}
                >
                  {kw}
                </span>
              );
            })}
          </div>
        </div>

        {/* Articles */}
        <div className="bg-card border border-border rounded-lg p-6">
          <h2 className="text-lg font-display font-semibold text-foreground mb-1">Recent Articles</h2>
          <p className="text-sm text-muted-foreground mb-4 font-body">{topicArticles.length} recent articles in this cluster</p>
          {topicArticles.length === 0 ? (
            <p className="text-muted-foreground font-body text-center py-12">No articles found.</p>
          ) : (
            <div className="divide-y divide-border">
              {topicArticles.map((article) => (
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
                      <p className="text-sm text-muted-foreground mt-1 font-body line-clamp-2">{article.summary}</p>
                      <div className="flex items-center gap-3 mt-1.5">
                        <span className="text-xs text-muted-foreground font-body">{article.author}</span>
                        <span className="text-xs text-muted-foreground font-body">
                          {article.date === "No Date" ? "No Date" : new Date(article.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                        </span>
                      </div>
                    </div>
                    <ExternalLink className="w-4 h-4 text-muted-foreground shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </div>
                </div>
              ))}
            </div>
          )}
          <PaginationBar page={page} totalPages={totalPages} pageSize={PAGE_SIZE} totalCount={totalCount} onPageChange={setPage} />
        </div>
      </main>

      <ArticleDrawer
        article={drawerArticle}
        open={!!drawerArticle}
        onClose={() => setDrawerArticle(null)}
      />
    </div>
  );
};

export default TopicDetail;
