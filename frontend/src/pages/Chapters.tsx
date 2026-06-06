import { useEffect, useState, useCallback } from "react";
import { PageLoader } from "@/components/PageLoader";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  FileUp,
  GripVertical,
  Hash,
  Pencil,
  Plus,
  Save,
  Trash2,
  X,
  Loader2,
} from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { toast } from "../components/ToastContext";
import { EmptyState } from "@/components/EmptyState";

interface Chapter {
  id: string;
  number: number;
  title: string;
  word_count: number;
  status: string;
  created_at: string | null;
  updated_at: string | null;
}

interface ChapterDetail extends Chapter {
  project_id: string;
  raw_text: string;
}

const STATUS_LABELS: Record<string, { label: string; cls: string }> = {
  pending: { label: "待处理", cls: "text-text-muted" },
  processing: { label: "处理中", cls: "text-warning" },
  completed: { label: "已完成", cls: "text-success" },
  error: { label: "出错", cls: "text-error" },
};

// ── Sortable Row Component ──

function SortableChapterRow({
  chapter,
  onEdit,
  onDelete,
  deletingId,
}: {
  chapter: Chapter;
  onEdit: (c: Chapter) => void;
  onDelete: (c: Chapter) => void;
  deletingId: string | null;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: chapter.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const status = STATUS_LABELS[chapter.status] || STATUS_LABELS.pending;

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-3"
    >
      {/* Drag handle */}
      <button
        {...attributes}
        {...listeners}
        className="cursor-grab text-text-muted hover:text-text-secondary"
        tabIndex={-1}
      >
        <GripVertical className="h-4 w-4" />
      </button>

      {/* Number */}
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded bg-surface text-xs font-mono text-text-muted">
        {chapter.number}
      </span>

      {/* Title & meta */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-text-primary">{chapter.title}</p>
        <p className="text-xs text-text-muted">
          {chapter.word_count.toLocaleString()} 字 · <span className={status.cls}>{status.label}</span>
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={() => onEdit(chapter)}
          className="rounded p-1.5 text-text-muted hover:bg-card-hover hover:text-text-secondary"
          title="编辑"
        >
          <Pencil className="h-3.5 w-3.5" />
        </button>
        <button
          onClick={() => onDelete(chapter)}
          disabled={deletingId === chapter.id}
          className="rounded p-1.5 text-text-muted hover:bg-error/10 hover:text-error disabled:opacity-50"
          title="删除"
        >
          {deletingId === chapter.id ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Trash2 className="h-3.5 w-3.5" />
          )}
        </button>
      </div>
    </div>
  );
}

// ── Page Component ──

