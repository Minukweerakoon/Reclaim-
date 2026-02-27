import { Component } from 'react';

class ErrorBoundary extends Component {
    state = {
        hasError: false,
        error: null,
    };

    static getDerivedStateFromError(error) {
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-background-dark text-white flex items-center justify-center p-6">
                    <div className="glass-panel p-8 rounded-xl max-w-lg w-full text-center border-alert-red/50">
                        <div className="text-6xl mb-6">⚠️</div>
                        <h1 className="text-2xl font-bold text-alert-red mb-4">Something went wrong</h1>
                        <p className="text-slate-300 mb-6">
                            The application encountered an unexpected error.
                            Please try refreshing the page.
                        </p>
                        {this.state.error && (
                            <div className="bg-surface-dark p-4 rounded-lg text-left mb-6 overflow-auto max-h-48">
                                <code className="text-xs font-mono text-alert-red">
                                    {this.state.error.toString()}
                                </code>
                            </div>
                        )}
                        <button
                            onClick={() => window.location.reload()}
                            className="px-6 py-3 bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors font-semibold"
                        >
                            Refresh Application
                        </button>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
