import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../api/health';

interface ConnectionStatusProps {
    /** Show detailed status info */
    detailed?: boolean;
    /** Show as a compact inline indicator */
    compact?: boolean;
    /** Custom className */
    className?: string;
}

export function ConnectionStatus({ detailed = false, compact = false, className = '' }: ConnectionStatusProps) {
    const { data: health, isLoading, isError, error } = useQuery({
        queryKey: ['health'],
        queryFn: healthApi.getHealth,
        refetchInterval: 15000, // Refresh every 15s
        retry: 2,
    });

    // Helper to extract redis status from nested or flat structure
    const getRedisStatus = () => {
        if (!health) return 'unknown';
        return health.components?.redis || health.redis || 'unknown';
    };

    // Helper to extract validators from nested or flat structure
    const getValidators = () => {
        if (!health) return null;
        if (health.components?.validators) {
            // Convert 'up'/'down' to boolean for display
            const v = health.components.validators;
            return {
                image: v.image === 'up',
                text: v.text === 'up',
                voice: v.voice === 'up',
                clip: v.clip === 'up',
            };
        }
        return health.validators || null;
    };

    const getStatusColor = () => {
        if (isLoading) return 'bg-gray-500';
        if (isError || !health) return 'bg-alert-red';
        if (health.status === 'healthy') return 'bg-neon-green';
        if (health.status === 'degraded') return 'bg-accent-amber';
        return 'bg-alert-red';
    };

    const getStatusText = () => {
        if (isLoading) return 'Connecting...';
        if (isError) return 'Offline';
        if (!health) return 'Unknown';
        return health.status === 'healthy' ? 'Connected' : health.status;
    };

    if (compact) {
        return (
            <div className={`flex items-center gap-2 ${className}`}>
                <div className={`w-2 h-2 rounded-full ${getStatusColor()} ${!isLoading && !isError && health?.status === 'healthy' ? 'animate-pulse' : ''}`} />
                <span className="text-xs text-slate-400">{getStatusText()}</span>
            </div>
        );
    }

    if (!detailed) {
        return (
            <div className={`flex items-center gap-3 ${className}`}>
                <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
                <div>
                    <div className="text-sm font-semibold capitalize">{getStatusText()}</div>
                </div>
            </div>
        );
    }

    const validators = getValidators();

    return (
        <div className={`glass-panel p-4 rounded-lg ${className}`}>
            <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-sm">System Status</h4>
                <div className={`w-3 h-3 rounded-full ${getStatusColor()} animate-pulse`} />
            </div>
            
            {isError ? (
                <div className="text-alert-red text-sm">
                    <p>Unable to connect to server</p>
                    <p className="text-xs text-slate-400 mt-1">{(error as Error)?.message || 'Connection failed'}</p>
                </div>
            ) : !health ? (
                <div className="text-slate-400 text-sm">Loading...</div>
            ) : (
                <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                        <span className="text-slate-400">API</span>
                        <span className={health.status === 'healthy' ? 'text-neon-green' : 'text-alert-red'}>
                            {health.status}
                        </span>
                    </div>
                    <div className="flex justify-between">
                        <span className="text-slate-400">Redis</span>
                        <span className={getRedisStatus() === 'up' ? 'text-neon-green' : 'text-accent-amber'}>
                            {getRedisStatus()}
                        </span>
                    </div>
                    {validators && (
                        <div className="pt-2 border-t border-surface-border">
                            <div className="text-xs text-slate-500 mb-1">Validators</div>
                            <div className="grid grid-cols-2 gap-1 text-xs">
                                {Object.entries(validators).map(([key, value]) => (
                                    <div key={key} className="flex items-center gap-1">
                                        <span className={`w-1.5 h-1.5 rounded-full ${value ? 'bg-neon-green' : 'bg-alert-red'}`} />
                                        <span className="text-slate-400 capitalize">{key}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {health.uptime !== undefined && (
                        <div className="flex justify-between text-xs pt-2 border-t border-surface-border">
                            <span className="text-slate-500">Uptime</span>
                            <span className="text-slate-400">{formatUptime(health.uptime)}</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function formatUptime(seconds: number): string {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

export default ConnectionStatus;
