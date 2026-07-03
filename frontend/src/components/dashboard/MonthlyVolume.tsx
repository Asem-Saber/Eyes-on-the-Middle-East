import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useMonthlyVolume } from "@/lib/queries";

const MonthlyVolume = () => {
  const { data: volumeData } = useMonthlyVolume();

  if (!volumeData) return null;

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
            <Tooltip
              contentStyle={{
                background: "hsl(240,8%,8%)",
                border: "1px solid hsl(240,10%,16%)",
                borderRadius: "8px",
                fontSize: "13px",
                fontFamily: "var(--font-body)",
              }}
              labelStyle={{ color: "hsl(40,20%,92%)" }}
            />
            <Bar dataKey="count" fill="hsl(38,92%,55%)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MonthlyVolume;
