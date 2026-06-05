import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Cog, Save } from "lucide-react";
import { useToast } from "../components/ToastContainer";

interface ProjectConfig {
  schema_version: string;
  schema_name: string;
  conversion_params: {
    target_format: string;
    language: string;
    scene_title_style: string;
    dialogue_name_style: string;
    annotation_detail_level: string;
    auto_split: boolean;
    dialogue_preservation: string;
  };
  input_chapters: Array<{ chapter_number: number; title: string; word_count: number }>;
  output_settings: {
    formats: string[];
    destination: string | null;
  };
}

const FORMAT_OPTIONS = [
  { value: "movie", label: "🎬 电影" },
  { value: "tv_series", label: "📺 电视剧" },
  { value: "stage_play", label: "🎭 舞台剧" },
];

const TITLE_STYLE_OPTIONS = [
  { value: "international", label: "国际 (INT./EXT.)" },
  { value: "chinese", label: "中文 (内/外)" },
];

const NAME_STYLE_OPTIONS = [
  { value: "full_name", label: "全名" },
  { value: "nickname", label: "昵称" },
  { value: "role", label: "角色称谓" },
];

const ANNOTATION_OPTIONS = [
  { value: "minimal", label: "最少" },
  { value: "standard", label: "标准" },
  { value: "verbose", label: "详细" },
];

const DIALOGUE_OPTIONS = [
  { value: "rewrite", label: "重写" },
  { value: "preserve", label: "保留原文" },
  { value: "enhance", label: "增强" },
];

const EXPORT_FORMATS = [
  { value: "yaml", label: "YAML" },
  { value: "pdf", label: "PDF" },
  { value: "fountain", label: "Fountain" },
  { value: "fdx", label: "Final Draft (FDX)" },
];

