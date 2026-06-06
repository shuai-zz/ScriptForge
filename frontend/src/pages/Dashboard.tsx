import { useEffect, useState, useCallback } from "react";
import { PageLoader } from "@/components/PageLoader";
import { useNavigate } from "react-router-dom";
import {
  BookOpen,
  Clapperboard,
  Plus,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useToast } from "../components/ToastContainer";
import { EmptyState } from "@/components/EmptyState";
import { motion } from "framer-motion";
import { OnboardingWizard } from "@/components/OnboardingWizard";

interface ProjectCard {
  id: string;
  name: string;
  description: string | null;
  status: string;
  config: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  chapter_count: number;
  scene_count: number;
  character_count: number;
}

const STATUS_LABELS: Record<string, string> = {
  draft: "草稿",
  active: "进行中",
  completed: "已完成",
  archived: "已归档",
};

const FORMAT_LABELS: Record<string, string> = {
  movie: "🎬 电影",
  tv_series: "📺 电视剧",
  stage_play: "🎭 舞台剧",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [projects, setProjects] = useState<ProjectCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create modal
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({
    name: "",
    description: "",
    target_format: "movie",
  });
  const [creating, setCreating] = useState(false);

  // Delete confirmation
  const [deleteTarget, setDeleteTarget] = useState<ProjectCard | null>(null);
  const [deleting, setDeleting] = useState(false);

  const fetchProjects = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/projects");
      if (!res.ok) throw new Error("加载失败");
      const data = await res.json();
      setProjects(data);
    } catch {
      setError("无法加载项目列表");
      toast("error", "无法加载项目列表");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "创建失败" }));
        throw new Error(err.detail || "创建失败");
      }
      const project = await res.json();
      toast("success", "项目已创建");
      setCreateOpen(false);
      setForm({ name: "", description: "", target_format: "movie" });
      // Navigate to project
      navigate(`/projects/${project.id}`);
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "创建失败");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/projects/${deleteTarget.id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("删除失败");
      toast("success", `项目「${deleteTarget.name}」已删除`);
      setDeleteTarget(null);
      await fetchProjects();
    } catch {
      toast("error", "删除失败");
    } finally {
      setDeleting(false);
    }
  };

  const getProgress = (p: ProjectCard): number => {
    if (p.config?.target_format === "tv_series") return p.chapter_count * 10;
    if (p.scene_count > 0 && p.chapter_count > 0) return Math.min(100, p.scene_count * 5);
    if (p.chapter_count > 0) return 25;
    return 0;
  };

  const getProgressLabel = (p: ProjectCard): string => {
    if (p.scene_count > 0) return `${p.scene_count} 场景`;
    if (p.chapter_count > 0) return `${p.chapter_count} 章`;
    return "草稿";
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-text-primary">
            ScriptForge
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            AI 辅助剧本创作工坊 — 将小说转换为结构化剧本
          </p>
        </div>
        <button
          onClick={() => setCreateOpen(true)}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
        >
          <Plus className="h-4 w-4" />
          新建项目
        </button>
      </div>

      <h2 className="mb-6 text-lg font-medium text-text-primary">📖 我的项目</h2>

      {/* Loading */}
      {loading ? (
        <PageLoader />
      ) : error && projects.length === 0 ? (
        /* Error state */
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-error/30 bg-error/5 py-20">
          <p className="text-text-secondary">{error}</p>
          <button
            onClick={fetchProjects}
            className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-text-primary transition-colors hover:border-primary/30"
          >
            重试
          </button>
        </div>
      ) : projects.length === 0 ? (
        <EmptyState
          icon={<Clapperboard className="h-12 w-12" />}
          title="还没有项目"
          description="创建一个新项目，开始将小说转换为剧本。"
          action={
            <button
              onClick={() => setCreateOpen(true)}
              className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-500"
            >
              创建第一个项目
            </button>
          }
        />
      ) : (
        /* Project Grid */
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p) => {
            const progress = getProgress(p);
            return (
              <motion.div
                key={p.id}
                onClick={() => navigate(`/projects/${p.id}`)}
                whileHover={{ y: -4, scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 300, damping: 20 }}
                className="group relative cursor-pointer overflow-hidden rounded-xl border border-neutral-800 bg-neutral-900 p-6 shadow-md transition-colors hover:border-amber-600/30 hover:shadow-lg"
              >
                {/* Top glow line */}
                <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

                <div className="mb-4 flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-muted">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="truncate font-medium text-text-primary">
                      《{p.name}》
                    </h3>
                    <p className="text-xs text-text-muted">
                      {new Date(p.updated_at || p.created_at).toLocaleDateString("zh-CN", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                  {/* Delete button — visible on hover */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setDeleteTarget(p);
                    }}
                    className="rounded-lg p-1.5 text-text-muted opacity-0 transition-colors hover:bg-error/10 hover:text-error group-hover:opacity-100"
                    title="删除项目"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>

                {/* Description */}
                {p.description && (
                  <p className="mb-3 line-clamp-2 text-sm text-text-secondary">
                    {p.description}
                  </p>
                )}

                {/* Progress */}
                <div className="mb-3 flex items-center gap-2">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-card">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-300"
                      style={{ width: `${Math.max(4, progress)}%` }}
                    />
                  </div>
                  <span className="shrink-0 text-xs text-text-muted">
                    {getProgressLabel(p)}
                  </span>
                </div>

                {/* Tags */}
                <div className="flex gap-2">
                  <span className="rounded-full bg-card px-2.5 py-0.5 text-xs text-text-secondary">
                    {FORMAT_LABELS[(p.config as Record<string, string> | null)?.target_format as string] || "🎬 电影"}
                  </span>
                  {p.character_count > 0 && (
                    <span className="rounded-full bg-card px-2.5 py-0.5 text-xs text-text-secondary">
                      <Users className="mr-1 inline h-3 w-3" />
                      {p.character_count} 角色
                    </span>
                  )}
                  <span className="rounded-full bg-card px-2.5 py-0.5 text-xs text-text-secondary">
                    {STATUS_LABELS[p.status] || p.status}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Create Modal */}
      {createOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setCreateOpen(false)}
          />
          <div className="relative z-10 w-full max-w-md rounded-xl border border-border bg-surface shadow-dialog">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h2 className="text-lg font-medium text-text-primary">新建项目</h2>
              <button
                onClick={() => setCreateOpen(false)}
                className="rounded p-1 text-text-muted hover:text-text-primary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreate} className="space-y-5 px-6 py-5">
              {/* Name */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  项目名称 <span className="text-error">*</span>
                </label>
                <input
                  type="text"
                  required
                  maxLength={255}
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="例如：长夜将明"
                />
              </div>

              {/* Description */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  描述
                </label>
                <textarea
                  rows={3}
                  value={form.description}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, description: e.target.value }))
                  }
                  className="w-full resize-none rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="可选的项目描述"
                />
              </div>

              {/* Target Format */}
              <div>
                <label className="mb-2 block text-sm text-text-secondary">
                  目标格式
                </label>
                <div className="flex flex-wrap gap-2">
                  {(["movie", "tv_series", "stage_play"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      type="button"
                      onClick={() => setForm((f) => ({ ...f, target_format: fmt }))}
                      className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                        form.target_format === fmt
                          ? "border-primary bg-primary-muted text-primary"
                          : "border-border bg-card text-text-secondary hover:text-text-primary"
                      }`}
                    >
                      {FORMAT_LABELS[fmt]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setCreateOpen(false)}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-text-primary transition-colors hover:border-primary/30"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover disabled:opacity-60"
                >
                  {creating ? "创建中..." : "创建项目"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setDeleteTarget(null)}
          />
          <div className="relative z-10 w-full max-w-sm rounded-xl border border-border bg-surface shadow-dialog">
            <div className="px-6 py-5">
              <h2 className="text-lg font-medium text-text-primary">删除项目</h2>
              <p className="mt-2 text-sm text-text-secondary">
                确定要删除「{deleteTarget.name}」吗？此操作将同时删除所有章节、剧本和相关数据，且不可撤销。
              </p>
            </div>
            <div className="flex justify-end gap-3 border-t border-border px-6 py-4">
              <button
                onClick={() => setDeleteTarget(null)}
                className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-text-primary transition-colors hover:border-primary/30"
              >
                取消
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-lg bg-error px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-error/80 disabled:opacity-60"
              >
                {deleting ? "删除中..." : "确认删除"}
              </button>
            </div>
          </div>
        </div>
      )}
      <OnboardingWizard />
    </div>
  );
}
