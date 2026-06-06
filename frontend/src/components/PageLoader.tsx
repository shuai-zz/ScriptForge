import { LoadingSpinner } from "./LoadingSpinner";

interface PageLoaderProps {
  message?: string;
}

export function PageLoader({ message = "加载中..." }: PageLoaderProps) {
  return (
    <div className="flex h-full min-h-[300px] flex-col items-center justify-center gap-4">
      <LoadingSpinner size="lg" />
      <p className="text-sm text-neutral-500">{message}</p>
    </div>
  );
}
