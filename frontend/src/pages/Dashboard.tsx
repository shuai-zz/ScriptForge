import { Clapperboard, Plus } from "lucide-react";

export default function Dashboard() {
  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold text-text-primary">
            ScriptForge
          </h1>
          <p className="mt-1 text-sm text-text-secondary">
            AI 辅助剧本创作工坊 — 将小说转换为结构化剧本
          </p>
        </div>
      </div>

      {/* Projects Section */}
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-medium text-text-primary">📖 我的项目</h2>
      </div>

      {/* Project Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {/* Empty State Card */}
        <button className="flex min-h-[180px] flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-border bg-surface p-6 text-text-muted transition-colors hover:border-primary/30 hover:text-text-secondary">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-card">
            <Plus className="h-6 w-6" />
          </div>
          <span className="text-sm font-medium">新建项目</span>
        </button>

        {/* Placeholder cards for future projects */}
        {["长夜将明", "蝉鸣时"].map((name) => (
          <div
            key={name}
            className="group relative overflow-hidden rounded-xl border border-border bg-surface p-6 shadow-card transition-all hover:border-primary/20 hover:shadow-card-hover"
          >
            {/* Top glow line */}
            <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

            <div className="mb-4 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-muted">
                <Clapperboard className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-medium text-text-primary">《{name}》</h3>
                <p className="text-xs text-text-muted">上次编辑: 2 小时前</p>
              </div>
            </div>

            {/* Progress */}
            <div className="mb-3 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-card">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${name === "长夜将明" ? 80 : 45}%` }}
                />
              </div>
              <span className="text-xs text-text-muted">
                {name === "长夜将明" ? "18 场景" : "12 场景"}
              </span>
            </div>

            {/* Tags */}
            <div className="flex gap-2">
              <span className="rounded-full bg-card px-2.5 py-0.5 text-xs text-text-secondary">
                🎬 剧本初稿
              </span>
              <span className="rounded-full bg-card px-2.5 py-0.5 text-xs text-text-secondary">
                👤 5 角色
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
