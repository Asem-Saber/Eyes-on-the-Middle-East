import StatsBar from "@/components/dashboard/StatsBar";
import DiscoveredTopics from "@/components/dashboard/DiscoveredTopics";
import TopicDistribution from "@/components/dashboard/TopicDistribution";
import TopicTimeline from "@/components/dashboard/TopicTimeline";
import TopicKeywords from "@/components/dashboard/TopicKeywords";
import ArticleList from "@/components/dashboard/ArticleList";
import MonthlyVolume from "@/components/dashboard/MonthlyVolume";
import TopAuthors from "@/components/dashboard/TopAuthors";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-6">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-display font-bold text-foreground tracking-tight">
            Eyes on the <span className="text-primary">Middle East</span>
          </h1>
          <p className="text-sm sm:text-base text-muted-foreground font-body mt-1">
            Al Jazeera political article trends & topic modeling — powered by BERTopic
          </p>
        </div>
      </header>

      {/* Dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 space-y-6">
        <StatsBar />

        {/* Topics + Distribution + Keywords */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <DiscoveredTopics />
          <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
            <TopicDistribution />
            <TopicKeywords />
          </div>
        </div>

        {/* Timeline */}
        <TopicTimeline />

        {/* Volume + Authors */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <MonthlyVolume />
          <TopAuthors />
        </div>

        {/* Articles */}
        <ArticleList />
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-8 sm:mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-xs text-muted-foreground font-body text-center">
            Data scraped from Al Jazeera Politics — Topic modeling via BERTopic + Sentence-BERT.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
