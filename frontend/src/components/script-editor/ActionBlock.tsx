import { useRef, useState, useCallback, useEffect } from "react";
import type { ScriptBlock, ScriptCharacter } from "@/types/script";
import { cn } from "@/lib/utils";
import SourcePopover from "./SourcePopover";

interface ActionBlockProps {
  block: ScriptBlock;
  characters: ScriptCharacter[];
  isSelected: boolean;
  readOnly?: boolean;
  onUpdate: (updates: Partial<ScriptBlock>) => void;
  onSelect: () => void;
  onEnter: () => void;
  onToggleType: () => void;
}

export default function ActionBlock({
  block,
  isSelected,
  readOnly,
  onUpdate,
  onSelect,
  onEnter,
  onToggleType,
}: ActionBlockProps) {
  const textRef = useRef<HTMLDivElement>(null);
  const [sourceOpen, setSourceOpen] = useState(false);

  // Keep the contentEditable uncontrolled while typing so the cursor is not
  // reset to the start on every parent re-render. Only sync from props when
  // this element is not the active element (e.g. external update).
  useEffect(() => {
    const el = textRef.current;
    if (!el || document.activeElement === el) return;
    el.innerText = block.text ?? "";
  }, [block.text]);

  const handleInput = useCallback(() => {
    const text = textRef.current?.innerText ?? "";
    onUpdate({ text });
  }, [onUpdate]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onEnter();
      }
      if (e.key === "Tab") {
        e.preventDefault();
        onToggleType();
      }
    },
    [onEnter, onToggleType]
  );

  return (
    <div
      className={cn(
        "group relative rounded-md border-l-4 bg-surface px-4 py-3 transition-all",
        "border-amber-gold",
        isSelected && "ring-1 ring-amber-gold/50"
      )}
      onClick={onSelect}
    >
      <div className="mb-1 flex items-center gap-2 text-xs text-muted">
        <span>🎬 动作</span>
        {block.annotation_refs.length > 0 && (
          <span className="rounded-full bg-rose-500/20 px-1.5 py-0.5 text-rose-400">
            {block.annotation_refs.length} 批注
          </span>
        )}
      </div>

      <div
        ref={textRef}
        className="min-h-[1.5em] whitespace-pre-wrap font-body text-sm leading-relaxed text-foreground outline-none"
        contentEditable={!readOnly}
        suppressContentEditableWarning
        onInput={handleInput}
        onKeyDown={handleKeyDown}
      />

      {block.source_ref && (
        <div className="mt-2">
          <button
            className="inline-flex items-center gap-1 text-xs text-muted hover:text-amber-gold"
            onClick={(e) => {
              e.stopPropagation();
              setSourceOpen((v) => !v);
            }}
          >
            💡 原文: 第{block.source_ref.chapter}章第{block.source_ref.paragraph}段
          </button>
          {sourceOpen && (
            <SourcePopover
              sourceRef={block.source_ref}
              onClose={() => setSourceOpen(false)}
            />
          )}
        </div>
      )}
    </div>
  );
}