export default function ChaptersPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);

  // Add/Edit
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [_editDetail, setEditDetail] = useState<ChapterDetail | null>(null);
  const [form, setForm] = useState({ title: "", raw_text: "" });
  const [saving, setSaving] = useState(false);

  // Delete
  const [deletingId, setDeletingId] = useState<string | null>(null);

  // Upload
  const [uploading, setUploading] = useState(false);

  const apiBase = `/api/projects/${projectId}/chapters`;

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const fetchChapters = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(apiBase);
      if (!res.ok) throw new Error("加载失败");
      const data: Chapter[] = await res.json();
      setChapters(data);
    } catch {
      toast("error", "无法加载章节列表");
    } finally {
      setLoading(false);
    }
  }, [apiBase, toast]);

  useEffect(() => {
    fetchChapters();
  }, [fetchChapters]);

  const openCreate = () => {
    setEditingId(null);
    setEditDetail(null);
    setForm({ title: "", raw_text: "" });
    setModalOpen(true);
  };

  const openEdit = async (ch: Chapter) => {
    try {
      const res = await fetch(`${apiBase}/${ch.id}`);
      if (!res.ok) throw new Error("加载失败");
      const detail: ChapterDetail = await res.json();
      setEditingId(ch.id);
      setEditDetail(detail);
      setForm({ title: detail.title, raw_text: detail.raw_text });
      setModalOpen(true);
    } catch {
      toast("error", "无法加载章节详情");
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
    setEditDetail(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingId) {
        const res = await fetch(`${apiBase}/${editingId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: form.title, raw_text: form.raw_text }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "保存失败" }));
          throw new Error(err.detail || "保存失败");
        }
        toast("success", "章节已更新");
      } else {
        const res = await fetch(apiBase, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: form.title || "未命名章节", raw_text: form.raw_text }),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "添加失败" }));
          throw new Error(err.detail || "添加失败");
        }
        toast("success", "章节已添加");
      }
      closeModal();
      await fetchChapters();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (ch: Chapter) => {
    if (!confirm(`确定要删除「${ch.title}」吗？`)) return;
    setDeletingId(ch.id);
    try {
      const res = await fetch(`${apiBase}/${ch.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      toast("success", "章节已删除");
      await fetchChapters();
    } catch {
      toast("error", "删除失败");
    } finally {
      setDeletingId(null);
    }
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = chapters.findIndex((c) => c.id === active.id);
    const newIndex = chapters.findIndex((c) => c.id === over.id);
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(chapters, oldIndex, newIndex);
    setChapters(reordered);

    // Persist reorder
    try {
      const res = await fetch(`${apiBase}/reorder`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order: reordered.map((c) => c.id) }),
      });
      if (!res.ok) {
        // Revert on failure
        await fetchChapters();
        toast("error", "排序保存失败");
      }
    } catch {
      await fetchChapters();
      toast("error", "排序保存失败");
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${apiBase}/upload`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "上传失败" }));
        throw new Error(err.detail || "上传失败");
      }
      toast("success", `「${file.name}」已上传`);
      await fetchChapters();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "上传失败");
    } finally {
      setUploading(false);
      // Clear the input
      e.target.value = "";
    }
  };

  const canConvert = chapters.length >= 3;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-text-secondary transition-colors hover:text-text-primary"
            title="返回"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-text-primary">
              章节管理
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              上传或粘贴小说章节，拖拽排序
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Conversion hint */}
          {!canConvert && chapters.length > 0 && (
            <span className="text-xs text-warning">
              还需要 {3 - chapters.length} 章才能开始转换
            </span>
          )}
          {canConvert && (
            <button
              onClick={() => navigate(`/projects/${projectId}/convert`)}
              className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-secondary-hover"
            >
              开始转换 ({chapters.length} 章)
            </button>
          )}
          <label
            className={`flex cursor-pointer items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-sm text-text-secondary transition-colors hover:text-text-primary ${
              uploading ? "pointer-events-none opacity-50" : ""
            }`}
          >
            <FileUp className="h-4 w-4" />
            {uploading ? "上传中..." : "上传文件"}
            <input
              type="file"
              accept=".txt,.md,text/plain,text/markdown"
              className="hidden"
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
          <button
            onClick={openCreate}
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
          >
            <Plus className="h-4 w-4" />
            添加章节
          </button>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <PageLoader />
      ) : chapters.length === 0 ? (
        <EmptyState
          icon={<Hash className="h-12 w-12" />}
          title="还没有章节"
          description="至少需要 3 章才能启动 AI 转换。可以粘贴文本、上传 .txt/.md 文件。"
          action={
            <div className="flex gap-3">
              <button
                onClick={openCreate}
                className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-500"
              >
                粘贴文本
              </button>
              <label className="cursor-pointer rounded-lg border border-neutral-700 bg-neutral-800 px-4 py-2 text-sm text-neutral-200 transition-colors hover:border-amber-600/50">
                上传文件
                <input
                  type="file"
                  accept=".txt,.md,text/plain,text/markdown"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </label>
            </div>
          }
        />
      ) : (
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={chapters.map((c) => c.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-2">
              {chapters.map((ch) => (
                <SortableChapterRow
                  key={ch.id}
                  chapter={ch}
                  onEdit={openEdit}
                  onDelete={handleDelete}
                  deletingId={deletingId}
                />
              ))}
            </div>
          </SortableContext>
        </DndContext>
      )}

      {/* Add/Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeModal}
          />
          <div className="relative z-10 w-full max-w-2xl rounded-xl border border-border bg-surface shadow-dialog">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h2 className="text-lg font-medium text-text-primary">
                {editingId ? "编辑章节" : "添加章节"}
              </h2>
              <button
                onClick={closeModal}
                className="rounded p-1 text-text-muted hover:text-text-primary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5">
              {/* Title */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  章节标题 <span className="text-error">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={form.title}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, title: e.target.value }))
                  }
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="例如：第一章·离别"
                />
              </div>

              {/* Text area */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  章节内容 <span className="text-error">*</span>
                </label>
                <textarea
                  required
                  rows={16}
                  value={form.raw_text}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, raw_text: e.target.value }))
                  }
                  className="w-full resize-y rounded-lg border border-border bg-card px-3 py-2 font-mono text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="粘贴小说章节内容…"
                />
                <p className="mt-1 text-xs text-text-muted">
                  {form.raw_text.length.toLocaleString()} 字符
                </p>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-text-primary transition-colors hover:border-primary/30"
                >
                  取消
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover disabled:opacity-60"
                >
                  <Save className="h-4 w-4" />
                  {saving ? "保存中..." : editingId ? "保存修改" : "添加章节"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
