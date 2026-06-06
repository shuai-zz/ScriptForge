import { useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { Users, Plus, Trash2, X, Network } from "lucide-react";
import { useToast } from "@/components/ToastContainer";
import { cn } from "@/lib/utils";
import CharacterGraph from "@/components/CharacterGraph";

interface CharacterItem {
  id: string;
  name: string;
  aliases: string[];
  role_type: string;
  traits: string[];
}

interface RelationshipItem {
  id: string;
  source_character_id: string;
  target_character_id: string;
  type: string;
  intensity: number;
}

const ROLE_COLORS: Record<string, string> = {
  protagonist: "bg-primary/20 text-primary border-primary/30",
  antagonist: "bg-rose-500/20 text-rose-400 border-rose-500/30",
  supporting: "bg-secondary/20 text-secondary border-secondary/30",
  minor: "bg-muted/20 text-text-muted border-muted/30",
};

const ROLE_LABELS: Record<string, string> = {
  protagonist: "主角",
  antagonist: "反派",
  supporting: "配角",
  minor: "龙套",
};

export default function CharactersPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { toast } = useToast();

  const [characters, setCharacters] = useState<CharacterItem[]>([]);
  const [relationships, setRelationships] = useState<RelationshipItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"list" | "graph">("list");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<CharacterItem>>({});
  const [showRelForm, setShowRelForm] = useState(false);
  const [relForm, setRelForm] = useState({ source: "", target: "", type: "friend", intensity: 3 });

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [cRes, rRes] = await Promise.all([
        fetch(`/api/projects/${projectId}/characters`),
        fetch(`/api/projects/${projectId}/characters/relationships`),
      ]);
      if (cRes.ok) setCharacters(await cRes.json());
      if (rRes.ok) setRelationships(await rRes.json());
    } catch {
      toast("error", "加载角色数据失败");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const selectedChar = useMemo(
    () => characters.find((c) => c.id === selectedCharId) || null,
    [characters, selectedCharId]
  );

  const handleCreate = async () => {
    try {
      const res = await fetch(`/api/projects/${projectId}/characters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "新角色", role_type: "supporting" }),
      });
      if (!res.ok) throw new Error("创建失败");
      const char = await res.json();
      setCharacters((prev) => [...prev, char]);
      setSelectedCharId(char.id);
      setEditing(true);
      setForm(char);
      toast("success", "角色已创建");
    } catch {
      toast("error", "创建失败");
    }
  };

  const handleUpdate = async () => {
    if (!selectedCharId) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/characters/${selectedCharId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) throw new Error("更新失败");
      const updated = await res.json();
      setCharacters((prev) => prev.map((c) => (c.id === selectedCharId ? updated : c)));
      setEditing(false);
      toast("success", "角色已更新");
    } catch {
      toast("error", "更新失败");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确定删除该角色吗？")) return;
    try {
      const res = await fetch(`/api/projects/${projectId}/characters/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error("删除失败");
      setCharacters((prev) => prev.filter((c) => c.id !== id));
      if (selectedCharId === id) setSelectedCharId(null);
      toast("success", "角色已删除");
    } catch {
      toast("error", "删除失败");
    }
  };

  const handleCreateRelationship = async () => {
    try {
      const res = await fetch(`/api/projects/${projectId}/characters/relationships`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_character_id: relForm.source,
          target_character_id: relForm.target,
          type: relForm.type,
          intensity: relForm.intensity,
        }),
      });
      if (!res.ok) throw new Error("创建失败");
      const rel = await res.json();
      setRelationships((prev) => [...prev, rel]);
      setShowRelForm(false);
      toast("success", "关系已创建");
    } catch {
      toast("error", "创建关系失败");
    }
  };

  const handleDeleteRelationship = async (id: string) => {
    try {
      const res = await fetch(`/api/projects/${projectId}/characters/relationships/${id}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("删除失败");
      setRelationships((prev) => prev.filter((r) => r.id !== id));
      toast("success", "关系已删除");
    } catch {
      toast("error", "删除关系失败");
    }
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border bg-surface px-6 py-3">
        <div className="flex items-center gap-3">
          <Users className="h-5 w-5 text-primary" />
          <h1 className="text-lg font-semibold text-text-primary">角色管理</h1>
          <span className="text-xs text-text-muted">({characters.length} 个角色)</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab("list")}
            className={cn(
              "rounded-lg px-3 py-1.5 text-xs transition-colors",
              activeTab === "list"
                ? "bg-primary-muted text-primary"
                : "text-text-secondary hover:bg-card"
            )}
          >
            列表
          </button>
          <button
            onClick={() => setActiveTab("graph")}
            className={cn(
              "flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs transition-colors",
              activeTab === "graph"
                ? "bg-primary-muted text-primary"
                : "text-text-secondary hover:bg-card"
            )}
          >
            <Network size={14} />
            关系图
          </button>
          <button
            onClick={handleCreate}
            className="flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-black transition-colors hover:bg-primary-hover"
          >
            <Plus size={14} />
            新建角色
          </button>
        </div>
      </div>

      {/* Content */}
      {activeTab === "list" ? (
        <div className="flex flex-1 overflow-hidden">
          {/* Character List */}
          <div className="w-64 border-r border-border bg-surface">
            <div className="p-2">
              {characters.length === 0 ? (
                <p className="px-2 py-4 text-center text-xs text-text-muted">暂无角色</p>
              ) : (
                <div className="space-y-1">
                  {characters.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        setSelectedCharId(c.id);
                        setEditing(false);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
                        selectedCharId === c.id
                          ? "bg-primary-muted"
                          : "hover:bg-card"
                      )}
                    >
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-card text-sm font-bold text-text-primary">
                        {c.name[0]}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="truncate text-sm font-medium text-text-primary">
                          {c.name}
                        </div>
                        <span
                          className={cn(
                            "inline-block rounded px-1.5 py-0.5 text-[10px] border",
                            ROLE_COLORS[c.role_type] || ROLE_COLORS.minor
                          )}
                        >
                          {ROLE_LABELS[c.role_type] || c.role_type}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Detail Panel */}
          <div className="flex-1 overflow-y-auto p-6">
            {selectedChar ? (
              <div className="mx-auto max-w-xl">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xl font-bold text-text-primary">{selectedChar.name}</h2>
                  <div className="flex gap-2">
                    {editing ? (
                      <>
                        <button
                          onClick={() => setEditing(false)}
                          className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-secondary hover:bg-card"
                        >
                          取消
                        </button>
                        <button
                          onClick={handleUpdate}
                          className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-black hover:bg-primary-hover"
                        >
                          保存
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          setEditing(true);
                          setForm(selectedChar);
                        }}
                        className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-secondary hover:bg-card"
                      >
                        编辑
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(selectedChar.id)}
                      className="rounded-lg p-1.5 text-text-muted hover:bg-rose-500/10 hover:text-rose-400"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>

                {editing ? (
                  <div className="space-y-4">
                    <div>
                      <label className="mb-1 block text-xs text-text-secondary">名称</label>
                      <input
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                        value={form.name || ""}
                        onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-text-secondary">类型</label>
                      <select
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                        value={form.role_type || "supporting"}
                        onChange={(e) => setForm((f) => ({ ...f, role_type: e.target.value }))}
                      >
                        {Object.entries(ROLE_LABELS).map(([value, label]) => (
                          <option key={value} value={value}>{label}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-text-secondary">别名（逗号分隔）</label>
                      <input
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                        value={(form.aliases || []).join(", ")}
                        onChange={(e) =>
                          setForm((f) => ({
                            ...f,
                            aliases: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                          }))
                        }
                      />
                    </div>
                    <div>
                      <label className="mb-1 block text-xs text-text-secondary">特质（逗号分隔）</label>
                      <input
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                        value={(form.traits || []).join(", ")}
                        onChange={(e) =>
                          setForm((f) => ({
                            ...f,
                            traits: e.target.value.split(",").map((s) => s.trim()).filter(Boolean),
                          }))
                        }
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="rounded-lg border border-border bg-surface p-4">
                      <div className="mb-2 text-xs text-text-muted">类型</div>
                      <span
                        className={cn(
                          "rounded px-2 py-0.5 text-xs border",
                          ROLE_COLORS[selectedChar.role_type] || ROLE_COLORS.minor
                        )}
                      >
                        {ROLE_LABELS[selectedChar.role_type] || selectedChar.role_type}
                      </span>
                    </div>
                    {selectedChar.aliases.length > 0 && (
                      <div className="rounded-lg border border-border bg-surface p-4">
                        <div className="mb-2 text-xs text-text-muted">别名</div>
                        <div className="flex flex-wrap gap-1">
                          {selectedChar.aliases.map((a) => (
                            <span key={a} className="rounded bg-card px-2 py-0.5 text-xs text-text-secondary">
                              {a}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedChar.traits.length > 0 && (
                      <div className="rounded-lg border border-border bg-surface p-4">
                        <div className="mb-2 text-xs text-text-muted">特质</div>
                        <div className="flex flex-wrap gap-1">
                          {selectedChar.traits.map((t) => (
                            <span key={t} className="rounded bg-card px-2 py-0.5 text-xs text-text-secondary">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Relationships */}
                    <div className="rounded-lg border border-border bg-surface p-4">
                      <div className="mb-2 flex items-center justify-between">
                        <div className="text-xs text-text-muted">关系</div>
                        <button
                          onClick={() => setShowRelForm(true)}
                          className="flex items-center gap-1 rounded bg-primary-muted px-2 py-0.5 text-[10px] text-primary hover:bg-primary/20"
                        >
                          <Plus size={10} /> 添加
                        </button>
                      </div>
                      {relationships.filter(
                        (r) =>
                          r.source_character_id === selectedChar.id ||
                          r.target_character_id === selectedChar.id
                      ).length === 0 ? (
                        <p className="text-xs text-text-muted">暂无关系</p>
                      ) : (
                        <div className="space-y-1">
                          {relationships
                            .filter(
                              (r) =>
                                r.source_character_id === selectedChar.id ||
                                r.target_character_id === selectedChar.id
                            )
                            .map((r) => {
                              const isSource = r.source_character_id === selectedChar.id;
                              const otherId = isSource ? r.target_character_id : r.source_character_id;
                              const other = characters.find((c) => c.id === otherId);
                              return (
                                <div
                                  key={r.id}
                                  className="flex items-center justify-between rounded bg-card px-2 py-1.5 text-xs"
                                >
                                  <span className="text-text-secondary">
                                    {isSource ? "→" : "←"} {other?.name || "未知"} ({r.type})
                                  </span>
                                  <div className="flex items-center gap-2">
                                    <span className="text-[10px] text-text-muted">
                                      {"★".repeat(r.intensity)}{"☆".repeat(5 - r.intensity)}
                                    </span>
                                    <button
                                      onClick={() => handleDeleteRelationship(r.id)}
                                      className="text-text-muted hover:text-rose-400"
                                    >
                                      <X size={12} />
                                    </button>
                                  </div>
                                </div>
                              );
                            })}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex h-full items-center justify-center text-text-muted">
                <p className="text-sm">选择一个角色查看详情</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <CharacterGraph
          characters={characters}
          relationships={relationships}
        />
      )}

      {/* Relationship Form Modal */}
      {showRelForm && selectedChar && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-sm rounded-xl border border-border bg-surface p-5 shadow-2xl">
            <h3 className="mb-4 text-sm font-bold text-text-primary">添加关系</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-xs text-text-secondary">目标角色</label>
                <select
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                  value={relForm.target}
                  onChange={(e) => setRelForm((f) => ({ ...f, target: e.target.value }))}
                >
                  <option value="">选择角色</option>
                  {characters
                    .filter((c) => c.id !== selectedChar.id)
                    .map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-secondary">关系类型</label>
                <select
                  className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-text-primary"
                  value={relForm.type}
                  onChange={(e) => setRelForm((f) => ({ ...f, type: e.target.value }))}
                >
                  {["lover", "family", "friend", "rival", "mentor", "enemy", "colleague", "other"].map(
                    (t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    )
                  )}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-xs text-text-secondary">强度 (1-5)</label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={relForm.intensity}
                  onChange={(e) => setRelForm((f) => ({ ...f, intensity: parseInt(e.target.value) }))}
                  className="w-full accent-primary"
                />
                <div className="text-center text-xs text-text-muted">{relForm.intensity}</div>
              </div>
            </div>
            <div className="mt-4 flex justify-end gap-2">
              <button
                onClick={() => setShowRelForm(false)}
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-text-secondary hover:bg-card"
              >
                取消
              </button>
              <button
                onClick={handleCreateRelationship}
                disabled={!relForm.target}
                className="rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-black hover:bg-primary-hover disabled:opacity-50"
              >
                创建
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
