// @ts-nocheck
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { ProfileDropdown } from './ProfileDropdown';
import reclaimLogo from '../assets/reclaim-logo.png';

export function Navbar({ currentPage = 'chat', onNavigate, user, onSignOut, showAdminLink }) {
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const navigate = useNavigate();

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

    const workspaceLinks = [
        { path: '/', label: 'Intent' },
        { path: '/chatbot', label: 'Chatbot' },
        { path: '/validation', label: 'Validation Hub' },
    ];

    return (
        <nav className="fixed top-0 left-0 right-0 glass-nav z-50 border-b border-white/10">
            <div className="h-16 flex items-center justify-between px-4 md:px-8">
                {/* Logo */}
                <div className="flex items-center gap-2 group cursor-pointer" onClick={() => onNavigate?.('home')}>
                    <img src={reclaimLogo} alt="Reclaim logo" className="w-8 h-8 object-contain rounded-lg" />
                    <span className="text-xl font-bold text-white tracking-tight">Reclaim</span>
                </div>

                {/* Nav Items — scroll to sections */}
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
                            className="text-sm font-medium transition-colors py-5 px-1 border-b-2 text-slate-400 border-transparent hover:text-white"
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Profile / Auth */}
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => setMobileMenuOpen((prev) => !prev)}
                        className="md:hidden w-9 h-9 rounded-lg flex items-center justify-center text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
                        aria-label="Toggle navigation menu"
                    >
                        {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
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
            </div>
            {mobileMenuOpen && (
                <div className="md:hidden border-t border-white/10 bg-[#0b1020]/95 backdrop-blur-xl px-4 py-3">
                    <div className="flex flex-col gap-2">
                        <button
                            type="button"
                            onClick={() => {
                                scrollToSection('hero-section');
                                setMobileMenuOpen(false);
                            }}
                            className="text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10"
                        >
                            Find
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                scrollToSection('features-section');
                                setMobileMenuOpen(false);
                            }}
                            className="text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10"
                        >
                            Report
                        </button>
                        <button
                            type="button"
                            onClick={() => {
                                openTrackingDashboard();
                                setMobileMenuOpen(false);
                            }}
                            className="text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10"
                        >
                            Tracking
                        </button>
                        <div className="h-px bg-white/10 my-1" />
                        {workspaceLinks.map((link) => (
                            <button
                                key={link.path}
                                type="button"
                                onClick={() => {
                                    navigate(link.path);
                                    setMobileMenuOpen(false);
                                }}
                                className="text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-300 hover:text-white hover:bg-white/10"
                            >
                                {link.label}
                            </button>
                        ))}
                        {showAdminLink && (
                            <Link
                                to="/reclaim/admin"
                                onClick={() => setMobileMenuOpen(false)}
                                className="px-3 py-2 rounded-lg text-sm font-medium text-amber-300 hover:bg-amber-500/10"
                            >
                                Admin
                            </Link>
                        )}
                    </div>
                </div>
            )}
        </nav>
    );
}
