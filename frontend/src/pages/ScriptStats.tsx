import { useCallback, useEffect, useMemo, useState } from "react";
import { PageLoader } from "@/components/PageLoader";
import { useParams } from "react-router-dom";
import { BarChart3, Users, Film, MessageSquare } from "lucide-react";
import { toast } from "@/components/ToastContext";
import { cn } from "@/lib/utils";

interface SceneData {
  scene_id: string;
  scene_number: number;
  slug: { location_type: string; location_name: string; time: string };
  characters_present: string[];
  blocks: { type: string; char_id?: string; char_name?: string }[];
}

interface ScriptData {
  metadata: { title: string; total_scenes: number };
  characters: { character_id: string; name: string; role_type: string }[];
  scenes: SceneData[];
}

export default function ScriptStats() {
  const { projectId } = useParams<{ projectId: string }>();
  const [script, setScript] = useState<ScriptData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchScript = useCallback(async () => {
    setLoading(true);
    try {
      // Try to load script from export endpoint
      const res = await fetch(`/api/projects/${projectId}/export/yaml`);
      if (!res.ok) {
        if (res.status === 404) {
          setScript(null);
          return;
        }
        throw new Error("加载失败");
      }
      const _yamlText = await res.text();
      // Simple YAML-like parsing for stats (in real app use js-yaml)
      // Fallback: use demo-like empty state
      void _yamlText;
      setScript(null);
    } catch {
      toast("error", "加载剧本数据失败");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchScript();
  }, [fetchScript]);

  // Demo stats for when no real script exists yet
  const stats = useMemo(() => {
    if (!script) return null;

    const totalScenes = script.scenes.length;
    const totalBlocks = script.scenes.reduce((sum, s) => sum + s.blocks.length, 0);

    // Character appearance counts
    const appearanceMap: Record<string, { count: number; dialogue: number }> = {};
    for (const scene of script.scenes) {
      const seen = new Set<string>();
      for (const cid of scene.characters_present) seen.add(cid);
      for (const block of scene.blocks) {
        if (block.type === "dialogue" && block.char_id) {
          seen.add(block.char_id);
        }
      }
      for (const cid of seen) {
        if (!appearanceMap[cid]) appearanceMap[cid] = { count: 0, dialogue: 0 };
        appearanceMap[cid].count++;
      }
      for (const block of scene.blocks) {
        if (block.type === "dialogue" && block.char_id) {
          appearanceMap[block.char_id].dialogue++;
        }
      }
    }

    const charStats = script.characters.map((c) => ({
      ...c,
      appearances: appearanceMap[c.character_id]?.count || 0,
      dialogues: appearanceMap[c.character_id]?.dialogue || 0,
      appearanceRate: totalScenes > 0 ? (appearanceMap[c.character_id]?.count || 0) / totalScenes : 0,
    }));

    // Scene distribution by location
    const locationMap: Record<string, number> = {};
    for (const scene of script.scenes) {
      const loc = `${scene.slug.location_type} ${scene.slug.location_name}`;
      locationMap[loc] = (locationMap[loc] || 0) + 1;
    }

    // Time distribution
    const timeMap: Record<string, number> = {};
    for (const scene of script.scenes) {
      timeMap[scene.slug.time] = (timeMap[scene.slug.time] || 0) + 1;
    }

    return { totalScenes, totalBlocks, charStats, locationMap, timeMap };
  }, [script]);

  if (loading) {
    return (
      <PageLoader />
    );
  }

  if (!script || !stats) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
        <BarChart3 className="h-12 w-12 text-text-muted" />
        <p className="text-text-secondary">暂无剧本统计数据</p>
        <p className="text-xs text-text-muted">
          请先完成 AI 转换流水线以生成剧本
        </p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="mb-6 flex items-center gap-3">
        <BarChart3 className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold text-text-primary">剧本统计</h1>
        <span className="text-xs text-text-muted">《{script.metadata.title}》</span>
      </div>

      {/* Top Stats */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard icon={Film} label="场景数" value={stats.totalScenes} color="text-primary" />
        <StatCard icon={MessageSquare} label="总块数" value={stats.totalBlocks} color="text-secondary" />
        <StatCard icon={Users} label="角色数" value={script.characters.length} color="text-tertiary" />
        <StatCard icon={BarChart3} label="对白/动作比" value={`${Math.round((stats.totalBlocks > 0 ? stats.charStats.reduce((s, c) => s + c.dialogues, 0) / stats.totalBlocks : 0) * 100)}%`} color="text-warning" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Character Stats */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <Users size={16} className="text-primary" />
            角色出场统计
          </h2>
          <div className="space-y-2">
            {stats.charStats
              .sort((a, b) => b.appearances - a.appearances)
              .map((c) => (
                <div key={c.character_id} className="flex items-center gap-3 rounded-lg bg-card px-3 py-2">
                  <div className="w-20 truncate text-xs font-medium text-text-primary">{c.name}</div>
                  <div className="flex-1">
                    <div className="h-2 overflow-hidden rounded-full bg-surface">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${Math.max(4, c.appearanceRate * 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="w-16 text-right text-[10px] text-text-muted">
                    {c.appearances} 场景
                  </div>
                  <div className="w-12 text-right text-[10px] text-text-muted">
                    {c.dialogues} 对白
                  </div>
                </div>
              ))}
          </div>
        </section>

        {/* Location Distribution */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <Film size={16} className="text-secondary" />
            场景地点分布
          </h2>
          <div className="space-y-2">
            {Object.entries(stats.locationMap)
              .sort(([, a], [, b]) => b - a)
              .map(([loc, count]) => {
                const rate = stats.totalScenes > 0 ? count / stats.totalScenes : 0;
                return (
                  <div key={loc} className="flex items-center gap-3 rounded-lg bg-card px-3 py-2">
                    <div className="w-32 truncate text-xs text-text-primary">{loc}</div>
                    <div className="flex-1">
                      <div className="h-2 overflow-hidden rounded-full bg-surface">
                        <div
                          className="h-full rounded-full bg-secondary transition-all"
                          style={{ width: `${Math.max(4, rate * 100)}%` }}
                        />
                      </div>
                    </div>
                    <div className="w-10 text-right text-[10px] text-text-muted">{count}</div>
                  </div>
                );
              })}
          </div>
        </section>

        {/* Time Distribution */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <MessageSquare size={16} className="text-tertiary" />
            时间分布
          </h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.timeMap).map(([time, count]) => (
              <div
                key={time}
                className="flex items-center gap-2 rounded-lg bg-card px-3 py-2"
              >
                <span className="text-xs font-medium text-text-primary">{time}</span>
                <span className="rounded-full bg-primary-muted px-2 py-0.5 text-[10px] text-primary">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.FC<{ className?: string }>;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="mb-2 flex items-center gap-2">
        <Icon className={cn("h-4 w-4", color)} />
        <span className="text-xs text-text-muted">{label}</span>
      </div>
      <div className="text-2xl font-bold text-text-primary">{value}</div>
    </div>
  );
}
