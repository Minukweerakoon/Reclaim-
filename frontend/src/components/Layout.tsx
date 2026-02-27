import { Outlet, Link, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '../api/health';
import { useAuth } from '../contexts/AuthContext';

function Layout() {
    const location = useLocation();
    const { user, signOutUser } = useAuth();

    const { data: health, isError } = useQuery({
        queryKey: ['health'],
        queryFn: healthApi.getHealth,
        refetchInterval: 30000, // Refresh every 30s
        retry: 2,
    });

    const navItems = [
        { path: '/', label: 'Intent', icon: '🧭' },
        { path: '/chatbot', label: 'Chatbot', icon: '💬' },
        { path: '/validation', label: 'Validation Hub', icon: '🎯' },
        { path: '/monitor', label: 'Monitor', icon: '📊' },
    ];

    const getStatusColor = () => {
        if (isError || !health) return 'bg-gray-500';
        if (health.status === 'healthy') return 'bg-neon-green';
        if (health.status === 'degraded') return 'bg-accent-amber';
        return 'bg-alert-red';
    };

    const getStatusText = () => {
        if (isError) return 'Offline';
        if (!health) return 'Connecting...';
        return health.status || 'Unknown';
    };

    return (
        <div className="min-h-screen bg-background-dark text-slate-100 grid-bg">
            <header className="sticky top-0 z-50 glass-panel-heavy border-b border-white/10">
                <div className="px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="h-9 w-9 rounded-lg bg-indigo-500/20 border border-indigo-500/40 flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.3)]">
                            <span className="text-indigo-400 text-lg">✦</span>
                        </div>
                        <div>
                            <div className="text-sm font-bold tracking-tight text-white">
                                Reclaim
                            </div>
                            <div className="text-[10px] text-slate-400 uppercase tracking-widest">
                                AI-Powered Lost &amp; Found
                            </div>
                        </div>
                    </div>

                    <nav className="hidden md:flex items-center gap-2">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-4 py-2 rounded-lg transition-all duration-300 flex items-center gap-2 text-xs uppercase tracking-wider ${location.pathname === item.path
                                    ? 'bg-primary/20 text-primary border border-primary/50'
                                    : 'hover:bg-white/5 text-slate-300 hover:text-white'
                                    }`}
                            >
                                <span>{item.icon}</span>
                                <span className="font-semibold">{item.label}</span>
                            </Link>
                        ))}
                    </nav>

                    <div className="flex items-center gap-6">
                        <div className="text-right">
                            <div className="text-[10px] text-slate-400 uppercase tracking-widest">System</div>
                            <div className="text-xs font-semibold uppercase text-slate-100">
                                {getStatusText()}
                            </div>
                        </div>
                        <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor()} animate-pulse`} />
                        <div className="hidden lg:flex items-center gap-3 border-l border-white/10 pl-4">
                            <div className="text-right">
                                <div className="text-[10px] text-slate-400 uppercase tracking-widest">Operator</div>
                                <div className="text-xs text-slate-200">
                                    {user?.email || 'Authenticated'}
                                </div>
                            </div>
                            <button
                                onClick={() => signOutUser()}
                                className="text-[10px] uppercase tracking-widest text-primary border border-primary/40 px-3 py-2 rounded-lg hover:bg-primary/20 transition-colors"
                            >
                                Sign out
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            <main className="px-6 py-6">
                <Outlet />
            </main>
        </div>
    );
}

export default Layout;
