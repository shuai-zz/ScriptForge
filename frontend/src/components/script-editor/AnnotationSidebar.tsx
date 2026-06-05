import { useState, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Check, EyeOff, Filter, Lightbulb, MessageSquare, X } from "lucide-react";

interface AnnotationItem {
  id: string;
  annotation_id: string;
  severity: "error" | "warning" | "info" | "suggestion";
  category: string;
  title: string;
  description: string;
  confidence: number;
  status: "pending" | "accepted" | "ignored" | "modified";
  block_id?: string;
  scene_id?: string;
  alternatives?: { alternative_id: string; text: string; pros: string; cons: string }[];
}

interface AnnotationSidebarProps {
  annotations: AnnotationItem[];
  activeBlockId: string | null;
  onHoverAnnotation: (blockId: string | null) => void;
  onClickAnnotation: (blockId: string) => void;
  onAccept: (id: string) => void;
  onIgnore: (id: string) => void;
  onApplyAlternative: (id: string, alternativeId: string) => void;
}

const severityConfig = {
  error: { label: "错误", color: "text-rose-400", bg: "bg-rose-500/10", border: "border-rose-500/30", icon: <X size={14} /> },
  warning: { label: "警告", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/30", icon: <MessageSquare size={14} /> },
  info: { label: "信息", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/30", icon: <MessageSquare size={14} /> },
  suggestion: { label: "建议", color: "text-sage-green", bg: "bg-green-500/10", border: "border-green-500/30", icon: <Lightbulb size={14} /> },
};

const statusConfig = {
  pending: { label: "待处理", dot: "bg-amber-400" },
  accepted: { label: "已接受", dot: "bg-sage-green" },
  ignored: { label: "已忽略", dot: "bg-muted" },
  modified: { label: "已修改", dot: "bg-blue-400" },
};

export default function AnnotationSidebar({
  annotations,
  activeBlockId,
  onHoverAnnotation,
  onClickAnnotation,
  onAccept,
  onIgnore,
  onApplyAlternative,
}: AnnotationSidebarProps) {
  const [filterOpen, setFilterOpen] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [confidenceMin, setConfidenceMin] = useState<number>(0);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return annotations.filter((a) => {
      if (severityFilter && a.severity !== severityFilter) return false;
      if (statusFilter && a.status !== statusFilter) return false;
      if (a.confidence < confidenceMin) return false;
      return true;
    });
  }, [annotations, severityFilter, statusFilter, confidenceMin]);

  const grouped = useMemo(() => {
    const g: Record<string, AnnotationItem[]> = { error: [], warning: [], info: [], suggestion: [] };
    for (const a of filtered) {
      g[a.severity]?.push(a);
    }
    return g;
  }, [filtered]);

  return (
    <div className="flex h-full w-72 flex-col border-l border-border bg-surface">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-3 py-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-muted">
          批注 ({filtered.length})
        </h4>
        <button
          className={cn(
            "rounded p-1 transition-colors",
            filterOpen ? "bg-accent text-foreground" : "text-muted hover:text-foreground"
          )}
          onClick={() => setFilterOpen((v) => !v)}
          title="筛选"
        >
          <Filter size={14} />
        </button>
      </div>

      {/* Filters */}
      {filterOpen && (
        <div className="space-y-2 border-b border-border px-3 py-2">
          <div className="flex flex-wrap gap-1">
            {(["error", "warning", "info", "suggestion"] as const).map((s) => (
              <button
                key={s}
                className={cn(
                  "rounded px-1.5 py-0.5 text-[10px]",
                  severityFilter === s
                    ? severityConfig[s].bg + " " + severityConfig[s].color
                    : "bg-page text-muted hover:bg-accent"
                )}
                onClick={() => setSeverityFilter((v) => (v === s ? null : s))}
              >
                {severityConfig[s].label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-1">
            {(["pending", "accepted", "ignored"] as const).map((s) => (
              <button
                key={s}
                className={cn(
                  "rounded px-1.5 py-0.5 text-[10px]",
                  statusFilter === s
                    ? "bg-accent text-foreground"
                    : "bg-page text-muted hover:bg-accent"
                )}
                onClick={() => setStatusFilter((v) => (v === s ? null : s))}
              >
                {statusConfig[s].label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-muted">置信度 ≥</span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.1}
              value={confidenceMin}
              onChange={(e) => setConfidenceMin(parseFloat(e.target.value))}
              className="h-1 w-20 accent-amber-gold"
            />
            <span className="text-[10px] text-muted">{confidenceMin.toFixed(1)}</span>
          </div>
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto px-2 py-2">
        {filtered.length === 0 && (
          <div className="py-8 text-center text-xs text-muted">无匹配批注</div>
        )}
        {(["error", "warning", "info", "suggestion"] as const).map((sev) => {
          const items = grouped[sev];
          if (items.length === 0) return null;
          return (
            <div key={sev} className="mb-3">
              <div className={cn("mb-1 flex items-center gap-1 text-[10px] font-bold uppercase", severityConfig[sev].color)}>
                {severityConfig[sev].icon}
                {severityConfig[sev].label} ({items.length})
              </div>
              <div className="space-y-1.5">
                {items.map((ann) => {
                  const isActive = activeBlockId === ann.block_id;
                  const isExpanded = expandedId === ann.id;
                  const cfg = severityConfig[ann.severity];
                  return (
                    <div
                      key={ann.id}
                      className={cn(
                        "cursor-pointer rounded-md border p-2 transition-all",
                        cfg.border,
                        isActive && "ring-1 ring-amber-gold/50",
                        ann.status === "ignored" && "opacity-40"
                      )}
                      onMouseEnter={() => ann.block_id && onHoverAnnotation(ann.block_id)}
                      onMouseLeave={() => onHoverAnnotation(null)}
                      onClick={() => {
                        if (ann.block_id) {
                          onClickAnnotation(ann.block_id);
                          setExpandedId((v) => (v === ann.id ? null : ann.id));
                        }
                      }}
                    >
                      <div className="flex items-start justify-between gap-1">
                        <span className="text-xs font-medium text-foreground">{ann.title}</span>
                        <span className={cn("h-1.5 w-1.5 shrink-0 rounded-full mt-1", statusConfig[ann.status].dot)} />
                      </div>
                      <p className="mt-0.5 text-[10px] text-muted line-clamp-2">{ann.description}</p>
                      <div className="mt-1 flex items-center gap-2 text-[10px] text-muted">
                        <span>置信 {Math.round(ann.confidence * 100)}%</span>
                        <span>{ann.category}</span>
                      </div>

                      {/* Actions */}
                      {ann.status === "pending" && (
                        <div className="mt-2 flex gap-1">
                          <button
                            className="flex items-center gap-0.5 rounded bg-sage-green/20 px-1.5 py-0.5 text-[10px] text-sage-green hover:bg-sage-green/30"
                            onClick={(e) => { e.stopPropagation(); onAccept(ann.id); }}
                          >
                            <Check size={10} /> 接受
                          </button>
                          <button
                            className="flex items-center gap-0.5 rounded bg-muted/20 px-1.5 py-0.5 text-[10px] text-muted hover:bg-muted/30"
                            onClick={(e) => { e.stopPropagation(); onIgnore(ann.id); }}
                          >
                            <EyeOff size={10} /> 忽略
                          </button>
                        </div>
                      )}

                      {/* Alternatives */}
                      {isExpanded && ann.alternatives && ann.alternatives.length > 0 && (
                        <div className="mt-2 space-y-1 border-t border-border pt-1">
                          <div className="text-[10px] text-muted">替代方案:</div>
                          {ann.alternatives.map((alt) => (
                            <button
                              key={alt.alternative_id}
                              className="block w-full rounded bg-accent/50 p-1.5 text-left text-[10px] text-foreground hover:bg-accent"
                              onClick={(e) => {
                                e.stopPropagation();
                                onApplyAlternative(ann.id, alt.alternative_id);
                              }}
                            >
                              <div className="font-medium">{alt.text}</div>
                              <div className="mt-0.5 text-muted">✓ {alt.pros}</div>
                              <div className="text-muted">✗ {alt.cons}</div>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
