import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ToastContext";
import { Skeleton } from "@/components/Skeleton";
import {
  GitCommit,
  Tag,
  ArrowLeftRight,
  RotateCcw,
  Save,
  Clock,
  User,
  AlertTriangle,
  RefreshCw,
} from "lucide-react";

interface VersionEntry {
  version_id: string;
  short_id: string;
  message: string;
  committed_at: string;
  author: string;
  tags: string[];
}

interface DiffResult {
  diff: string;
  added_lines: number;
  removed_lines: number;
}

export default function VersionHistory() {
  const { projectId } = useParams<{ projectId: string }>();

  const [versions, setVersions] = useState<VersionEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [compareVersion, setCompareVersion] = useState<string | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [diffLoading, setDiffLoading] = useState(false);

  const [checkpointOpen, setCheckpointOpen] = useState(false);
  const [checkpointMessage, setCheckpointMessage] = useState("");
  const [checkpointTag, setCheckpointTag] = useState("");
  const [checkpointLoading, setCheckpointLoading] = useState(false);
  const [checkpointError, setCheckpointError] = useState<string | null>(null);

  const [restoreOpen, setRestoreOpen] = useState(false);
  const [restoreVersionId, setRestoreVersionId] = useState<string | null>(null);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);

  const apiBase = `/api/projects/${projectId}/versions`;

  const fetchVersions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(apiBase);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "加载失败" }));
        throw new Error(err.detail || "加载失败");
      }
      const data: VersionEntry[] = await res.json();
      setVersions(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "加载失败";
      setError(msg);
      toast("error", msg);
    } finally {
      setLoading(false);
    }
  }, [apiBase, toast]);

  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  const handleDiff = useCallback(
    async (a: string, b: string) => {
      setDiffLoading(true);
      setDiffResult(null);
      try {
        const res = await fetch(`${apiBase}/diff?a=${encodeURIComponent(a)}&b=${encodeURIComponent(b)}`);
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "对比失败" }));
          throw new Error(err.detail || "对比失败");
        }
        const data: DiffResult = await res.json();
        setDiffResult(data);
      } catch (err) {
        toast("error", err instanceof Error ? err.message : "对比失败");
      } finally {
        setDiffLoading(false);
      }
    },
    [apiBase, toast]
  );

  const handleCheckpoint = useCallback(async () => {
    if (!checkpointMessage.trim()) return;
    setCheckpointLoading(true);
    setCheckpointError(null);
    try {
      // For now, checkpoint uses an empty YAML placeholder if no script exists.
      // In production this should load the current script from the editor/API.
      const yaml = "# ScriptForge checkpoint\n";
      const res = await fetch(`${apiBase}/checkpoint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          yaml_content: yaml,
          message: checkpointMessage.trim(),
          tag: checkpointTag.trim() || null,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "存档失败" }));
        throw new Error(err.detail || "存档失败");
      }
      const data = await res.json();
      if (data.version_id) {
        toast("success", `存档已保存: ${data.short_id || data.version_id.slice(0, 7)}`);
      } else {
        toast("info", "没有变更需要保存");
      }
      setCheckpointOpen(false);
      setCheckpointMessage("");
      setCheckpointTag("");
      await fetchVersions();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "存档失败";
      setCheckpointError(msg);
      toast("error", msg);
    } finally {
      setCheckpointLoading(false);
    }
  }, [apiBase, checkpointMessage, checkpointTag, fetchVersions, toast]);

  const handleRestore = useCallback(async () => {
    if (!restoreVersionId) return;
    setRestoreLoading(true);
    setRestoreError(null);
    try {
      const res = await fetch(`${apiBase}/restore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version_id: restoreVersionId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "恢复失败" }));
        throw new Error(err.detail || "恢复失败");
      }
      toast("success", "版本已恢复，请刷新编辑器查看");
      setRestoreOpen(false);
      setRestoreVersionId(null);
      await fetchVersions();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "恢复失败";
      setRestoreError(msg);
      toast("error", msg);
    } finally {
      setRestoreLoading(false);
    }
  }, [apiBase, restoreVersionId, fetchVersions, toast]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getVersionType = (v: VersionEntry) => {
    if (v.tags.includes("ai-generated")) return "ai-generated";
    if (v.message.startsWith("restore:")) return "restored";
    if (v.message.startsWith("auto:")) return "auto-save";
    return "checkpoint";
  };

  const typeDot = (type: string) => {
    switch (type) {
      case "ai-generated":
        return "bg-sage-green";
      case "checkpoint":
        return "bg-amber-gold";
      case "restored":
        return "bg-secondary";
      default:
        return "bg-text-muted";
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
        <div>
          <h1 className="text-lg font-bold text-foreground">版本历史</h1>
          <p className="text-xs text-muted">{versions.length} 个版本</p>
        </div>
        <button
          className="flex items-center gap-1.5 rounded-md bg-amber-gold px-3 py-1.5 text-sm font-medium text-black hover:opacity-90"
          onClick={() => {
            setCheckpointOpen(true);
            setCheckpointError(null);
          }}
        >
          <Save size={14} /> 创建存档点
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Timeline */}
        <div className="w-80 overflow-y-auto border-r border-border bg-surface p-4">
          {loading ? (
            <div className="space-y-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center gap-3 py-10 text-muted">
              <AlertTriangle size={24} />
              <p className="text-sm">{error}</p>
              <button
                onClick={fetchVersions}
                className="flex items-center gap-1 rounded-md bg-accent px-3 py-1.5 text-xs hover:bg-accent/80"
              >
                <RefreshCw size={12} /> 重试
              </button>
            </div>
          ) : versions.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-10 text-muted">
              <GitCommit size={24} className="opacity-30" />
              <p className="text-sm">暂无版本记录</p>
              <p className="text-xs opacity-60">创建第一个存档点开始使用版本管理</p>
            </div>
          ) : (
            <div className="relative space-y-4 pl-4">
              {/* Vertical line */}
              <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />

              {versions.map((v) => {
                const isSelected = selectedVersion === v.version_id;
                const isCompare = compareVersion === v.version_id;
                const vType = getVersionType(v);
                return (
                  <div key={v.version_id} className="relative">
                    {/* Dot */}
                    <div
                      className={cn(
                        "absolute -left-[3px] top-1.5 h-3 w-3 rounded-full border-2",
                        isSelected
                          ? "border-amber-gold bg-amber-gold"
                          : "border-border bg-surface"
                      )}
                    >
                      <span className={cn("absolute inset-0.5 rounded-full", typeDot(vType))} />
                    </div>

                    <div
                      className={cn(
                        "cursor-pointer rounded-lg border p-3 transition-all",
                        isSelected
                          ? "border-amber-gold/50 bg-amber-gold/5"
                          : "border-transparent hover:bg-accent"
                      )}
                      onClick={() => {
                        setSelectedVersion(v.version_id);
                        if (compareVersion && compareVersion !== v.version_id) {
                          handleDiff(v.version_id, compareVersion);
                        }
                      }}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-1.5">
                          <GitCommit size={12} className="text-muted" />
                          <span className="font-mono text-xs text-muted">{v.short_id}</span>
                        </div>
                        {v.tags.length > 0 && (
                          <span className="flex items-center gap-0.5 rounded bg-amber-gold/20 px-1.5 py-0.5 text-[10px] text-amber-gold">
                            <Tag size={8} /> {v.tags[0]}
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-sm font-medium text-foreground">{v.message}</p>
                      <div className="mt-1 flex items-center gap-2 text-[10px] text-muted">
                        <span className="flex items-center gap-0.5">
                          <Clock size={10} /> {formatDate(v.committed_at)}
                        </span>
                        <span className="flex items-center gap-0.5">
                          <User size={10} /> {v.author}
                        </span>
                      </div>

                      {/* Actions */}
                      <div className="mt-2 flex gap-1">
                        <button
                          className={cn(
                            "rounded px-1.5 py-0.5 text-[10px]",
                            isCompare
                              ? "bg-amber-gold/20 text-amber-gold"
                              : "bg-page text-muted hover:bg-accent"
                          )}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (compareVersion && compareVersion !== v.version_id) {
                              // 已有对比基准且点击的是另一个版本，直接触发 diff
                              handleDiff(v.version_id, compareVersion);
                            } else {
                              // 切换当前版本的对比状态
                              setCompareVersion((prev) =>
                                prev === v.version_id ? null : v.version_id
                              );
                              if (compareVersion === v.version_id) {
                                // 取消对比时清空 diff
                                setDiffResult(null);
                              }
                            }
                          }}
                        >
                          <ArrowLeftRight size={10} className="inline mr-0.5" />
                          {isCompare ? "取消对比" : "对比"}
                        </button>
                        <button
                          className="rounded bg-page px-1.5 py-0.5 text-[10px] text-muted hover:bg-accent"
                          onClick={(e) => {
                            e.stopPropagation();
                            setRestoreVersionId(v.version_id);
                            setRestoreError(null);
                            setRestoreOpen(true);
                          }}
                        >
                          <RotateCcw size={10} className="inline mr-0.5" />
                          恢复
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Diff / Detail */}
        <div className="flex-1 overflow-y-auto bg-page p-6">
          {diffLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-1/3" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : compareVersion && !diffResult ? (
            <div className="flex h-full flex-col items-center justify-center text-muted">
              <ArrowLeftRight size={32} className="mb-2 opacity-30" />
              <p className="text-sm">已选择对比基准版本</p>
              <p className="mt-1 text-xs opacity-60">
                请点击另一个版本的「对比」按钮或卡片进行对比
              </p>
            </div>
          ) : diffResult ? (
            <div>
              <div className="mb-3 flex items-center gap-3">
                <h3 className="text-sm font-bold text-foreground">版本对比</h3>
                <span className="rounded bg-sage-green/20 px-1.5 py-0.5 text-[10px] text-sage-green">
                  +{diffResult.added_lines}
                </span>
                <span className="rounded bg-rose-500/20 px-1.5 py-0.5 text-[10px] text-rose-400">
                  -{diffResult.removed_lines}
                </span>
              </div>
              <div className="rounded-lg border border-border bg-surface p-4 font-mono text-xs leading-relaxed">
                {diffResult.diff.split("\n").map((line, i) => {
                  const isAdd = line.startsWith("+") && !line.startsWith("+++");
                  const isRemove = line.startsWith("-") && !line.startsWith("---");
                  const isHeader = line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++");
                  return (
                    <div
                      key={i}
                      className={cn(
                        "px-2 py-0.5",
                        isAdd && "bg-sage-green/10 text-sage-green",
                        isRemove && "bg-rose-500/10 text-rose-400",
                        isHeader && "text-muted"
                      )}
                    >
                      {line || " "}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center text-muted">
              <GitCommit size={32} className="mb-2 opacity-30" />
              <p className="text-sm">选择一个版本查看详情</p>
              <p className="text-xs opacity-60">或选择两个版本进行对比</p>
            </div>
          )}
        </div>
      </div>

      {/* Checkpoint Modal */}
      {checkpointOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-5 shadow-2xl">
            <h3 className="text-base font-bold text-foreground">创建存档点</h3>
            <p className="mt-1 text-xs text-muted">将当前剧本保存为一个可恢复的版本</p>
            <div className="mt-4 space-y-3">
              <div>
                <label className="mb-1 block text-xs text-muted">描述</label>
                <textarea
                  className="w-full rounded-md border border-border bg-page px-3 py-2 text-sm text-foreground outline-none focus:border-amber-gold"
                  rows={3}
                  placeholder="例如：完成第三章场景转换"
                  value={checkpointMessage}
                  onChange={(e) => setCheckpointMessage(e.target.value)}
                />
              </div>
              <div>
                <label className="mb-1 block text-xs text-muted">标签（可选）</label>
                <input
                  className="w-full rounded-md border border-border bg-page px-3 py-2 text-sm text-foreground outline-none focus:border-amber-gold"
                  placeholder="例如：v0.4"
                  value={checkpointTag}
                  onChange={(e) => setCheckpointTag(e.target.value)}
                />
              </div>
              {checkpointError && (
                <p className="text-xs text-error">{checkpointError}</p>
              )}
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-accent"
                onClick={() => setCheckpointOpen(false)}
              >
                取消
              </button>
              <button
                className="flex items-center gap-1.5 rounded-md bg-amber-gold px-3 py-1.5 text-sm font-medium text-black hover:opacity-90 disabled:opacity-40"
                disabled={!checkpointMessage.trim() || checkpointLoading}
                onClick={handleCheckpoint}
              >
                {checkpointLoading && <RefreshCw size={14} className="animate-spin" />}
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Restore Dialog */}
      {restoreOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-5 shadow-2xl">
            <div className="flex items-center gap-2 text-amber-400">
              <AlertTriangle size={18} />
              <h3 className="text-base font-bold text-foreground">确认恢复版本</h3>
            </div>
            <p className="mt-2 text-sm text-muted">
              恢复到旧版本将覆盖当前剧本内容。建议在恢复前先创建一个存档点。
            </p>
            <div className="mt-4 rounded bg-amber-gold/5 p-3 text-xs text-amber-gold">
              <strong>提示：</strong>恢复前系统会自动创建"恢复前快照"，你可以在之后随时回滚。
            </div>
            {restoreError && (
              <p className="mt-3 text-xs text-error">{restoreError}</p>
            )}
            <div className="mt-5 flex justify-end gap-2">
              <button
                className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-accent"
                onClick={() => setRestoreOpen(false)}
              >
                取消
              </button>
              <button
                className="flex items-center gap-1.5 rounded-md bg-rose-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-600 disabled:opacity-50"
                disabled={restoreLoading}
                onClick={handleRestore}
              >
                {restoreLoading && <RefreshCw size={14} className="animate-spin" />}
                确认恢复
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
