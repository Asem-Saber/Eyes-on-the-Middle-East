import { useAuthors } from "@/lib/queries";
import { Skeleton } from "@/components/ui/skeleton";

const TopAuthors = () => {
  const { data: authors, isLoading, isError } = useAuthors(8);

  if (isLoading) {
    return (
      <div className="bg-card border border-border rounded-lg p-6">
        <Skeleton className="h-6 w-32 mb-2" />
        <Skeleton className="h-4 w-44 mb-6" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i}>
              <div className="flex justify-between mb-1">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-2 w-full rounded-full" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError || !authors || authors.length === 0) return null;

  const max = authors[0]?.count || 1;

  return (
    <div className="bg-card border border-border rounded-lg p-6">
      <h2 className="text-xl font-display font-semibold text-foreground mb-1">
        Top Authors
      </h2>
      <p className="text-sm text-muted-foreground mb-6 font-body">
        Most prolific contributors
      </p>
      <div className="space-y-3">
        {authors.map(({ author, count }) => (
          <div key={author}>
            <div className="flex justify-between text-sm font-body mb-1">
              <span className="text-foreground">{author}</span>
              <span className="text-muted-foreground">{count} articles</span>
            </div>
            <div className="h-2 rounded-full bg-secondary overflow-hidden">
              <div
                className="h-full rounded-full bg-accent transition-all"
                style={{ width: `${(count / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopAuthors;
