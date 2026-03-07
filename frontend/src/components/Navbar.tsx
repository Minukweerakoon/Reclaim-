// @ts-nocheck
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Search, Sparkles } from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';

export function Navbar({ currentPage = 'chat', onNavigate, user, onSignOut, showAdminLink }) {
    const [dropdownOpen, setDropdownOpen] = useState(false);

    const displayName = user?.user_metadata?.full_name || user?.email || 'User';
    const nameParts = displayName.split(' ');
    const firstName = nameParts[0] || 'User';
    const lastInitial = nameParts[1]?.[0] ? `${nameParts[1][0]}.` : '';
    const avatarUrl = user?.user_metadata?.avatar_url ||
        `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}`;

    const scrollToSection = (sectionId) => {
        if (currentPage !== 'home') onNavigate?.('home');
        setTimeout(() => document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth' }), 100);
    };

    const openTrackingDashboard = () => {
        window.location.href = 'https://frontend.cloudixpro.cloud/dashboard';
    };

    return (
        <nav className="fixed top-0 left-0 right-0 h-16 glass-nav z-50 flex items-center justify-between px-4 md:px-8">
            {/* Logo */}
            <div className="flex items-center gap-2 group cursor-pointer" onClick={() => onNavigate?.('home')}>
                <div className="relative flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-500/10 group-hover:bg-indigo-500/20 transition-colors">
                    <Sparkles className="w-5 h-5 text-indigo-400" />
                    <div className="absolute inset-0 rounded-lg shadow-[0_0_15px_rgba(99,102,241,0.3)] opacity-50 group-hover:opacity-100 transition-opacity" />
                </div>
                <span className="text-xl font-bold text-white tracking-tight">Reclaim</span>
            </div>

            {/* Nav Items — scroll to sections, do NOT navigate to chat */}
            <div className="hidden md:flex items-center gap-8">
                {showAdminLink && (
                    <Link
                        to="/reclaim/admin"
                        className="text-sm font-medium text-amber-400 hover:text-amber-300 border-b-2 border-transparent py-5 px-1"
                    >
                        Admin
                    </Link>
                )}
                {[
                    { label: 'Find', section: 'hero-section' },
                    { label: 'Report', section: 'features-section' },
                    { label: 'Tracking', section: 'cta-section' },
                ].map(({ label, section }) => (
                    <button
                        key={label}
                        onClick={() => (label === 'Tracking' ? openTrackingDashboard() : scrollToSection(section))}
                        className={`text-sm font-medium transition-colors py-5 px-1 border-b-2 ${currentPage === 'home'
                                ? 'text-slate-400 border-transparent hover:text-white'
                                : 'text-slate-400 border-transparent hover:text-white'
                            }`}
                    >
                        {label}
                    </button>
                ))}
            </div>

            {/* Profile / Auth */}
            <div className="flex items-center gap-4">
                <button className="p-2 rounded-full hover:bg-white/5 transition-colors text-slate-400 hover:text-white md:hidden">
                    <Search className="w-5 h-5" />
                </button>
                <div className="relative flex items-center gap-3 pl-4 border-l border-white/10">
                    {user ? (
                        <>
                            <div className="text-right hidden sm:block">
                                <p className="text-xs text-slate-400">Signed in as</p>
                                <p className="text-sm font-medium text-white">{firstName} {lastInitial}</p>
                            </div>
                            <button
                                onClick={() => setDropdownOpen((o) => !o)}
                                className="w-9 h-9 rounded-full overflow-hidden border-2 border-indigo-500/30 hover:border-indigo-500/60 transition-all hover:scale-105"
                            >
                                <img src={avatarUrl} alt={displayName} className="w-full h-full object-cover" />
                            </button>
                            {dropdownOpen && (
                                <ProfileDropdown
                                    user={user}
                                    onClose={() => setDropdownOpen(false)}
                                    onSignOut={() => { setDropdownOpen(false); onSignOut?.(); }}
                                />
                            )}
                        </>
                    ) : (
                        <button
                            onClick={() => onNavigate?.('login')}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-full transition-all hover:scale-105 shadow-[0_0_12px_rgba(99,102,241,0.3)]"
                        >
                            Sign In
                        </button>
                    )}
                </div>
            </div>
        </nav>
    );
}
