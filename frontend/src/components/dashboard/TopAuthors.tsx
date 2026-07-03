import { useAuthors } from "@/lib/queries";

const TopAuthors = () => {
  const { data: authors } = useAuthors(8);

  if (!authors || authors.length === 0) return null;

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
