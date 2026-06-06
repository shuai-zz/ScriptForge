import { useEffect, useState, useCallback } from "react";
import { PageLoader } from "@/components/PageLoader";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Bot,
  KeyRound,
  Layers,
  Pencil,
  Plus,
  Server,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "../components/ToastContext";

type ProviderType = "anthropic" | "openai_compatible";

type PipelineStage = "stage_0" | "stage_1" | "stage_2";

interface Provider {
  id: string;
  provider_id: string;
  label: string;
  provider_type: ProviderType;
  model_name: string;
  base_url: string | null;
  api_key_masked: string;
  assigned_stages: PipelineStage[];
  parameters?: {
    temperature?: number;
    max_tokens?: number | null;
    thinking?: boolean | null;
  };
}

interface FormData {
  label: string;
  provider_type: ProviderType;
  model_name: string;
  base_url: string;
  api_key: string;
  assigned_stages: PipelineStage[];
  temperature: number;
  max_tokens: string;
  thinking: boolean;
}

const STAGE_LABELS: Record<PipelineStage, string> = {
  stage_0: "圣经分析",
  stage_1: "章节转换",
  stage_2: "剧本组装",
};

const TYPE_LABELS: Record<ProviderType, string> = {
  anthropic: "Anthropic",
  openai_compatible: "OpenAI Compatible",
};

const DEFAULT_FORM: FormData = {
  label: "",
  provider_type: "anthropic",
  model_name: "claude-sonnet-4-6",
  base_url: "",
  api_key: "",
  assigned_stages: [],
  temperature: 0.7,
  max_tokens: "",
  thinking: false,
};

