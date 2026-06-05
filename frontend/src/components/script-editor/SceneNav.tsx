import { cn } from "@/lib/utils";
import type { Scene, ScriptCharacter } from "@/types/script";

interface SceneNavProps {
  scenes: Scene[];
  characters: ScriptCharacter[];
  activeSceneId: string | null;
  onSelectScene: (sceneId: string) => void;
}

export default function SceneNav({
  scenes,
  characters,
  activeSceneId,
  onSelectScene,
}: SceneNavProps) {
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

  return (
    <div className="h-full w-56 overflow-y-auto border-r border-border bg-surface p-3">
      <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-muted">
        场景
      </h4>
      <div className="space-y-1">
        {scenes.map((scene) => {
          const isActive = activeSceneId === scene.scene_id;
          const slug = `${scene.slug.location_type} ${scene.slug.location_name}`;
          return (
            <button
              key={scene.scene_id}
              className={cn(
                "flex w-full flex-col rounded-md px-2 py-1.5 text-left transition-colors",
                isActive
                  ? "bg-accent text-foreground"
                  : "text-muted hover:bg-accent/50 hover:text-foreground"
              )}
              onClick={() => onSelectScene(scene.scene_id)}
            >
              <div className="flex items-center gap-1.5">
                <span className="text-[10px] font-bold">#{scene.scene_number}</span>
                <span className="truncate text-xs">{slug}</span>
              </div>
              <div className="mt-0.5 flex gap-0.5">
                {scene.characters_present.slice(0, 6).map((cid) => (
                  <span
                    key={cid}
                    className={cn("h-1.5 w-1.5 rounded-full", charColor(cid))}
                    title={characters.find((c) => c.character_id === cid)?.name}
                  />
                ))}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
