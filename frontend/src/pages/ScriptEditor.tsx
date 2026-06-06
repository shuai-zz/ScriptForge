import { useState, useCallback, useEffect, useRef } from "react";
import { useParams } from "react-router-dom";
import type { ScriptV1, ScriptBlock, Scene } from "@/types/script";
import SceneTimeline from "@/components/script-editor/SceneTimeline";
import SceneNav from "@/components/script-editor/SceneNav";
import SceneContainer from "@/components/script-editor/SceneContainer";
import CommandPalette from "@/components/script-editor/CommandPalette";
import AnnotationSidebar from "@/components/script-editor/AnnotationSidebar";
import ExportDialog from "@/components/script-editor/ExportDialog";
import { toast } from "@/components/ToastContext";
import { cn } from "@/lib/utils";
import { Keyboard, Maximize2, Minimize2, Download, X, Loader2, GitCommit } from "lucide-react";

/** Demo script for preview (Phase 7 placeholder data) */
function makeDemoScript(): ScriptV1 {
  const charIds = { wang: "c1", ding: "c2", shi: "c3" };
  return {
    schema_version: "1.0",
    schema_name: "scriptforge-script",
    metadata: {
      title: "三体",
      subtitle: "第一部：地球往事",
      source_novel: "三体",
      source_author: "刘慈欣",
      schema_version: "1.0",
      total_scenes: 3,
      estimated_runtime: 120,
    },
    characters: [
      {
        character_id: charIds.wang,
        name: "汪淼",
        aliases: ["淼淼"],
        role_type: "protagonist",
        age: 40,
        gender: "男",
        archetype: "科学家",
        traits: ["理性", "好奇", "坚韧"],
        arc_summary: "从怀疑到觉醒的科学家",
      },
      {
        character_id: charIds.ding,
        name: "丁仪",
        aliases: [],
        role_type: "supporting",
        age: 35,
        gender: "男",
        archetype: "物理学家",
        traits: ["玩世不恭", "天才", "悲观"],
        arc_summary: "揭示真相的物理学家",
      },
      {
        character_id: charIds.shi,
        name: "史强",
        aliases: ["大史"],
        role_type: "supporting",
        age: 45,
        gender: "男",
        archetype: "刑警",
        traits: ["粗犷", "直觉敏锐", "忠诚"],
        arc_summary: "保护科学家的刑警",
      },
    ],
    scenes: [
      {
        scene_id: "s1",
        scene_number: 1,
        slug: { location_type: "INT.", location_name: "汪淼家 - 客厅", time: "NIGHT" },
        summary: "汪淼发现照片上的倒计时",
        characters_present: [charIds.wang],
        props: ["相机", "照片"],
        blocks: [
          {
            block_id: "b1",
            order: 0,
            type: "action",
            text: "汪淼坐在沙发上，手里拿着一叠照片。台灯的光线下，他的脸色苍白。",
            annotation_refs: [],
            source_ref: { chapter: 1, paragraph: 3, quote: "汪淼觉得，在他的后半生中，他再也没有力气去爱了。" },
          },
          {
            block_id: "b2",
            order: 1,
            type: "dialogue",
            char_id: charIds.wang,
            char_name: "汪淼",
            line: "这不可能...每一张照片上都有数字。",
            parenthetical: "（颤抖着声音）",
            annotation_refs: [],
            source_ref: { chapter: 1, paragraph: 5, quote: "照片上的数字让他感到恐惧。" },
          },
        ],
        annotations: [],
      },
      {
        scene_id: "s2",
        scene_number: 2,
        slug: { location_type: "EXT.", location_name: "台球厅", time: "DAY" },
        summary: "丁仪用台球比喻解释物理定律的崩溃",
        characters_present: [charIds.wang, charIds.ding],
        props: ["台球", "球杆"],
        blocks: [
          {
            block_id: "b3",
            order: 0,
            type: "action",
            text: "台球厅里烟雾缭绕。丁仪拿起一支球杆，对准白球。",
            annotation_refs: [],
            source_ref: { chapter: 2, paragraph: 1, quote: "丁仪把两支烟放在桌上，对汪淼说：你来打一局。" },
          },
          {
            block_id: "b4",
            order: 1,
            type: "dialogue",
            char_id: charIds.ding,
            char_name: "丁仪",
            line: "想象一下，如果物理定律在不同的地方、不同的时间是不一样的，会怎样？",
            parenthetical: "（吐出一口烟）",
            annotation_refs: [],
          },
          {
            block_id: "b5",
            order: 2,
            type: "dialogue",
            char_id: charIds.wang,
            char_name: "汪淼",
            line: "那科学就不存在了。",
            annotation_refs: ["a1"],
          },
        ],
        annotations: [],
      },
      {
        scene_id: "s3",
        scene_number: 3,
        slug: { location_type: "INT.", location_name: "作战中心", time: "NIGHT" },
        summary: "史强展示射手和农场主假说",
        characters_present: [charIds.wang, charIds.shi],
        props: ["白板", "马克笔"],
        blocks: [
          {
            block_id: "b6",
            order: 0,
            type: "action",
            text: "史强在白板上画了一个靶子，上面均匀地分布着弹孔。",
            annotation_refs: [],
            source_ref: { chapter: 3, paragraph: 1, quote: "射手假说：有一名神枪手，在一个靶子上每隔十厘米打一个洞。" },
          },
          {
            block_id: "b7",
            order: 1,
            type: "dialogue",
            char_id: charIds.shi,
            char_name: "史强",
            line: "靶子上的生物科学家会总结出一个伟大的定律：每隔十厘米，就有一个洞。",
            parenthetical: "（咧嘴笑）",
            annotation_refs: [],
          },
          {
            block_id: "b8",
            order: 2,
            type: "action",
            text: "汪淼盯着白板，感到一阵眩晕。",
            annotation_refs: [],
          },
        ],
        annotations: [],
      },
    ],
    scene_index: [
      { scene_id: "s1", scene_number: 1, slug_line: "INT. 汪淼家 - 客厅 - NIGHT", characters: [charIds.wang], page_estimate: 1.5 },
      { scene_id: "s2", scene_number: 2, slug_line: "EXT. 台球厅 - DAY", characters: [charIds.wang, charIds.ding], page_estimate: 2 },
      { scene_id: "s3", scene_number: 3, slug_line: "INT. 作战中心 - NIGHT", characters: [charIds.wang, charIds.shi], page_estimate: 1.8 },
    ],
    global_annotations: [],
  };
}

