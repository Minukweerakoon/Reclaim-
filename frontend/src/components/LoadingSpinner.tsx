interface LoadingSpinnerProps {
    /** Size of the spinner */
    size?: 'sm' | 'md' | 'lg' | 'xl';
    /** Optional label to show */
    label?: string;
    /** Center the spinner in its container */
    center?: boolean;
    /** Additional className */
    className?: string;
}

export function LoadingSpinner({ size = 'md', label, center = false, className = '' }: LoadingSpinnerProps) {
    const getSizeClasses = () => {
        switch (size) {
            case 'sm':
                return 'w-4 h-4 border-2';
            case 'lg':
                return 'w-10 h-10 border-3';
            case 'xl':
                return 'w-16 h-16 border-4';
            default:
                return 'w-6 h-6 border-2';
        }
    };

    const getLabelSize = () => {
        switch (size) {
            case 'sm':
                return 'text-xs';
            case 'lg':
            case 'xl':
                return 'text-base';
            default:
                return 'text-sm';
        }
    };

    const spinner = (
        <div className={`flex flex-col items-center gap-2 ${className}`}>
            <div
                className={`${getSizeClasses()} border-surface-border border-t-primary rounded-full animate-spin`}
            />
            {label && <span className={`${getLabelSize()} text-slate-400`}>{label}</span>}
        </div>
    );

    if (center) {
        return (
            <div className="flex items-center justify-center w-full h-full min-h-[100px]">
                {spinner}
            </div>
        );
    }

    return spinner;
}

interface LoadingOverlayProps {
    /** Whether the overlay is visible */
    isLoading: boolean;
    /** Optional message */
    message?: string;
    /** Progress percentage (0-100) */
    progress?: number;
    /** Progress stage message */
    progressMessage?: string;
}

export function LoadingOverlay({ isLoading, message, progress, progressMessage }: LoadingOverlayProps) {
    if (!isLoading) return null;

    return (
        <div className="fixed inset-0 bg-background-dark/80 backdrop-blur-sm z-50 flex items-center justify-center">
            <div className="glass-panel p-8 rounded-xl text-center max-w-sm">
                <LoadingSpinner size="xl" className="mb-4 mx-auto" />
                {message && <p className="text-lg font-semibold text-white mb-2">{message}</p>}
                
                {progress !== undefined && (
                    <div className="mt-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-slate-400">Progress</span>
                            <span className="text-sm text-primary font-semibold">{Math.round(progress)}%</span>
                        </div>
                        <div className="w-full bg-surface-dark rounded-full h-2 overflow-hidden">
                            <div
                                className="bg-gradient-to-r from-primary to-neon-purple h-full transition-all duration-300"
                                style={{ width: `${progress}%` }}
                            />
                        </div>
                        {progressMessage && (
                            <p className="text-xs text-slate-400 mt-2">{progressMessage}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export default LoadingSpinner;
