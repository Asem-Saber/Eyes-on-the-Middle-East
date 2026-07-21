import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useMonthlyVolume } from "@/lib/queries";
import { CHART_TOOLTIP_STYLE } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

const MonthlyVolume = () => {
  const { data: volumeData, isLoading, isError } = useMonthlyVolume();

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-48 mb-2" />
        <Skeleton className="h-4 w-56 mb-6" />
        <Skeleton className="h-[260px] w-full rounded" />
      </div>
    );
  }

  if (isError || !volumeData) {
    return (
      <div className="bg-card border border-destructive/50 rounded-lg p-6 text-center">
        <p className="text-sm text-destructive font-body">Failed to load monthly volume.</p>
      </div>
    );
  }

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-display font-semibold text-foreground mb-1">
        Monthly Article Volume
      </h2>
      <p className="text-sm text-muted-foreground mb-6 font-body">
        Total articles scraped per month
      </p>
      <div className="h-[260px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={volumeData} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
            <XAxis dataKey="month" stroke="hsl(240,5%,55%)" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="hsl(240,5%,55%)" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip {...CHART_TOOLTIP_STYLE} />
            <Bar dataKey="count" fill="hsl(38,92%,55%)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MonthlyVolume;
