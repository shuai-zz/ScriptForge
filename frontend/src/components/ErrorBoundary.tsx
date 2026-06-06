import { Component, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div className="min-h-screen flex items-center justify-center bg-neutral-950 text-neutral-100 p-8">
          <div className="max-w-md w-full text-center space-y-6">
            <div className="text-6xl">💥</div>
            <h1 className="text-2xl font-bold font-display tracking-tight">
              出错了
            </h1>
            <p className="text-neutral-400">
              页面渲染时发生了意外错误。请刷新页面重试。
            </p>
            {this.state.error && (
              <details className="text-left bg-neutral-900 rounded-lg p-4 text-sm text-neutral-500 overflow-auto">
                <summary className="cursor-pointer font-mono">
                  {this.state.error.name}: {this.state.error.message}
                </summary>
                <pre className="mt-2 whitespace-pre-wrap">
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            <button
              onClick={() => window.location.reload()}
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-md transition-colors font-medium"
            >
              刷新页面
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
