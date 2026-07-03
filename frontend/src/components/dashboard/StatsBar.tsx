import { Newspaper, Brain, Calendar, Clock } from "lucide-react";
import { useStats } from "@/lib/queries";
import { formatNumber } from "@/lib/utils";

const icons = [Newspaper, Brain, Calendar, Clock];
const labels = ["Articles Scraped", "Topics Discovered", "Coverage Period", "Last Scraped"];

const StatsBar = () => {
  const { data: stats } = useStats();

  if (!stats) return null;

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
