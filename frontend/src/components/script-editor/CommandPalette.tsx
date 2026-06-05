import { useState, useEffect, useRef, useMemo } from "react";
import { cn } from "@/lib/utils";
import { Search, FileText, GitCommit, Download, Focus } from "lucide-react";

interface Command {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
}

interface CommandPaletteProps {
  open: boolean;
  scenes: { scene_id: string; scene_number: number; slug: { location_name: string } }[];
  onClose: () => void;
  onNavigateScene: (sceneId: string) => void;
  onCreateCheckpoint: () => void;
  onExport: () => void;
  onToggleFocus: () => void;
}

export default function CommandPalette({
  open,
  scenes,
  onClose,
  onNavigateScene,
  onCreateCheckpoint,
  onExport,
  onToggleFocus,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: Command[] = useMemo(() => {
    const base: Command[] = [
      {
        id: "focus",
        label: "进入专注模式",
        icon: <Focus size={16} />,
        shortcut: "Shift+F",
        action: () => {
          onToggleFocus();
          onClose();
        },
      },
      {
        id: "checkpoint",
        label: "创建存档点",
        icon: <GitCommit size={16} />,
        shortcut: "Cmd+S",
        action: () => {
          onCreateCheckpoint();
          onClose();
        },
      },
      {
        id: "export",
        label: "导出剧本",
        icon: <Download size={16} />,
        action: () => {
          onExport();
          onClose();
        },
      },
    ];

    const sceneCmds: Command[] = scenes.map((s) => ({
      id: `scene-${s.scene_id}`,
      label: `场景 ${s.scene_number}: ${s.slug.location_name}`,
      icon: <FileText size={16} />,
      action: () => {
        onNavigateScene(s.scene_id);
        onClose();
      },
    }));

    return [...base, ...sceneCmds];
  }, [scenes, onNavigateScene, onCreateCheckpoint, onExport, onToggleFocus, onClose]);

  const filtered = useMemo(() => {
    if (!query.trim()) return commands;
    const q = query.toLowerCase();
    return commands.filter((c) => c.label.toLowerCase().includes(q));
  }, [commands, query]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((i) => (i + 1) % filtered.length);
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((i) => (i - 1 + filtered.length) % filtered.length);
      }
      if (e.key === "Enter") {
        e.preventDefault();
        filtered[selectedIndex]?.action();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, filtered, selectedIndex, onClose]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 pt-[15vh]">
      <div className="w-full max-w-lg overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <Search size={18} className="text-muted" />
          <input
            ref={inputRef}
            className="flex-1 bg-transparent text-sm text-foreground outline-none placeholder:text-muted"
            placeholder="搜索操作或场景..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
          />
          <kbd className="rounded bg-accent px-1.5 py-0.5 text-[10px] text-muted">ESC</kbd>
        </div>
        <div className="max-h-[50vh] overflow-y-auto py-1">
          {filtered.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-muted">
              未找到匹配的操作
            </div>
          )}
          {filtered.map((cmd, i) => (
            <button
              key={cmd.id}
              className={cn(
                "flex w-full items-center gap-3 px-4 py-2 text-left transition-colors",
                i === selectedIndex ? "bg-accent text-foreground" : "text-muted hover:bg-accent/50"
              )}
              onMouseEnter={() => setSelectedIndex(i)}
              onClick={() => cmd.action()}
            >
              <span className="text-muted">{cmd.icon}</span>
              <span className="flex-1 text-sm">{cmd.label}</span>
              {cmd.shortcut && (
                <kbd className="rounded bg-page px-1.5 py-0.5 text-[10px] text-muted">
                  {cmd.shortcut}
                </kbd>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