/** Demo annotations for preview (Phase 8) */
function makeDemoAnnotations() {
  return [
    {
      id: "a1",
      annotation_id: "ann-001",
      severity: "suggestion" as const,
      category: "inner_to_visual",
      title: "内心独白转视觉动作",
      description: "汪淼的内心恐惧可以通过视觉元素（颤抖的手、照片掉落）来呈现，而非直接叙述。",
      confidence: 0.82,
      status: "pending" as const,
      block_id: "b1",
      scene_id: "s1",
      alternatives: [
        { alternative_id: "alt1", text: "汪淼的手颤抖着，照片从指间滑落", pros: "更电影化，视觉冲击力更强", cons: "损失部分内心细腻描写" },
        { alternative_id: "alt2", text: "保持原文叙述风格", pros: "保留文学质感", cons: "电影感较弱" },
      ],
    },
    {
      id: "a2",
      annotation_id: "ann-002",
      severity: "warning" as const,
      category: "dialogue_enhancement",
      title: "对话可以更加口语化",
      description: "丁仪的台词偏学术化，可以加入更多口语化表达来体现他\"玩世不恭\"的特质。",
      confidence: 0.65,
      status: "pending" as const,
      block_id: "b4",
      scene_id: "s2",
      alternatives: [],
    },
    {
      id: "a3",
      annotation_id: "ann-003",
      severity: "info" as const,
      category: "pacing_suggestion",
      title: "场景节奏建议",
      description: "当前三个场景节奏偏慢，建议在台球厅场景增加一个视觉转折来加快节奏。",
      confidence: 0.71,
      status: "pending" as const,
      scene_id: "s2",
      alternatives: [],
    },
  ];
}

