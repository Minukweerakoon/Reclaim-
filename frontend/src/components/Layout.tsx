import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { healthApi } from '../api/health';
import { useAuth } from '../contexts/AuthContext';
import { Sparkles } from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';

function Layout() {
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const location = useLocation();
    const navigate = useNavigate();
    const { user, signOutUser } = useAuth();

    const { data: health, isError } = useQuery({
        queryKey: ['health'],
        queryFn: healthApi.getHealth,
        refetchInterval: 30000, // Refresh every 30s
        retry: 2,
    });

    const navItems = [
        { path: '/', label: 'Intent' },
        { path: '/chatbot', label: 'Chatbot' },
        { path: '/validation', label: 'Validation Hub' },
        { path: '/monitor', label: 'Monitor' },
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

    const displayName = user?.user_metadata?.full_name || user?.email || 'User';
    const nameParts = String(displayName).split(' ');
    const firstName = nameParts[0] || 'User';
    const lastInitial = nameParts[1]?.[0] ? `${nameParts[1][0]}.` : '';
    const avatarUrl = user?.user_metadata?.avatar_url ||
        `https://ui-avatars.com/api/?name=${encodeURIComponent(String(displayName))}`;

    return (
        <div className="min-h-screen w-full bg-[#08080f] text-white relative overflow-x-hidden">
            {/* Background Glow Orbs */}
            <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

            <header className="fixed top-0 left-0 right-0 z-50 glass-panel-heavy backdrop-blur-xl border-b border-white/10">
                <div className="px-6 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2 group cursor-pointer" onClick={() => navigate('/reclaim')}>
                        <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/10 group-hover:bg-indigo-500/20 transition-colors">
                            <Sparkles className="w-5 h-5 text-indigo-400" />
                            <div className="absolute inset-0 rounded-lg shadow-[0_0_15px_rgba(99,102,241,0.3)] opacity-50 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <div>
                            <div className="text-xl font-bold text-white tracking-tight">Reclaim</div>
                            <div className="text-[10px] text-slate-400 uppercase tracking-widest">AI-Powered Lost &amp; Found</div>
                        </div>
                    </div>

                    <nav className="hidden md:flex items-center gap-2">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={`px-4 py-2 rounded-lg transition-all duration-300 flex items-center text-xs uppercase tracking-wider ${location.pathname === item.path
                                    ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/50'
                                    : 'hover:bg-white/5 text-slate-300 hover:text-white'
                                    }`}
                            >
                                <span className="font-semibold">{item.label}</span>
                            </Link>
                        ))}
                    </nav>

                    <div className="flex items-center gap-4">
                        <div className="text-right">
                            <div className="text-[10px] text-slate-400 uppercase tracking-widest">System</div>
                            <div className="text-xs font-semibold uppercase text-slate-100">
                                {getStatusText()}
                            </div>
                        </div>
                        <div className={`w-2.5 h-2.5 rounded-full ${getStatusColor()} animate-pulse`} />
                        <div className="flex items-center gap-3 pl-4 border-l border-white/10">
                            <div className="text-right hidden sm:block">
                                <p className="text-xs text-slate-400">Signed in as</p>
                                <p className="text-sm font-medium text-white">{firstName} {lastInitial}</p>
                            </div>
                            <div className="relative">
                                <button
                                    onClick={() => setDropdownOpen((o) => !o)}
                                    className="w-9 h-9 rounded-full overflow-hidden border-2 border-indigo-500/30 hover:border-indigo-500/60 transition-all"
                                >
                                    <img src={avatarUrl} alt={String(displayName)} className="w-full h-full object-cover" />
                                </button>
                                {dropdownOpen ? (
                                    <ProfileDropdown
                                        user={user}
                                        onClose={() => setDropdownOpen(false)}
                                        onSignOut={() => {
                                            setDropdownOpen(false);
                                            signOutUser();
                                        }}
                                    />
                                ) : null}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="pt-24 pb-16 px-4 md:px-8 max-w-7xl mx-auto relative z-10">
                <Outlet />
            </main>
        </div>
    );
}

export default Layout;
