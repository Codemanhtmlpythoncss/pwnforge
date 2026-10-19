import { Component, type ReactNode } from "react";

/**
 * Catches render errors in the routed page so a single page bug shows a recovery
 * card instead of blanking the whole app. Key it by route (in App) so navigating
 * away clears the error.
 */
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    // Surfaced in the console for debugging; no external reporting.
    console.error("Page error:", error);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="max-w-lg mx-auto mt-16 card p-6 text-center">
          <div className="text-3xl mb-2" aria-hidden="true">⚠️</div>
          <div className="font-semibold mb-1">Something went wrong on this page</div>
          <div className="text-muted text-sm mb-4">
            The rest of the app still works — try reloading, or head back to the dashboard.
          </div>
          <div className="flex gap-2 justify-center">
            <button className="btn btn-primary text-sm" onClick={() => window.location.reload()}>Reload</button>
            <a className="btn text-sm" href="/">Go to dashboard</a>
          </div>
          <pre className="text-left text-xs text-muted mt-4 overflow-auto max-h-32 whitespace-pre-wrap">
            {String(this.state.error.message || this.state.error)}
          </pre>
        </div>
      );
    }
    return this.props.children;
  }
}
