import { useTopics } from "@/lib/queries";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { Search, CalendarIcon, X } from "lucide-react";

interface ArticleFiltersProps {
  search: string;
  onSearchChange: (v: string) => void;
  selectedTopic: string;
  onTopicChange: (v: string) => void;
  dateFrom: Date | undefined;
  onDateFromChange: (v: Date | undefined) => void;
  dateTo: Date | undefined;
  onDateToChange: (v: Date | undefined) => void;
}

const ArticleFilters = ({
  search,
  onSearchChange,
  selectedTopic,
  onTopicChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
}: ArticleFiltersProps) => {
  const { data: topics } = useTopics();
  const hasFilters = search || selectedTopic !== "all" || dateFrom || dateTo;

  const clearAll = () => {
    onSearchChange("");
    onTopicChange("all");
    onDateFromChange(undefined);
    onDateToChange(undefined);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 mb-5">
      <div className="relative flex-1 min-w-[180px]">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search headline, author…"
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-8 h-9 bg-secondary border-border text-foreground placeholder:text-muted-foreground font-body text-sm"
        />
      </div>

      <Select value={selectedTopic} onValueChange={onTopicChange}>
        <SelectTrigger className="w-[180px] h-9 bg-secondary border-border text-sm font-body">
          <SelectValue placeholder="All Topics" />
        </SelectTrigger>
        <SelectContent className="bg-card border-border">
          <SelectItem value="all">All Topics</SelectItem>
          {topics?.map((t) => (
            <SelectItem key={t.topic_id} value={String(t.topic_id)}>{t.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className={cn("h-9 px-3 text-sm font-body bg-secondary border-border", !dateFrom && "text-muted-foreground")}>
            <CalendarIcon className="w-3.5 h-3.5 mr-1.5" />
            {dateFrom ? format(dateFrom, "MMM d") : "From"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar mode="single" selected={dateFrom} onSelect={onDateFromChange} initialFocus className={cn("p-3 pointer-events-auto")} />
        </PopoverContent>
      </Popover>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className={cn("h-9 px-3 text-sm font-body bg-secondary border-border", !dateTo && "text-muted-foreground")}>
            <CalendarIcon className="w-3.5 h-3.5 mr-1.5" />
            {dateTo ? format(dateTo, "MMM d") : "To"}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar mode="single" selected={dateTo} onSelect={onDateToChange} initialFocus className={cn("p-3 pointer-events-auto")} />
        </PopoverContent>
      </Popover>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearAll} className="h-9 px-2 text-muted-foreground hover:text-foreground">
          <X className="w-3.5 h-3.5 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
};

export default ArticleFilters;
