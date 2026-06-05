import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { cn } from "@/lib/utils";
import {
  GitCommit,
  Tag,
  ArrowLeftRight,
  RotateCcw,
  Save,
  Clock,
  User,
  AlertTriangle,
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
  useParams<{ projectId: string }>();
  const [versions, setVersions] = useState<VersionEntry[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [compareVersion, setCompareVersion] = useState<string | null>(null);
  const [diffResult, setDiffResult] = useState<DiffResult | null>(null);
  const [, setLoading] = useState(false);
  const [checkpointOpen, setCheckpointOpen] = useState(false);
  const [checkpointMessage, setCheckpointMessage] = useState("");
  const [checkpointTag, setCheckpointTag] = useState("");
  const [restoreOpen, setRestoreOpen] = useState(false);
  const [restoreVersionId, setRestoreVersionId] = useState<string | null>(null);
  // const [, setYamlContent] = useState("");

  // Load demo data
  useEffect(() => {
    const demo: VersionEntry[] = [
      {
        version_id: "abc1234def5678",
        short_id: "abc1234",
        message: "feat: 完成第三章场景转换",
        committed_at: "2026-06-05T14:30:00Z",
        author: "ScriptForge",
        tags: ["v0.3"],
      },
      {
        version_id: "def5678abc1234",
        short_id: "def5678",
        message: "fix: 调整丁仪对话口语化",
        committed_at: "2026-06-04T10:15:00Z",
        author: "ScriptForge",
        tags: [],
      },
      {
        version_id: "ghi9012jkl3456",
        short_id: "ghi9012",
        message: "feat: 添加台球厅场景",
        committed_at: "2026-06-03T18:00:00Z",
        author: "ScriptForge",
        tags: ["v0.2"],
      },
      {
        version_id: "jkl3456ghi9012",
        short_id: "jkl3456",
        message: "init: 项目初始化",
        committed_at: "2026-06-01T09:00:00Z",
        author: "ScriptForge",
        tags: ["v0.1"],
      },
    ];
    setVersions(demo);
  }, []);

  const handleDiff = useCallback(async (_a: string, _b: string) => {
    setLoading(true);
    try {
      // Demo diff
      const demoDiff: DiffResult = {
        diff: `--- a/script.yaml\n+++ b/script.yaml\n@@ -15,7 +15,7 @@\n scenes:\n   - scene_id: s3\n     scene_number: 3\n-    slug: INT. 作战中心 - NIGHT\n+    slug: INT. 作战中心会议室 - NIGHT\n     blocks:\n       - block_id: b6\n         type: action`,
        added_lines: 1,
        removed_lines: 1,
      };
      setDiffResult(demoDiff);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleCheckpoint = useCallback(async () => {
    if (!checkpointMessage.trim()) return;
    // TODO: call API
    setVersions((prev) => [
      {
        version_id: Date.now().toString(16),
        short_id: Date.now().toString(16).slice(0, 7),
        message: checkpointMessage,
        committed_at: new Date().toISOString(),
        author: "ScriptForge",
        tags: checkpointTag ? [checkpointTag] : [],
      },
      ...prev,
    ]);
    setCheckpointOpen(false);
    setCheckpointMessage("");
    setCheckpointTag("");
  }, [checkpointMessage, checkpointTag]);

  const handleRestore = useCallback(async () => {
    if (!restoreVersionId) return;
    // TODO: call API
    setRestoreOpen(false);
    setRestoreVersionId(null);
  }, [restoreVersionId]);

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("zh-CN", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
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
          onClick={() => setCheckpointOpen(true)}
        >
          <Save size={14} /> 创建存档点
        </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Timeline */}
        <div className="w-80 overflow-y-auto border-r border-border bg-surface p-4">
          <div className="relative space-y-4 pl-4">
            {/* Vertical line */}
            <div className="absolute left-[19px] top-2 bottom-2 w-px bg-border" />

            {versions.map((v) => {
              const isSelected = selectedVersion === v.version_id;
              const isCompare = compareVersion === v.version_id;
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
                  />

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
                          setCompareVersion((prev) =>
                            prev === v.version_id ? null : v.version_id
                          );
                          setDiffResult(null);
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
        </div>

        {/* Diff / Detail */}
        <div className="flex-1 overflow-y-auto bg-page p-6">
          {diffResult ? (
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
                  const isAdd = line.startsWith("+");
                  const isRemove = line.startsWith("-");
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
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <button
                className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-accent"
                onClick={() => setCheckpointOpen(false)}
              >
                取消
              </button>
              <button
                className="rounded-md bg-amber-gold px-3 py-1.5 text-sm font-medium text-black hover:opacity-90 disabled:opacity-40"
                disabled={!checkpointMessage.trim()}
                onClick={handleCheckpoint}
              >
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
            <div className="mt-5 flex justify-end gap-2">
              <button
                className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-accent"
                onClick={() => setRestoreOpen(false)}
              >
                取消
              </button>
              <button
                className="rounded-md bg-rose-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-rose-600"
                onClick={handleRestore}
              >
                确认恢复
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
