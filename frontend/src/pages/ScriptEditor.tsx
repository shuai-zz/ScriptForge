import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { ScriptV1, ScriptBlock, Scene } from "@/types/script";
import SceneTimeline from "@/components/script-editor/SceneTimeline";
import SceneNav from "@/components/script-editor/SceneNav";
import SceneContainer from "@/components/script-editor/SceneContainer";
import CommandPalette from "@/components/script-editor/CommandPalette";
import AnnotationSidebar from "@/components/script-editor/AnnotationSidebar";
import ExportDialog from "@/components/script-editor/ExportDialog";
import { toast } from "@/components/ToastContext";
import { cn } from "@/lib/utils";
import { Keyboard, Maximize2, Minimize2, Download, X, Loader2, GitCommit, FileText } from "lucide-react";

/** Annotation shape consumed by the editor's sidebar. */
interface EditorAnnotation {
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

/** Map a backend annotation (GET /annotations) into the editor's shape. */
function mapAnnotation(a: {
  id: string;
  annotation_id: string;
  severity: EditorAnnotation["severity"];
  category: string;
  title: string;
  description: string;
  confidence?: number;
  status?: EditorAnnotation["status"];
  target_reference?: { block_id?: string; scene_id?: string } | null;
  alternatives?: EditorAnnotation["alternatives"];
}): EditorAnnotation {
  const ref = a.target_reference ?? {};
  return {
    id: a.id,
    annotation_id: a.annotation_id,
    severity: a.severity,
    category: a.category,
    title: a.title,
    description: a.description,
    confidence: a.confidence ?? 0,
    status: a.status ?? "pending",
    block_id: ref.block_id,
    scene_id: ref.scene_id,
    alternatives: a.alternatives ?? [],
  };
}

export default function ScriptEditor() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [script, setScript] = useState<ScriptV1 | null>(null);
  const [annotations, setAnnotations] = useState<EditorAnnotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSceneId, setActiveSceneId] = useState<string | null>(null);
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [hoveredBlockId, setHoveredBlockId] = useState<string | null>(null);
  const [focusMode, setFocusMode] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [checkpointOpen, setCheckpointOpen] = useState(false);
  const [checkpointMessage, setCheckpointMessage] = useState("");
  const [checkpointSaving, setCheckpointSaving] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  /** ---- Load real script + annotations ---- */
  useEffect(() => {
    if (!projectId) return;
    let cancelled = false;
    (async () => {
      setLoading(true);
      try {
        const [sRes, aRes] = await Promise.all([
          fetch(`/api/projects/${projectId}/script`),
          fetch(`/api/projects/${projectId}/annotations`),
        ]);
        if (cancelled) return;
        if (sRes.ok) {
          const data: ScriptV1 = await sRes.json();
          setScript(data);
          setActiveSceneId(data.scenes[0]?.scene_id ?? null);
        } else {
          setScript(null); // 404 → empty state (project not converted yet)
        }
        if (aRes.ok) {
          const raw = await aRes.json();
          setAnnotations(Array.isArray(raw) ? raw.map(mapAnnotation) : []);
        }
      } catch {
        if (!cancelled) toast("error", "加载剧本数据失败");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  /** ---- Block operations ---- */
  const updateBlock = useCallback((sceneId: string, blockId: string, updates: Partial<ScriptBlock>) => {
    setScript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        scenes: prev.scenes.map((s) =>
          s.scene_id === sceneId
            ? { ...s, blocks: s.blocks.map((b) => (b.block_id === blockId ? { ...b, ...updates } : b)) }
            : s
        ),
      };
    });
  }, []);

  const addBlock = useCallback((sceneId: string, afterBlockId?: string, type: ScriptBlock["type"] = "action") => {
    const newBlock: ScriptBlock = {
      block_id: `b-${Date.now()}`,
      order: 0,
      type,
      text: type === "action" ? "" : undefined,
      char_id: type === "dialogue" ? script?.characters[0]?.character_id : undefined,
      char_name: type === "dialogue" ? script?.characters[0]?.name : undefined,
      line: type === "dialogue" ? "" : undefined,
      annotation_refs: [],
    };
    setScript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        scenes: prev.scenes.map((s) => {
          if (s.scene_id !== sceneId) return s;
          const idx = afterBlockId ? s.blocks.findIndex((b) => b.block_id === afterBlockId) : -1;
          const insertAt = idx >= 0 ? idx + 1 : s.blocks.length;
          const newBlocks = [...s.blocks];
          newBlocks.splice(insertAt, 0, newBlock);
          return { ...s, blocks: newBlocks.map((b, i) => ({ ...b, order: i })) };
        }),
      };
    });
    setSelectedBlockId(newBlock.block_id);
  }, [script]);

  const deleteBlock = useCallback((sceneId: string, blockId: string) => {
    setScript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        scenes: prev.scenes.map((s) =>
          s.scene_id === sceneId
            ? { ...s, blocks: s.blocks.filter((b) => b.block_id !== blockId).map((b, i) => ({ ...b, order: i })) }
            : s
        ),
      };
    });
    setSelectedBlockId(null);
  }, []);

  const reorderBlocks = useCallback((sceneId: string, blockIds: string[]) => {
    setScript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        scenes: prev.scenes.map((s) => {
          if (s.scene_id !== sceneId) return s;
          const map = new Map(s.blocks.map((b) => [b.block_id, b]));
          const newBlocks = blockIds.map((id) => map.get(id)!).map((b, i) => ({ ...b, order: i }));
          return { ...s, blocks: newBlocks };
        }),
      };
    });
  }, []);

  const toggleBlockType = useCallback((sceneId: string, blockId: string) => {
    setScript((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        scenes: prev.scenes.map((s) =>
          s.scene_id === sceneId
            ? {
                ...s,
                blocks: s.blocks.map((b) => {
                  if (b.block_id !== blockId) return b;
                  const newType = b.type === "action" ? "dialogue" : "action";
                  return {
                    ...b,
                    type: newType,
                    text: newType === "action" ? b.line ?? "" : undefined,
                    line: newType === "dialogue" ? b.text ?? "" : undefined,
                    parenthetical: newType === "dialogue" ? b.parenthetical : undefined,
                    char_id: newType === "dialogue" ? prev.characters[0]?.character_id : undefined,
                    char_name: newType === "dialogue" ? prev.characters[0]?.name : undefined,
                  };
                }),
              }
            : s
        ),
      };
    });
  }, []);

  const insertScene = useCallback((afterSceneNumber: number) => {
    const newScene: Scene = {
      scene_id: `s-${Date.now()}`,
      scene_number: afterSceneNumber + 1,
      slug: { location_type: "INT.", location_name: "新场景", time: "DAY" },
      characters_present: [],
      props: [],
      blocks: [],
      annotations: [],
    };
    setScript((prev) => {
      if (!prev) return prev;
      const idx = prev.scenes.findIndex((s) => s.scene_number === afterSceneNumber);
      const insertAt = idx >= 0 ? idx + 1 : prev.scenes.length;
      const newScenes = [...prev.scenes];
      newScenes.splice(insertAt, 0, newScene);
      // Renumber
      const renumbered = newScenes.map((s, i) => ({ ...s, scene_number: i + 1 }));
      return { ...prev, scenes: renumbered, metadata: { ...prev.metadata, total_scenes: renumbered.length } };
    });
    setActiveSceneId(newScene.scene_id);
  }, []);

  /** ---- Checkpoint ---- */
  const openCheckpoint = useCallback(() => {
    setCheckpointMessage("");
    setCheckpointOpen(true);
  }, []);

  const createCheckpoint = useCallback(async () => {
    if (!projectId || !script) return;
    setCheckpointSaving(true);
    try {
      const yaml = "# ScriptForge checkpoint\n" + JSON.stringify(script, null, 2);
      const res = await fetch(`/api/projects/${projectId}/versions/checkpoint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          yaml_content: yaml,
          message: checkpointMessage.trim() || "手动存档",
          tag: null,
        }),
      });
      if (!res.ok) throw new Error("Checkpoint failed");
      toast("success", "存档已保存");
      setCheckpointOpen(false);
    } catch {
      toast("error", "存档失败");
    } finally {
      setCheckpointSaving(false);
    }
  }, [projectId, script, checkpointMessage]);

  /** ---- Keyboard shortcuts ---- */
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandOpen((v) => !v);
      }
      if (e.key === "f" && e.shiftKey) {
        e.preventDefault();
        setFocusMode((v) => !v);
      }
      if (e.key === "s" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        openCheckpoint();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [openCheckpoint]);

  /** ---- Scroll to active scene ---- */
  useEffect(() => {
    if (activeSceneId && mainRef.current) {
      const el = document.getElementById(`scene-${activeSceneId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }
  }, [activeSceneId]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center gap-2 bg-page text-sm text-muted">
        <Loader2 className="h-5 w-5 animate-spin" />
        加载剧本中…
      </div>
    );
  }

  if (!script) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-page text-center">
        <FileText className="h-12 w-12 text-muted" />
        <div>
          <p className="text-base font-medium text-foreground">尚未生成剧本</p>
          <p className="mt-1 text-sm text-muted">先运行 AI 转换，生成的剧本会显示在这里。</p>
        </div>
        <button
          onClick={() => navigate(`/projects/${projectId}/convert`)}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
        >
          去转换
        </button>
      </div>
    );
  }

  return (
    <div className={cn("flex h-screen flex-col", focusMode && "bg-black")}>
      {/* Top bar */}
      {!focusMode && (
        <div className="flex items-center justify-between border-b border-border bg-surface px-4 py-2">
          <div>
            <h1 className="text-sm font-bold text-foreground">{script.metadata.title}</h1>
            <p className="text-[10px] text-muted">
              {script.metadata.total_scenes} 场景 · {script.scenes.reduce((sum, s) => sum + s.blocks.length, 0)} 块
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="rounded p-1.5 text-muted hover:bg-accent hover:text-foreground"
              onClick={() => setCommandOpen(true)}
              title="命令面板 (Cmd+K)"
            >
              <Keyboard size={16} />
            </button>
            <button
              className="rounded p-1.5 text-muted hover:bg-accent hover:text-foreground"
              onClick={() => setExportOpen(true)}
              title="导出剧本"
            >
              <Download size={16} />
            </button>
            <button
              className="rounded p-1.5 text-muted hover:bg-accent hover:text-foreground"
              onClick={() => setFocusMode((v) => !v)}
              title={focusMode ? "退出专注模式" : "专注模式 (Shift+F)"}
            >
              {focusMode ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
          </div>
        </div>
      )}

      {/* Timeline */}
      {!focusMode && (
        <SceneTimeline
          scenes={script.scenes}
          characters={script.characters}
          activeSceneId={activeSceneId}
          onSelectScene={setActiveSceneId}
          onInsertScene={insertScene}
        />
      )}

      {/* Main editor area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left nav */}
        {!focusMode && (
          <SceneNav
            scenes={script.scenes}
            characters={script.characters}
            activeSceneId={activeSceneId}
            onSelectScene={setActiveSceneId}
          />
        )}

        {/* Editor */}
        <main
          ref={mainRef}
          className={cn(
            "flex-1 overflow-y-auto px-6 py-6",
            focusMode
              ? "flex items-center justify-center bg-black"
              : "bg-page"
          )}
        >
          {script.scenes.length === 0 ? (
            <div className="flex h-full items-center justify-center text-sm text-muted">
              该剧本暂无场景。
            </div>
          ) : (
            <div className={cn("w-full", focusMode && "max-w-2xl")}>
              {script.scenes.map((scene) => (
                <div key={scene.scene_id} id={`scene-${scene.scene_id}`}>
                  <SceneContainer
                    scene={scene}
                    characters={script.characters}
                    selectedBlockId={selectedBlockId}
                    highlightedBlockId={hoveredBlockId}
                    readOnly={false}
                    onUpdateBlock={(blockId, updates) => updateBlock(scene.scene_id, blockId, updates)}
                    onAddBlock={(afterBlockId, type) => addBlock(scene.scene_id, afterBlockId, type)}
                    onDeleteBlock={(blockId) => deleteBlock(scene.scene_id, blockId)}
                    onReorderBlocks={(blockIds) => reorderBlocks(scene.scene_id, blockIds)}
                    onSelectBlock={setSelectedBlockId}
                    onToggleBlockType={(blockId) => toggleBlockType(scene.scene_id, blockId)}
                  />
                </div>
              ))}
            </div>
          )}
        </main>

        {/* Right sidebar — must live inside the flex row, otherwise it becomes a
            column sibling that steals the editor's height and leaves a blank area */}
        {!focusMode && (
          <AnnotationSidebar
            annotations={annotations}
            activeBlockId={selectedBlockId}
            onHoverAnnotation={(blockId) => setHoveredBlockId(blockId)}
            onClickAnnotation={(blockId) => {
              setSelectedBlockId(blockId);
              const scene = script.scenes.find((s) => s.blocks.some((b) => b.block_id === blockId));
              if (scene) setActiveSceneId(scene.scene_id);
            }}
            onAccept={(id) => setAnnotations((prev) => prev.map((a) => a.id === id ? { ...a, status: "accepted" as const } : a))}
            onIgnore={(id) => setAnnotations((prev) => prev.map((a) => a.id === id ? { ...a, status: "ignored" as const } : a))}
            onApplyAlternative={(id) => setAnnotations((prev) => prev.map((a) => a.id === id ? { ...a, status: "modified" as const } : a))}
          />
        )}
      </div>

      {/* Command palette */}
      <CommandPalette
        open={commandOpen}
        scenes={script.scenes.map((s) => ({
          scene_id: s.scene_id,
          scene_number: s.scene_number,
          slug: { location_name: s.slug.location_name },
        }))}
        onClose={() => setCommandOpen(false)}
        onNavigateScene={setActiveSceneId}
        onCreateCheckpoint={openCheckpoint}
        onExport={() => setExportOpen(true)}
        onToggleFocus={() => setFocusMode((v) => !v)}
      />

      {/* Export dialog */}
      <ExportDialog
        open={exportOpen}
        projectId={projectId ?? ""}
        onClose={() => setExportOpen(false)}
      />

      {/* Checkpoint modal */}
      {checkpointOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-md overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div className="flex items-center gap-2 text-sm font-bold text-foreground">
                <GitCommit size={16} />
                创建存档点
              </div>
              <button
                className="rounded p-1 text-muted hover:bg-accent hover:text-foreground"
                onClick={() => setCheckpointOpen(false)}
              >
                <X size={16} />
              </button>
            </div>
            <div className="px-4 py-3">
              <label className="mb-1.5 block text-xs text-muted">存档说明</label>
              <input
                type="text"
                value={checkpointMessage}
                onChange={(e) => setCheckpointMessage(e.target.value)}
                placeholder="例如：修改对白后存档"
                className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground outline-none focus:border-border-active"
              />
            </div>
            <div className="flex items-center justify-end gap-2 border-t border-border px-4 py-3">
              <button
                className="rounded-lg border border-border px-3 py-1.5 text-xs text-muted hover:bg-accent hover:text-foreground"
                onClick={() => setCheckpointOpen(false)}
              >
                取消
              </button>
              <button
                disabled={checkpointSaving}
                className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-1.5 text-xs font-medium text-black hover:bg-primary-hover disabled:opacity-60"
                onClick={createCheckpoint}
              >
                {checkpointSaving ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    保存中...
                  </>
                ) : (
                  "保存存档"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
