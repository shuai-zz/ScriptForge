import { useRef, useState, useCallback, useEffect } from "react";
import type { ScriptBlock, ScriptCharacter } from "@/types/script";
import { cn } from "@/lib/utils";
import SourcePopover from "./SourcePopover";

interface DialogueBlockProps {
  block: ScriptBlock;
  characters: ScriptCharacter[];
  isSelected: boolean;
  readOnly?: boolean;
  onUpdate: (updates: Partial<ScriptBlock>) => void;
  onSelect: () => void;
  onEnter: () => void;
  onToggleType: () => void;
}

export default function DialogueBlock({
  block,
  characters,
  isSelected,
  readOnly,
  onUpdate,
  onSelect,
  onEnter,
  onToggleType,
}: DialogueBlockProps) {
  const lineRef = useRef<HTMLDivElement>(null);
  const parenRef = useRef<HTMLDivElement>(null);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [charDropdown, setCharDropdown] = useState(false);

  // Sync external prop updates without stealing focus/resetting the caret.
  useEffect(() => {
    const el = lineRef.current;
    if (!el || document.activeElement === el) return;
    el.innerText = block.line ?? "";
  }, [block.line]);

  useEffect(() => {
    const el = parenRef.current;
    if (!el || document.activeElement === el) return;
    el.innerText = block.parenthetical ?? "";
  }, [block.parenthetical]);

  const handleLineInput = useCallback(() => {
    const line = lineRef.current?.innerText ?? "";
    onUpdate({ line });
  }, [onUpdate]);

  const handleParenInput = useCallback(() => {
    const parenthetical = parenRef.current?.innerText ?? "";
    onUpdate({ parenthetical });
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
        "border-sage-green",
        isSelected && "ring-1 ring-sage-green/50"
      )}
      onClick={onSelect}
    >
      {/* Character header */}
      <div className="mb-1 flex items-center justify-between">
        <div className="relative">
          <button
            className="flex items-center gap-1 text-sm font-semibold text-foreground hover:text-sage-green"
            onClick={(e) => {
              e.stopPropagation();
              setCharDropdown((v) => !v);
            }}
          >
            {block.char_name ?? "未知角色"}
            {!readOnly && <span className="text-xs text-muted">▼</span>}
          </button>
          {charDropdown && !readOnly && (
            <div className="absolute left-0 top-full z-20 mt-1 w-40 rounded-md border border-border bg-surface shadow-lg">
              {characters.map((c) => (
                <button
                  key={c.character_id}
                  className="block w-full px-3 py-1.5 text-left text-sm hover:bg-accent"
                  onClick={(e) => {
                    e.stopPropagation();
                    onUpdate({ char_id: c.character_id, char_name: c.name });
                    setCharDropdown(false);
                  }}
                >
                  {c.name}
                </button>
              ))}
            </div>
          )}
        </div>
        {block.annotation_refs.length > 0 && (
          <span className="rounded-full bg-rose-500/20 px-1.5 py-0.5 text-xs text-rose-400">
            {block.annotation_refs.length} 批注
          </span>
        )}
      </div>

      {/* Parenthetical */}
      {block.parenthetical !== undefined && (
        <div
          ref={parenRef}
          className="mb-1 min-h-[1.2em] text-xs italic text-muted outline-none"
          contentEditable={!readOnly}
          suppressContentEditableWarning
          onInput={handleParenInput}
          onKeyDown={handleKeyDown}
        />
      )}

      {/* Dialogue line */}
      <div
        ref={lineRef}
        data-testid="dialogue-line"
        className="min-h-[1.5em] whitespace-pre-wrap font-body text-sm leading-relaxed text-foreground outline-none"
        contentEditable={!readOnly}
        suppressContentEditableWarning
        onInput={handleLineInput}
        onKeyDown={handleKeyDown}
      />

      {/* Source ref */}
      {block.source_ref && (
        <div className="mt-2">
          <button
            className="inline-flex items-center gap-1 text-xs text-muted hover:text-sage-green"
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
