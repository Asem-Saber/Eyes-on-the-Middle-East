import { Newspaper, Brain, Calendar, Clock } from "lucide-react";
import { useStats } from "@/lib/queries";
import { formatNumber } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const icons = [Newspaper, Brain, Calendar, Clock];
const labels = ["Articles Scraped", "Topics Discovered", "Coverage Period", "Last Scraped"];

const StatsBar = () => {
  const { data: stats, isLoading, isError } = useStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="bg-card border border-border rounded-lg p-5 flex items-center gap-4">
            <Skeleton className="w-10 h-10 rounded-md" />
            <div className="space-y-2">
              <Skeleton className="h-3 w-20" />
              <Skeleton className="h-5 w-16" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-5 text-center">
        <p className="text-sm text-destructive font-body">Failed to load stats.</p>
      </div>
    );
  }

  const values = [
    formatNumber(stats.articles_scraped),
    formatNumber(stats.topics_discovered),
    stats.coverage_period,
    new Date(stats.last_scraped).toLocaleDateString(),
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {labels.map((label, i) => {
        const Icon = icons[i];
        return (
          <div key={label} className="bg-card border border-border rounded-lg p-5 flex items-center gap-4">
            <div className="p-2.5 rounded-md bg-secondary">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground font-body">{label}</p>
              <p className="text-lg font-semibold text-foreground font-body">{values[i]}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default StatsBar;
