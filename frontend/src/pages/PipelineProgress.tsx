import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clapperboard,
  Loader2,
  Play,
  RefreshCw,
  ScrollText,
  XCircle,
} from "lucide-react";

interface ProgressEvent {
  current_stage: string;
  percent: number;
  message: string;
  details?: Record<string, unknown>;
  run_id?: string;
  type?: "error";
}

interface RunInfo {
  id: string;
  status: string;
  stage: string;
  error_message: string | null;
  started_at: string;
}

const STAGES = [
  {
    key: "stage_0",
    label: "Stage 0",
    title: "故事圣经",
    description: "全局分析：角色、关系、时间线、主题",
    icon: BookOpen,
    color: "text-tertiary",
    bg: "bg-tertiary/15",
    border: "border-tertiary/30",
  },
  {
    key: "stage_1",
    label: "Stage 1",
    title: "逐章转换",
    description: "并行处理：场景边界、对白、动作",
    icon: ScrollText,
    color: "text-secondary",
    bg: "bg-secondary/15",
    border: "border-secondary/30",
  },
  {
    key: "stage_2",
    label: "Stage 2",
    title: "全局组装",
    description: "拼接场景、编号、一致性校验",
    icon: Clapperboard,
    color: "text-primary",
    bg: "bg-primary-muted",
    border: "border-primary/30",
  },
];

