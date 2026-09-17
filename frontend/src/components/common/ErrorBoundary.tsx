import { Component, type ErrorInfo, type ReactNode } from 'react';
export default class ErrorBoundary extends Component<{
  children: ReactNode;
}, {
  failed: boolean;
}> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Aero Health render error', error, info.componentStack); }
  render() {
    if (this.state.failed)
      return <main className="crash-screen">
        <h1>Let's take a fresh breath.</h1>
        <p>This view could not be displayed. Your saved demo data has not been deleted.</p>
        <button className="button button-primary" onClick={() => window.location.reload()}>Reload Aero Health</button>
      </main>;
    return this.props.children;
  }
}
