import { useState, useEffect, useCallback } from "react";
import { X } from "lucide-react";
import { getToastEventName } from "@/components/ToastContext";

type Toast = {
  id: number;
  type: "success" | "error" | "info";
  message: string;
};

let nextId = 0;

export default function ToastContainer() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler = (e: Event) => {
      const custom = e as CustomEvent<{ type: Toast["type"]; message: string }>;
      const { type, message } = custom.detail;
      const id = nextId++;
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4000);
    };
    window.addEventListener(getToastEventName(), handler);
    return () => window.removeEventListener(getToastEventName(), handler);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-center gap-3 rounded-lg px-4 py-3 shadow-dialog animate-in ${
            t.type === "success"
              ? "bg-success/10 border border-success/30 text-success"
              : t.type === "error"
                ? "bg-error/10 border border-error/30 text-error"
                : "bg-card border border-border text-text-primary"
          }`}
        >
          <span className="text-sm">{t.message}</span>
          <button
            onClick={() => removeToast(t.id)}
            className="ml-2 rounded p-0.5 opacity-60 hover:opacity-100"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