export default function PipelineProgress() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [status, setStatus] = useState<
    "idle" | "running" | "completed" | "failed" | "paused"
  >("idle");
  const [runId, setRunId] = useState<string | null>(null);
  const [latestEvent, setLatestEvent] = useState<ProgressEvent | null>(null);
  const [runs, setRuns] = useState<RunInfo[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  // Load previous runs on mount
  useEffect(() => {
    fetch(`/api/projects/${projectId}/convert/runs`)
      .then((r) => r.json())
      .then((data) => setRuns(data))
      .catch(() => {});
  }, [projectId]);

  const currentStageKey = () => {
    const stage = latestEvent?.current_stage || "";
    if (stage.startsWith("stage_0") || stage === "validate_input" || stage === "quality_gate_0")
      return "stage_0";
    if (stage.startsWith("stage_1") || stage.startsWith("stage_1_chapter"))
      return "stage_1";
    if (stage.startsWith("stage_2") || stage === "quality_gate_2" || stage === "format_output")
      return "stage_2";
    return null;
  };

  const connectStream = (url: string) => {
    if (esRef.current) {
      esRef.current.close();
    }

    setStatus("running");
    setErrorMsg(null);
    setEvents([]);

    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (e) => {
      try {
        const data: ProgressEvent = JSON.parse(e.data);
        setEvents((prev) => [...prev, data]);
        setLatestEvent(data);

        if (data.run_id && !runId) {
          setRunId(data.run_id);
        }

        if (data.current_stage === "done") {
          setStatus("completed");
          es.close();
          refreshRuns();
        } else if (data.type === "error") {
          setErrorMsg(data.message);
          setStatus("failed");
        }
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      es.close();
      setStatus((prev) => (prev === "running" ? "failed" : prev));
    };
  };

  const startConversion = () => {
    connectStream(`/api/projects/${projectId}/convert/stream`);
  };

  const resumeConversion = () => {
    if (!runId) return;
    connectStream(`/api/projects/${projectId}/convert/runs/${runId}/resume`);
  };

  const refreshRuns = () => {
    fetch(`/api/projects/${projectId}/convert/runs`)
      .then((r) => r.json())
      .then((data) => setRuns(data))
      .catch(() => {});
  };

  const stageKey = currentStageKey();

  return (
    <div className="p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/")}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-surface text-text-secondary transition-colors hover:text-text-primary"
            title="返回"
          >
            <ArrowLeft className="h-4 w-4" />
          </button>
          <div>
            <h1 className="font-display text-2xl font-semibold text-text-primary">
              AI 转换流水线
            </h1>
            <p className="mt-1 text-sm text-text-secondary">
              三阶段智能改编：圣经分析 → 逐章转换 → 全局组装
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {status === "running" ? (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-surface px-4 py-2 text-sm text-text-secondary">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              转换中…
            </div>
          ) : status === "paused" || status === "failed" ? (
            <button
              onClick={resumeConversion}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
            >
              <RefreshCw className="h-4 w-4" />
              恢复转换
            </button>
          ) : (
            <button
              onClick={startConversion}
              className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-primary-hover"
            >
              <Play className="h-4 w-4" />
              开始转换
            </button>
          )}
        </div>
      </div>

      {/* Stage Cards */}
      <div className="mb-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
        {STAGES.map((s, idx) => {
          const isActive = stageKey === s.key;
          const isPast =
            stageKey === "stage_1" && s.key === "stage_0" ||
            stageKey === "stage_2" && (s.key === "stage_0" || s.key === "stage_1");
          const isCompleted =
            status === "completed" || (isPast && status !== "idle");

          return (
            <div
              key={s.key}
              className={`relative overflow-hidden rounded-xl border bg-surface p-5 shadow-card transition-all ${
                isActive
                  ? `${s.border} shadow-card-hover`
                  : "border-border"
              }`}
            >
              {/* Active glow line */}
              {isActive && (
                <div className="absolute left-0 right-0 top-0 h-px bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
              )}

              <div className="mb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className={`flex h-8 w-8 items-center justify-center rounded-lg ${
                      isActive || isCompleted ? s.bg : "bg-card"
                    }`}
                  >
                    <s.icon
                      className={`h-4 w-4 ${
                        isActive || isCompleted ? s.color : "text-text-muted"
                      }`}
                    />
                  </div>
                  <div>
                    <p className="text-xs font-medium text-text-muted">
                      {s.label}
                    </p>
                    <p
                      className={`text-sm font-medium ${
                        isActive || isCompleted
                          ? "text-text-primary"
                          : "text-text-secondary"
                      }`}
                    >
                      {s.title}
                    </p>
                  </div>
                </div>
                {isCompleted ? (
                  <CheckCircle2 className="h-5 w-5 text-success" />
                ) : isActive ? (
                  <Loader2 className="h-5 w-5 animate-spin text-primary" />
                ) : (
                  <div className="h-5 w-5 rounded-full border-2 border-text-muted" />
                )}
              </div>

              <p className="mb-3 text-sm text-text-secondary">
                {s.description}
              </p>

              {/* Progress bar */}
              {(() => {
                const widthPct = isCompleted
                  ? 100
                  : isActive
                    ? Math.min(100, Math.max(10, (latestEvent?.percent || 0) - idx * 25))
                    : 0;
                return (
                  <div className="h-1.5 overflow-hidden rounded-full bg-card">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isCompleted
                          ? "bg-success"
                          : isActive
                            ? "bg-primary"
                            : "bg-transparent"
                      }`}
                      style={{ width: `${widthPct}%` }}
                    />
                  </div>
                );
              })()}
            </div>
          );
        })}
      </div>

      {/* Overall progress */}
      {status !== "idle" && (
        <div className="mb-6 rounded-xl border border-border bg-surface p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-medium text-text-primary">
              {latestEvent?.message || "准备中…"}
            </span>
            <span className="text-sm text-text-muted">
              {latestEvent?.percent || 0}%
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-card">
            <div
              className="h-full rounded-full bg-primary transition-all duration-300"
              style={{ width: `${latestEvent?.percent || 0}%` }}
            />
          </div>
        </div>
      )}

      {/* Error banner */}
      {errorMsg && (
        <div className="mb-6 flex items-start gap-3 rounded-lg border border-error/30 bg-error/10 p-4 text-error">
          <XCircle className="mt-0.5 h-5 w-5 shrink-0" />
          <div>
            <p className="font-medium">转换出错</p>
            <p className="mt-1 text-sm opacity-90">{errorMsg}</p>
          </div>
        </div>
      )}

      {/* Event log */}
      <div className="rounded-xl border border-border bg-surface">
        <div className="border-b border-border px-4 py-3">
          <h3 className="text-sm font-medium text-text-primary">事件日志</h3>
        </div>
        <div className="max-h-[320px] overflow-y-auto p-4">
          {events.length === 0 ? (
            <p className="text-sm text-text-muted">暂无事件</p>
          ) : (
            <div className="space-y-2">
              {events.map((ev, i) => (
                <div
                  key={i}
                  className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                    ev.type === "error"
                      ? "bg-error/10 text-error"
                      : ev.current_stage === "done"
                        ? "bg-success/10 text-success"
                        : "bg-card text-text-secondary"
                  }`}
                >
                  <span className="shrink-0 font-mono text-xs text-text-muted">
                    {ev.percent}%
                  </span>
                  <span className="shrink-0 rounded bg-surface px-1.5 py-0.5 text-xs text-text-muted">
                    {ev.current_stage}
                  </span>
                  <span className="truncate">{ev.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Run history */}
      {runs.length > 0 && (
        <div className="mt-6 rounded-xl border border-border bg-surface">
          <div className="border-b border-border px-4 py-3">
            <h3 className="text-sm font-medium text-text-primary">历史记录</h3>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {runs.slice(0, 5).map((run) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-sm"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`h-2 w-2 rounded-full ${
                        run.status === "completed"
                          ? "bg-success"
                          : run.status === "failed"
                            ? "bg-error"
                            : run.status === "paused"
                              ? "bg-warning"
                              : "bg-primary"
                      }`}
                    />
                    <span className="text-text-secondary">{run.stage}</span>
                    {run.error_message && (
                      <span className="truncate text-xs text-error">
                        {run.error_message}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-text-muted">
                    {new Date(run.started_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