export default function ProjectSettings() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState<ProjectConfig | null>(null);

  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/config`);
      if (!res.ok) throw new Error("加载失败");
      const data: ProjectConfig = await res.json();
      setConfig(data);
    } catch {
      toast("error", "无法加载项目配置");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const updateParam = <
    K extends keyof ProjectConfig["conversion_params"],
    V extends ProjectConfig["conversion_params"][K],
  >(
    key: K,
    value: V,
  ) => {
    setConfig((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        conversion_params: { ...prev.conversion_params, [key]: value },
      };
    });
  };

  const toggleExportFormat = (fmt: string) => {
    setConfig((prev) => {
      if (!prev) return prev;
      const formats = prev.output_settings.formats;
      const updated = formats.includes(fmt)
        ? formats.filter((f) => f !== fmt)
        : [...formats, fmt];
      return {
        ...prev,
        output_settings: { ...prev.output_settings, formats: updated },
      };
    });
  };

  const handleSave = async () => {
    if (!config) return;
    setSaving(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/config`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "保存失败" }));
        throw new Error(err.detail || "保存失败");
      }
      toast("success", "配置已保存");
    } catch (err) {
      toast("error", err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-8">
        <p className="text-text-secondary">配置加载失败。</p>
      </div>
    );
  }

  const params = config.conversion_params;

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-text-secondary transition-colors hover:text-text-primary"
            title="返回"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-text-primary">
              项目设置
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              配置转换参数和导出选项
            </p>
          </div>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover disabled:opacity-60"
        >
          <Save className="h-4 w-4" />
          {saving ? "保存中..." : "保存配置"}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Conversion Parameters */}
        <div className="rounded-xl border border-border bg-surface p-6">
          <div className="mb-4 flex items-center gap-2">
            <Cog className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-medium text-text-primary">转换参数</h2>
          </div>

          {/* Target Format */}
          <div className="mb-5">
            <label className="mb-2 block text-sm text-text-secondary">
              目标格式
            </label>
            <div className="flex flex-wrap gap-2">
              {FORMAT_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => updateParam("target_format", o.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    params.target_format === o.value
                      ? "border-primary bg-primary-muted text-primary"
                      : "border-border bg-card text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Scene Title Style */}
          <div className="mb-5">
            <label className="mb-2 block text-sm text-text-secondary">
              场景标题风格
            </label>
            <div className="flex flex-wrap gap-2">
              {TITLE_STYLE_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => updateParam("scene_title_style", o.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    params.scene_title_style === o.value
                      ? "border-primary bg-primary-muted text-primary"
                      : "border-border bg-card text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Dialogue Name Style */}
          <div className="mb-5">
            <label className="mb-2 block text-sm text-text-secondary">
              对白姓名风格
            </label>
            <div className="flex flex-wrap gap-2">
              {NAME_STYLE_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => updateParam("dialogue_name_style", o.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    params.dialogue_name_style === o.value
                      ? "border-primary bg-primary-muted text-primary"
                      : "border-border bg-card text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Annotation Detail Level */}
          <div className="mb-5">
            <label className="mb-2 block text-sm text-text-secondary">
              注释详细程度
            </label>
            <div className="flex flex-wrap gap-2">
              {ANNOTATION_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => updateParam("annotation_detail_level", o.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    params.annotation_detail_level === o.value
                      ? "border-primary bg-primary-muted text-primary"
                      : "border-border bg-card text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Dialogue Preservation */}
          <div className="mb-5">
            <label className="mb-2 block text-sm text-text-secondary">
              原文对白处理
            </label>
            <div className="flex flex-wrap gap-2">
              {DIALOGUE_OPTIONS.map((o) => (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => updateParam("dialogue_preservation", o.value)}
                  className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                    params.dialogue_preservation === o.value
                      ? "border-primary bg-primary-muted text-primary"
                      : "border-border bg-card text-text-secondary hover:text-text-primary"
                  }`}
                >
                  {o.label}
                </button>
              ))}
            </div>
          </div>

          {/* Auto Split */}
          <div className="mb-5">
            <label className="flex items-center gap-2 text-sm text-text-secondary">
              <input
                type="checkbox"
                checked={params.auto_split}
                onChange={(e) => updateParam("auto_split", e.target.checked)}
                className="accent-primary"
              />
              自动分隔场景（AI 自动判断场景边界）
            </label>
          </div>

          {/* Language */}
          <div>
            <label className="mb-2 block text-sm text-text-secondary">
              输出语言
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => updateParam("language", "zh")}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                  params.language === "zh"
                    ? "border-primary bg-primary-muted text-primary"
                    : "border-border bg-card text-text-secondary hover:text-text-primary"
                }`}
              >
                中文
              </button>
              <button
                type="button"
                onClick={() => updateParam("language", "en")}
                className={`rounded-lg border px-3 py-1.5 text-sm transition-colors ${
                  params.language === "en"
                    ? "border-primary bg-primary-muted text-primary"
                    : "border-border bg-card text-text-secondary hover:text-text-primary"
                }`}
              >
                English
              </button>
            </div>
          </div>
        </div>

        {/* Export Settings */}
        <div className="rounded-xl border border-border bg-surface p-6">
          <div className="mb-4 flex items-center gap-2">
            <Cog className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-medium text-text-primary">导出设置</h2>
          </div>

          <label className="mb-2 block text-sm text-text-secondary">
            导出格式（多选）
          </label>
          <div className="space-y-2">
            {EXPORT_FORMATS.map((fmt) => (
              <label
                key={fmt.value}
                className="flex items-center gap-3 rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-text-primary transition-colors hover:border-primary/20"
              >
                <input
                  type="checkbox"
                  checked={config.output_settings.formats.includes(fmt.value)}
                  onChange={() => toggleExportFormat(fmt.value)}
                  className="accent-primary"
                />
                {fmt.label}
              </label>
            ))}
          </div>

          {/* Chapter Summary */}
          {config.input_chapters.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-3 text-sm font-medium text-text-primary">
                章节列表（只读）
              </h3>
              <div className="max-h-[260px] space-y-1 overflow-y-auto rounded-lg border border-border bg-card p-3">
                {config.input_chapters.map((ch) => (
                  <div
                    key={ch.chapter_number}
                    className="flex items-center justify-between rounded px-2 py-1.5 text-sm"
                  >
                    <span className="text-text-secondary">
                      {ch.chapter_number}. {ch.title}
                    </span>
                    <span className="text-xs text-text-muted">
                      {ch.word_count.toLocaleString()} 字
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
