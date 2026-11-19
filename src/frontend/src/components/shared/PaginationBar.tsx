import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface PaginationBarProps {
  page: number;
  totalPages: number;
  pageSize: number;
  totalCount: number;
  onPageChange: (page: number) => void;
}

const PaginationBar = ({ page, totalPages, pageSize, totalCount, onPageChange }: PaginationBarProps) => {
  if (totalPages <= 1) return null;

  return (
    <div className="flex items-center justify-between mt-5 pt-4 border-t border-border">
      <p className="text-xs text-muted-foreground font-body">
        {(page - 1) * pageSize + 1}–{Math.min(page * pageSize, totalCount)} of {totalCount}
      </p>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page === 1} onClick={() => onPageChange(page - 1)}>
          <ChevronLeft className="w-4 h-4" />
        </Button>
        {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => i + 1).map((p) => (
          <Button key={p} variant={p === page ? "default" : "ghost"} size="sm" className="h-8 w-8 p-0 text-xs" onClick={() => onPageChange(p)}>
            {p}
          </Button>
        ))}
        {totalPages > 7 && <span className="text-xs text-muted-foreground px-1">…</span>}
        <Button variant="ghost" size="sm" className="h-8 w-8 p-0" disabled={page === totalPages} onClick={() => onPageChange(page + 1)}>
          <ChevronRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
};

export default PaginationBar;
