import { cn } from "@/lib/utils";
import type { Scene, ScriptCharacter } from "@/types/script";
import { Plus } from "lucide-react";

interface SceneTimelineProps {
  scenes: Scene[];
  characters: ScriptCharacter[];
  activeSceneId: string | null;
  onSelectScene: (sceneId: string) => void;
  onInsertScene: (afterSceneNumber: number) => void;
}

export default function SceneTimeline({
  scenes,
  characters,
  activeSceneId,
  onSelectScene,
  onInsertScene,
}: SceneTimelineProps) {
  const charColor = (charId: string) => {
    const idx = characters.findIndex((c) => c.character_id === charId);
    const colors = [
      "bg-red-400",
      "bg-blue-400",
      "bg-green-400",
      "bg-yellow-400",
      "bg-purple-400",
      "bg-pink-400",
      "bg-cyan-400",
      "bg-orange-400",
    ];
    return colors[idx % colors.length] ?? "bg-gray-400";
  };

  const locationEmoji = (loc: string) => {
    const map: Record<string, string> = {
      INT: "🏠",
      EXT: "🌳",
      "INT./EXT.": "🚪",
    };
    return map[loc] ?? "📍";
  };

  return (
    <div className="border-b border-border bg-surface px-4 py-3">
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {scenes.map((scene) => (
          <div key={scene.scene_id} className="flex items-center gap-1">
            <button
              className={cn(
                "flex min-w-[120px] flex-col rounded-lg border px-3 py-2 text-left transition-all",
                activeSceneId === scene.scene_id
                  ? "border-amber-gold bg-amber-gold/10"
                  : "border-border bg-page hover:border-muted"
              )}
              onClick={() => onSelectScene(scene.scene_id)}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-sm">
                  {locationEmoji(scene.slug.location_type)}
                </span>
                <span className="text-xs font-bold text-foreground">
                  #{scene.scene_number}
                </span>
              </div>
              <div className="mt-1 truncate text-[10px] text-muted">
                {scene.slug.location_name}
              </div>
              <div className="mt-1 flex gap-0.5">
                {scene.characters_present.slice(0, 4).map((cid) => (
                  <span
                    key={cid}
                    className={cn("h-1.5 w-1.5 rounded-full", charColor(cid))}
                    title={characters.find((c) => c.character_id === cid)?.name}
                  />
                ))}
                {scene.characters_present.length > 4 && (
                  <span className="text-[8px] text-muted">
                    +{scene.characters_present.length - 4}
                  </span>
                )}
              </div>
              <div className="mt-1 text-[10px] text-muted">
                ~{Math.ceil(scene.blocks.length / 3)}p
              </div>
            </button>

            <button
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-muted hover:bg-accent hover:text-foreground"
              onClick={() => onInsertScene(scene.scene_number)}
              title="插入场景"
            >
              <Plus size={12} />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
