import { useCallback, useEffect, useState } from "react";
import { PageLoader } from "@/components/PageLoader";
import { useParams } from "react-router-dom";
import { BookOpen, Users, Clock, MapPin, Lightbulb } from "lucide-react";
import { toast } from "@/components/ToastContext";

interface StoryBibleData {
  id: string;
  content: Record<string, unknown>;
  created_at: string;
}

export default function StoryBiblePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [bible, setBible] = useState<StoryBibleData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchBible = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/story-bible`);
      if (!res.ok) {
        if (res.status === 404) {
          setBible(null);
          return;
        }
        throw new Error("加载失败");
      }
      setBible(await res.json());
    } catch {
      toast("error", "加载故事圣经失败");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    fetchBible();
  }, [fetchBible]);

  if (loading) {
    return (
      <PageLoader />
    );
  }

  if (!bible) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
        <BookOpen className="h-12 w-12 text-text-muted" />
        <p className="text-text-secondary">该项目暂无故事圣经</p>
        <p className="text-xs text-text-muted">
          请先完成 AI 转换流水线 Stage 0 以生成故事圣经
        </p>
      </div>
    );
  }

  const content = bible.content || {};
  const synopsis = (content.overall_synopsis as string) || "暂无概要";
  const chapterSynopses = (content.chapter_synopses as any[]) || [];
  const charNetwork = (content.character_network as any) || { nodes: [], edges: [] };
  const timeline = (content.timeline as any[]) || [];
  const themes = (content.themes as any[]) || [];
  const locations = (content.location_index as any[]) || [];

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="mb-6 flex items-center gap-3">
        <BookOpen className="h-5 w-5 text-primary" />
        <h1 className="text-lg font-semibold text-text-primary">故事圣经</h1>
      </div>

      {/* Overall Synopsis */}
      <section className="mb-6 rounded-xl border border-border bg-surface p-5">
        <h2 className="mb-3 text-sm font-bold text-text-primary">整体概要</h2>
        <p className="text-sm leading-relaxed text-text-secondary">{synopsis}</p>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Chapter Synopses */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <BookOpen size={16} className="text-secondary" />
            章节摘要 ({chapterSynopses.length})
          </h2>
          {chapterSynopses.length === 0 ? (
            <p className="text-xs text-text-muted">暂无章节摘要</p>
          ) : (
            <div className="space-y-3">
              {chapterSynopses.map((ch: any, i: number) => (
                <div key={i} className="rounded-lg bg-card p-3">
                  <div className="mb-1 text-xs font-medium text-text-primary">
                    第 {ch.chapter_number} 章
                  </div>
                  <p className="text-xs text-text-secondary">{ch.summary}</p>
                  {ch.key_events?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {ch.key_events.map((ev: any, j: number) => (
                        <span
                          key={j}
                          className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-text-muted"
                        >
                          {ev.description}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Character Network Summary */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <Users size={16} className="text-primary" />
            角色网络 ({charNetwork.nodes?.length || 0} 角色)
          </h2>
          {charNetwork.nodes?.length === 0 ? (
            <p className="text-xs text-text-muted">暂无角色数据</p>
          ) : (
            <div className="space-y-2">
              {charNetwork.nodes.map((node: any, i: number) => (
                <div key={i} className="flex items-center gap-2 rounded-lg bg-card px-3 py-2">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-muted text-xs font-bold text-primary">
                    {node.name?.[0] || "?"}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-medium text-text-primary">
                      {node.name}
                    </div>
                    <div className="text-[10px] text-text-muted">{node.role_type}</div>
                  </div>
                </div>
              ))}
              {charNetwork.edges?.length > 0 && (
                <div className="mt-2 rounded-lg bg-card p-2">
                  <div className="mb-1 text-[10px] text-text-muted">关系</div>
                  <div className="flex flex-wrap gap-1">
                    {charNetwork.edges.slice(0, 6).map((edge: any, i: number) => {
                      const src = charNetwork.nodes.find((n: any) => n.character_id === edge.source);
                      const tgt = charNetwork.nodes.find((n: any) => n.character_id === edge.target);
                      return (
                        <span
                          key={i}
                          className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-text-secondary"
                        >
                          {src?.name || "?"} → {tgt?.name || "?"} ({edge.type})
                        </span>
                      );
                    })}
                    {charNetwork.edges.length > 6 && (
                      <span className="text-[10px] text-text-muted">
                        +{charNetwork.edges.length - 6} 更多
                      </span>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* Timeline */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <Clock size={16} className="text-tertiary" />
            时间线 ({timeline.length})
          </h2>
          {timeline.length === 0 ? (
            <p className="text-xs text-text-muted">暂无时间线数据</p>
          ) : (
            <div className="relative space-y-3 pl-4">
              <div className="absolute left-1.5 top-0 bottom-0 w-px bg-border" />
              {timeline.map((ev: any, i: number) => (
                <div key={i} className="relative">
                  <div className="absolute -left-4 top-1.5 h-2 w-2 rounded-full bg-primary" />
                  <div className="rounded-lg bg-card p-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-primary">{ev.time_of_day}</span>
                      <span className="text-[10px] text-text-muted">第 {ev.chapter} 章</span>
                    </div>
                    <p className="mt-1 text-xs text-text-secondary">{ev.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Themes */}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <Lightbulb size={16} className="text-warning" />
            主题 ({themes.length})
          </h2>
          {themes.length === 0 ? (
            <p className="text-xs text-text-muted">暂无主题数据</p>
          ) : (
            <div className="space-y-3">
              {themes.map((theme: any, i: number) => (
                <div key={i} className="rounded-lg bg-card p-3">
                  <div className="mb-1 text-xs font-medium text-text-primary">{theme.name}</div>
                  <p className="text-xs text-text-secondary">{theme.description}</p>
                  {theme.visual_motifs?.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {theme.visual_motifs.map((m: string, j: number) => (
                        <span
                          key={j}
                          className="rounded bg-primary-muted px-1.5 py-0.5 text-[10px] text-primary"
                        >
                          {m}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Locations */}
      {locations.length > 0 && (
        <section className="mt-6 rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-text-primary">
            <MapPin size={16} className="text-error" />
            地点索引 ({locations.length})
          </h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {locations.map((loc: any, i: number) => (
              <div key={i} className="rounded-lg bg-card p-3">
                <div className="text-xs font-medium text-text-primary">{loc.name}</div>
                <p className="mt-1 text-[10px] text-text-muted">{loc.description}</p>
                {loc.key_props?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {loc.key_props.map((p: string, j: number) => (
                      <span
                        key={j}
                        className="rounded bg-surface px-1.5 py-0.5 text-[10px] text-text-muted"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
