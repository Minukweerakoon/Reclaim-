export function ErrorMessage({
    title,
    message,
    onRetry,
    onDismiss,
    variant = 'error',
    size = 'md',
    className = '',
}) {
    const getVariantStyles = () => {
        switch (variant) {
            case 'warning':
                return {
                    bg: 'bg-accent-amber/10',
                    border: 'border-accent-amber/30',
                    icon: '⚠️',
                    titleColor: 'text-accent-amber',
                };
            case 'info':
                return {
                    bg: 'bg-primary/10',
                    border: 'border-primary/30',
                    icon: 'ℹ️',
                    titleColor: 'text-primary',
                };
            case 'error':
            default:
                return {
                    bg: 'bg-alert-red/10',
                    border: 'border-alert-red/30',
                    icon: '❌',
                    titleColor: 'text-alert-red',
                };
        }
    };

    const getSizeStyles = () => {
        switch (size) {
            case 'sm':
                return 'p-3 text-sm';
            case 'lg':
                return 'p-6 text-base';
            default:
                return 'p-4 text-sm';
        }
    };

    const styles = getVariantStyles();

    return (
        <div
            className={`${styles.bg} ${styles.border} border rounded-lg ${getSizeStyles()} ${className}`}
            role="alert"
        >
            <div className="flex items-start gap-3">
                <span className={size === 'lg' ? 'text-2xl' : 'text-lg'}>{styles.icon}</span>
                <div className="flex-1">
                    {title && (
                        <h4 className={`font-semibold ${styles.titleColor} ${size === 'sm' ? 'text-sm' : ''}`}>
                            {title}
                        </h4>
                    )}
                    <p className={`text-slate-300 ${title ? 'mt-1' : ''}`}>{message}</p>
                    
                    {(onRetry || onDismiss) && (
                        <div className="flex gap-2 mt-3">
                            {onRetry && (
                                <button
                                    onClick={onRetry}
                                    className="px-3 py-1 bg-surface-dark hover:bg-surface-border text-white rounded text-sm transition-colors"
                                >
                                    Try Again
                                </button>
                            )}
                            {onDismiss && (
                                <button
                                    onClick={onDismiss}
                                    className="px-3 py-1 text-slate-400 hover:text-white text-sm transition-colors"
                                >
                                    Dismiss
                                </button>
                            )}
                        </div>
                    )}
                </div>
                {onDismiss && !onRetry && (
                    <button
                        onClick={onDismiss}
                        className="text-slate-400 hover:text-white transition-colors"
                        aria-label="Dismiss"
                    >
                        ×
                    </button>
                )}
            </div>
        </div>
    );
}

/**
 * Format API error messages to be user-friendly
 */
export function formatErrorMessage(error) {
    if (!error) return 'An unknown error occurred';
    
    if (typeof error === 'string') return error;
    
    if (error instanceof Error) {
        // Handle common error patterns
        const message = error.message;
        
        // Network errors
        if (message.includes('Network Error') || message.includes('Failed to fetch')) {
            return 'Unable to connect to the server. Please check your connection and try again.';
        }
        
        // Timeout errors
        if (message.includes('timeout') || message.includes('ETIMEDOUT')) {
            return 'The request timed out. Please try again.';
        }
        
        // Server errors
        if (message.includes('500') || message.includes('Internal Server Error')) {
            return 'The server encountered an error. Please try again later.';
        }
        
        // Validation errors
        if (message.includes('400') || message.includes('Bad Request')) {
            return 'Invalid input. Please check your data and try again.';
        }
        
        // Auth errors
        if (message.includes('401') || message.includes('Unauthorized')) {
            return 'Authentication required. Please log in and try again.';
        }
        
        if (message.includes('403') || message.includes('Forbidden')) {
            return 'You do not have permission to perform this action.';
        }
        
        // Return original message if no pattern matches
        return message;
    }
    
    // Handle axios-style errors
    if (typeof error === 'object' && error !== null) {
        const err = error;
        if (err.response && typeof err.response === 'object') {
            const response = err.response;
            if (response.data && typeof response.data === 'object') {
                const data = response.data;
                if (typeof data.detail === 'string') return data.detail;
                if (typeof data.message === 'string') return data.message;
            }
        }
        if (typeof err.message === 'string') return err.message;
    }
    
    return 'An unexpected error occurred. Please try again.';
}

export default ErrorMessage;
