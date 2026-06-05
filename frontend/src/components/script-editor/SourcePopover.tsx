import type { SourceRef } from "@/types/script";
import { useEffect, useRef } from "react";

interface SourcePopoverProps {
  sourceRef: SourceRef;
  onClose: () => void;
}

export default function SourcePopover({ sourceRef, onClose }: SourcePopoverProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute z-30 mt-1 w-80 rounded-lg border border-border bg-surface p-3 shadow-xl"
    >
      <div className="mb-1 text-xs text-muted">
        第{sourceRef.chapter}章 · 第{sourceRef.paragraph}段
      </div>
      <p className="rounded bg-accent/50 p-2 text-sm leading-relaxed text-foreground">
        {sourceRef.quote}
      </p>
    </div>
  );
}