export default function ProviderConfig() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormData>(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const apiBase = `/api/projects/${projectId}/providers`;

  const fetchProviders = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(apiBase);
      if (!res.ok) throw new Error("加载失败");
      const data = await res.json();
      setProviders(data);
    } catch {
      toast("error", "无法加载模型配置");
    } finally {
      setLoading(false);
    }
  }, [apiBase, toast]);

  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  const openCreate = () => {
    setEditingId(null);
    setForm(DEFAULT_FORM);
    setModalOpen(true);
  };

  const openEdit = (p: Provider) => {
    setEditingId(p.provider_id);
    setForm({
      label: p.label,
      provider_type: p.provider_type,
      model_name: p.model_name,
      base_url: p.base_url ?? "",
      api_key: "",
      assigned_stages: [...p.assigned_stages],
      temperature: p.parameters?.temperature ?? 0.7,
      max_tokens: p.parameters?.max_tokens?.toString() ?? "",
      thinking: p.parameters?.thinking ?? false,
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    const payload: Record<string, unknown> = {
      label: form.label,
      provider_type: form.provider_type,
      model_name: form.model_name,
      assigned_stages: form.assigned_stages,
      parameters: {
        temperature: form.temperature,
        max_tokens: form.max_tokens ? parseInt(form.max_tokens, 10) : null,
        thinking: form.provider_type === "anthropic" ? form.thinking : null,
      },
    };

    if (form.provider_type === "openai_compatible") {
      payload.base_url = form.base_url || null;
    }

    if (editingId) {
      if (form.api_key) payload.api_key = form.api_key;
    } else {
      payload.api_key = form.api_key;
    }

    try {
      const url = editingId ? `${apiBase}/${editingId}` : apiBase;
      const method = editingId ? "PUT" : "POST";
      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "请求失败" }));
        throw new Error(err.detail || "请求失败");
      }
      toast("success", editingId ? "配置已更新" : "模型已添加");
      closeModal();
      await fetchProviders();
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (providerId: string) => {
    if (!confirm("确定要删除这个模型配置吗？")) return;
    setDeletingId(providerId);
    try {
      const res = await fetch(`${apiBase}/${providerId}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      toast("success", "配置已删除");
      await fetchProviders();
    } catch {
      toast("error", "删除失败");
    } finally {
      setDeletingId(null);
    }
  };

  const toggleStage = (stage: PipelineStage) => {
    setForm((prev) => {
      const has = prev.assigned_stages.includes(stage);
      return {
        ...prev,
        assigned_stages: has
          ? prev.assigned_stages.filter((s) => s !== stage)
          : [...prev.assigned_stages, stage],
      };
    });
  };

  const updateForm = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-text-secondary transition-colors hover:text-text-primary"
            title="返回项目"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-text-primary">
              模型配置
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              管理项目的 LLM 提供商与阶段分配
            </p>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
        >
          <Plus className="h-4 w-4" />
          添加模型
        </button>
      </div>

      {/* Provider List */}
      {loading ? (
        <PageLoader />
      ) : providers.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-border bg-surface py-20">
          <Bot className="h-12 w-12 text-text-muted" />
          <p className="text-text-secondary">暂无模型配置</p>
          <button
            onClick={openCreate}
            className="rounded-lg border border-border bg-card px-4 py-2 text-sm text-text-primary transition-colors hover:border-primary/30"
          >
            添加第一个模型
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {providers.map((p) => (
            <div
              key={p.id}
              className="group relative overflow-hidden rounded-xl border border-border bg-surface p-6 shadow-card transition-all hover:border-primary/20 hover:shadow-card-hover"
            >
              <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

              {/* Top row: type + stages */}
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      p.provider_type === "anthropic"
                        ? "bg-tertiary/15 text-tertiary"
                        : "bg-secondary/15 text-secondary"
                    }`}
                  >
                    {p.provider_type === "anthropic" ? (
                      <Bot className="h-3 w-3" />
                    ) : (
                      <Server className="h-3 w-3" />
                    )}
                    {TYPE_LABELS[p.provider_type]}
                  </span>
                </div>
                <div className="flex gap-1">
                  {p.assigned_stages.map((s) => (
                    <span
                      key={s}
                      className="rounded-full bg-primary-muted px-2 py-0.5 text-xs text-primary"
                    >
                      {STAGE_LABELS[s]}
                    </span>
                  ))}
                  {p.assigned_stages.length === 0 && (
                    <span className="text-xs text-text-muted">未分配阶段</span>
                  )}
                </div>
              </div>

              {/* Body */}
              <div className="mb-4 space-y-2">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-medium text-text-primary">
                    {p.label}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-text-secondary">
                  <Layers className="h-3.5 w-3.5" />
                  <span>{p.model_name}</span>
                </div>
                {p.base_url && (
                  <div className="flex items-center gap-2 text-sm text-text-muted">
                    <Server className="h-3.5 w-3.5" />
                    <span className="truncate">{p.base_url}</span>
                  </div>
                )}
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <KeyRound className="h-3.5 w-3.5" />
                  <span className="font-mono">{p.api_key_masked}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 border-t border-border pt-4">
                <button
                  onClick={() => openEdit(p)}
                  className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-text-secondary transition-colors hover:bg-card hover:text-text-primary"
                >
                  <Pencil className="h-3.5 w-3.5" />
                  编辑
                </button>
                <button
                  onClick={() => handleDelete(p.provider_id)}
                  disabled={deletingId === p.provider_id}
                  className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-error/70 transition-colors hover:bg-error/10 hover:text-error disabled:opacity-50"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                  {deletingId === p.provider_id ? "删除中..." : "删除"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={closeModal}
          />
          <div className="relative z-10 w-full max-w-lg rounded-xl border border-border bg-surface shadow-dialog">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <h2 className="text-lg font-medium text-text-primary">
                {editingId ? "编辑模型配置" : "添加模型"}
              </h2>
              <button
                onClick={closeModal}
                className="rounded p-1 text-text-muted hover:text-text-primary"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5">
              {/* Label */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  显示名称
                </label>
                <input
                  type="text"
                  required
                  value={form.label}
                  onChange={(e) => updateForm("label", e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="例如：Claude 主力模型"
                />
              </div>

              {/* Provider Type */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  提供商类型
                </label>
                <select
                  value={form.provider_type}
                  onChange={(e) =>
                    updateForm("provider_type", e.target.value as ProviderType)
                  }
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                >
                  <option value="anthropic">Anthropic</option>
                  <option value="openai_compatible">OpenAI Compatible</option>
                </select>
              </div>

              {/* Model Name */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  模型名称
                </label>
                <input
                  type="text"
                  required
                  value={form.model_name}
                  onChange={(e) => updateForm("model_name", e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder={
                    form.provider_type === "anthropic"
                      ? "claude-sonnet-4-6"
                      : "gpt-4o"
                  }
                />
              </div>

              {/* Base URL (OpenAI only) */}
              {form.provider_type === "openai_compatible" && (
                <div>
                  <label className="mb-1.5 block text-sm text-text-secondary">
                    自定义 Base URL
                  </label>
                  <input
                    type="url"
                    value={form.base_url}
                    onChange={(e) => updateForm("base_url", e.target.value)}
                    className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                    placeholder="https://api.example.com/v1"
                  />
                </div>
              )}

              {/* API Key */}
              <div>
                <label className="mb-1.5 block text-sm text-text-secondary">
                  API 密钥 {editingId && "（留空则不修改）"}
                </label>
                <input
                  type="password"
                  required={!editingId}
                  value={form.api_key}
                  onChange={(e) => updateForm("api_key", e.target.value)}
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                  placeholder="sk-..."
                />
              </div>

              {/* Assigned Stages */}
              <div>
                <label className="mb-2 block text-sm text-text-secondary">
                  分配阶段
                </label>
                <div className="flex flex-wrap gap-2">
                  {(
                    ["stage_0", "stage_1", "stage_2"] as PipelineStage[]
                  ).map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => toggleStage(s)}
                      className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                        form.assigned_stages.includes(s)
                          ? "border-primary bg-primary-muted text-primary"
                          : "border-border bg-card text-text-secondary hover:text-text-primary"
                      }`}
                    >
                      {STAGE_LABELS[s]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Parameters */}
              <div className="space-y-3 rounded-lg border border-border bg-card p-4">
                <p className="text-sm font-medium text-text-primary">推理参数</p>

                <div>
                  <div className="mb-1 flex items-center justify-between">
                    <label className="text-sm text-text-secondary">温度 (Temperature)</label>
                    <span className="text-xs text-text-muted">{form.temperature}</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={2}
                    step={0.1}
                    value={form.temperature}
                    onChange={(e) =>
                      updateForm("temperature", parseFloat(e.target.value))
                    }
                    className="w-full accent-primary"
                  />
                </div>

                <div>
                  <label className="mb-1 block text-sm text-text-secondary">
                    最大 Token 数
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={form.max_tokens}
                    onChange={(e) => updateForm("max_tokens", e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary transition-colors focus:border-border-active"
                    placeholder="默认不限制"
                  />
                </div>

                {form.provider_type === "anthropic" && (
                  <label className="flex items-center gap-2 text-sm text-text-secondary">
                    <input
                      type="checkbox"
                      checked={form.thinking}
                      onChange={(e) => updateForm("thinking", e.target.checked)}
                      className="accent-primary"
                    />
                    启用 Thinking 模式
                  </label>
                )}
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
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover disabled:opacity-60"
                >
                  {saving
                    ? "保存中..."
                    : editingId
                      ? "保存修改"
                      : "添加模型"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
