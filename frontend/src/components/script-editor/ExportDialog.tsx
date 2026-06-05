import { useState } from "react";
import { cn } from "@/lib/utils";
import { Download, FileText, FileCode, FileType, FileArchive, X, Check, Loader2 } from "lucide-react";

const API_BASE = "http://localhost:8000/api";

interface ExportFormat {
  key: string;
  label: string;
  description: string;
  ext: string;
  icon: React.ReactNode;
}

const FORMATS: ExportFormat[] = [
  {
    key: "yaml",
    label: "YAML",
    description: "ScriptForge 原生格式，包含完整元数据",
    ext: ".yaml",
    icon: <FileCode size={18} />,
  },
  {
    key: "fountain",
    label: "Fountain",
    description: "纯文本编剧格式，兼容大多数编辑器",
    ext: ".fountain",
    icon: <FileText size={18} />,
  },
  {
    key: "pdf",
    label: "PDF",
    description: "标准剧本格式，可直接打印或分享",
    ext: ".pdf",
    icon: <FileType size={18} />,
  },
  {
    key: "fdx",
    label: "Final Draft (.fdx)",
    description: "Final Draft XML 格式",
    ext: ".fdx",
    icon: <FileText size={18} />,
  },
];

interface ExportDialogProps {
  open: boolean;
  projectId: string;
  onClose: () => void;
}

export default function ExportDialog({ open, projectId, onClose }: ExportDialogProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [exporting, setExporting] = useState(false);
  const [done, setDone] = useState(false);

  const toggle = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleExport = async () => {
    if (selected.size === 0) return;
    setExporting(true);

    try {
      if (selected.size === 1) {
        const format = Array.from(selected)[0];
        const res = await fetch(`${API_BASE}/projects/${projectId}/export/${format}`);
        if (!res.ok) throw new Error("Export failed");
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const disposition = res.headers.get("content-disposition");
        const match = disposition?.match(/filename="(.+)"/);
        a.download = match ? match[1] : `script.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      } else {
        const res = await fetch(`${API_BASE}/projects/${projectId}/export/batch`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ formats: Array.from(selected) }),
        });
        if (!res.ok) throw new Error("Batch export failed");
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const disposition = res.headers.get("content-disposition");
        const match = disposition?.match(/filename="(.+)"/);
        a.download = match ? match[1] : "script.zip";
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
      setDone(true);
      setTimeout(() => {
        setDone(false);
        onClose();
      }, 1200);
    } catch (e) {
      console.error(e);
    } finally {
      setExporting(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-sm font-bold text-foreground">导出剧本</h2>
          <button className="rounded p-1 text-muted hover:bg-accent hover:text-foreground" onClick={onClose}>
            <X size={16} />
          </button>
        </div>

        <div className="px-4 py-3">
          <p className="mb-3 text-xs text-muted">选择要导出的格式（可多选）:</p>
          <div className="space-y-2">
            {FORMATS.map((f) => {
              const isSelected = selected.has(f.key);
              return (
                <button
                  key={f.key}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg border px-3 py-2.5 text-left transition-all",
                    isSelected
                      ? "border-amber-gold bg-amber-gold/10"
                      : "border-border bg-surface hover:border-amber-gold/50"
                  )}
                  onClick={() => toggle(f.key)}
                >
                  <span className={cn("text-muted", isSelected && "text-amber-gold")}>{f.icon}</span>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-foreground">{f.label}</div>
                    <div className="text-[10px] text-muted">{f.description}</div>
                  </div>
                  <div
                    className={cn(
                      "flex h-5 w-5 items-center justify-center rounded border",
                      isSelected ? "border-amber-gold bg-amber-gold text-black" : "border-muted"
                    )}
                  >
                    {isSelected && <Check size={12} strokeWidth={3} />}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
          <button
            className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:bg-accent hover:text-foreground"
            onClick={onClose}
          >
            取消
          </button>
          <button
            className={cn(
              "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium",
              selected.size === 0 || exporting
                ? "cursor-not-allowed bg-muted/30 text-muted"
                : done
                ? "bg-green-600 text-white"
                : "bg-amber-gold text-black hover:bg-amber-gold/90"
            )}
            disabled={selected.size === 0 || exporting}
            onClick={handleExport}
          >
            {exporting ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                导出中...
              </>
            ) : done ? (
              <>
                <Check size={14} />
                已完成
              </>
            ) : (
              <>
                <Download size={14} />
                导出{selected.size > 1 ? ` (${selected.size} 格式)` : ""}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
