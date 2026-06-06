import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: EmptyStateProps) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-neutral-800 bg-neutral-900/30 py-16 text-center ${className}`}
    >
      {icon && <div className="text-4xl text-neutral-600">{icon}</div>}
      <div className="space-y-1">
        <h3 className="text-base font-medium text-neutral-300">{title}</h3>
        {description && (
          <p className="text-sm text-neutral-500 max-w-xs mx-auto">
            {description}
          </p>
        )}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