export default function ScriptEditor() {
  const { projectId } = useParams<{ projectId: string }>();

  const [script, setScript] = useState<ScriptV1>(makeDemoScript);
  const [annotations, setAnnotations] = useState<any[]>(makeDemoAnnotations);
  const [activeSceneId, setActiveSceneId] = useState<string | null>("s1");
  const [selectedBlockId, setSelectedBlockId] = useState<string | null>(null);
  const [hoveredBlockId, setHoveredBlockId] = useState<string | null>(null);
  const [focusMode, setFocusMode] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [checkpointOpen, setCheckpointOpen] = useState(false);
  const [checkpointMessage, setCheckpointMessage] = useState("");
  const [checkpointSaving, setCheckpointSaving] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  /** ---- Block operations ---- */
  const updateBlock = useCallback((sceneId: string, blockId: string, updates: Partial<ScriptBlock>) => {
    setScript((prev) => ({
      ...prev,
      scenes: prev.scenes.map((s) =>
        s.scene_id === sceneId
          ? { ...s, blocks: s.blocks.map((b) => (b.block_id === blockId ? { ...b, ...updates } : b)) }
          : s
      ),
    }));
  }, []);

  const addBlock = useCallback((sceneId: string, afterBlockId?: string, type: ScriptBlock["type"] = "action") => {
    const newBlock: ScriptBlock = {
      block_id: `b-${Date.now()}`,
      order: 0,
      type,
      text: type === "action" ? "" : undefined,
      char_id: type === "dialogue" ? script.characters[0]?.character_id : undefined,
      char_name: type === "dialogue" ? script.characters[0]?.name : undefined,
      line: type === "dialogue" ? "" : undefined,
      annotation_refs: [],
    };
    setScript((prev) => ({
      ...prev,
      scenes: prev.scenes.map((s) => {
        if (s.scene_id !== sceneId) return s;
        const idx = afterBlockId ? s.blocks.findIndex((b) => b.block_id === afterBlockId) : -1;
        const insertAt = idx >= 0 ? idx + 1 : s.blocks.length;
        const newBlocks = [...s.blocks];
        newBlocks.splice(insertAt, 0, newBlock);
        return { ...s, blocks: newBlocks.map((b, i) => ({ ...b, order: i })) };
      }),
    }));
    setSelectedBlockId(newBlock.block_id);
  }, [script.characters]);

  const deleteBlock = useCallback((sceneId: string, blockId: string) => {
    setScript((prev) => ({
      ...prev,
      scenes: prev.scenes.map((s) =>
        s.scene_id === sceneId
          ? { ...s, blocks: s.blocks.filter((b) => b.block_id !== blockId).map((b, i) => ({ ...b, order: i })) }
          : s
      ),
    }));
    setSelectedBlockId(null);
  }, []);

  const reorderBlocks = useCallback((sceneId: string, blockIds: string[]) => {
    setScript((prev) => ({
      ...prev,
      scenes: prev.scenes.map((s) => {
        if (s.scene_id !== sceneId) return s;
        const map = new Map(s.blocks.map((b) => [b.block_id, b]));
        const newBlocks = blockIds.map((id) => map.get(id)!).map((b, i) => ({ ...b, order: i }));
        return { ...s, blocks: newBlocks };
      }),
    }));
  }, []);

  const toggleBlockType = useCallback((sceneId: string, blockId: string) => {
    setScript((prev) => ({
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
    }));
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
    if (!projectId) return;
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
  }, [projectId, script, checkpointMessage, toast]);

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

      {/* Global annotations */}
      {!focusMode && (
        <div className="border-b border-border bg-amber-gold/5 px-4 py-2">
          <div className="flex items-center gap-2 text-xs text-amber-gold">
            <span className="font-bold">全局建议:</span>
            <span>当前3个场景节奏偏慢，建议在台球厅场景增加视觉转折。</span>
          </div>
        </div>
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
        projectId={projectId ?? "demo-project"}
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
