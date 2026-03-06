// @ts-nocheck
import React from 'react';
import { Link } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { Search, ShieldCheck, Zap, ArrowRight, MapPin, ShieldAlert } from 'lucide-react';

const stats = [
    { label: 'Items Returned', value: '12,405' },
    { label: 'Success Rate', value: '94%' },
    { label: 'Avg. Match Time', value: '2.5 hrs' },
    { label: 'Active Users', value: '50k+' },
];

export function HomePage({ onNavigate, user, onSignOut, showAdminLink }) {
    return (
        <div className="min-h-screen w-full bg-[#08080f] text-white relative overflow-x-hidden">
            <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

            <Navbar currentPage="home" onNavigate={onNavigate} user={user} onSignOut={onSignOut} showAdminLink={showAdminLink} />

            <main className="pt-24 pb-16 px-4 md:px-8 max-w-7xl mx-auto relative z-10">
                {/* Hero */}
                <div id="hero-section" className="text-center max-w-3xl mx-auto mb-20 animate-fade-in">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-6">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                        </span>
                        AI-Powered Lost &amp; Found
                    </div>
                    <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                        Reclaim what's <br />yours with AI
                    </h1>
                    <p className="text-lg md:text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
                        The intelligent platform that connects lost items with their owners instantly using advanced image recognition and location matching.
                    </p>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        {showAdminLink && (
                            <Link
                                to="/reclaim/admin"
                                className="w-full sm:w-auto px-8 py-4 bg-amber-600/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 rounded-full font-medium transition-all hover:scale-105 flex items-center justify-center gap-2"
                            >
                                <ShieldAlert className="w-5 h-5" /> Admin Dashboard
                            </Link>
                        )}
                        <button onClick={() => onNavigate?.('lost')}
                            className="w-full sm:w-auto px-8 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-full font-medium transition-all hover:scale-105 shadow-[0_0_20px_rgba(99,102,241,0.4)] flex items-center justify-center gap-2">
                            <Search className="w-5 h-5" /> Find Lost Item
                        </button>
                        <button onClick={() => onNavigate?.('found')}
                            className="w-full sm:w-auto px-8 py-4 bg-[#1a1a2e] hover:bg-[#232338] border border-white/10 text-white rounded-full font-medium transition-all hover:scale-105 flex items-center justify-center gap-2">
                            <MapPin className="w-5 h-5 text-cyan-400" /> Report Found Item
                        </button>
                    </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-24 max-w-4xl mx-auto">
                    {stats.map((stat, i) => (
                        <div key={i} className="glass-panel p-6 rounded-2xl text-center">
                            <div className="text-2xl md:text-3xl font-bold text-white mb-1">{stat.value}</div>
                            <div className="text-xs text-slate-400 uppercase tracking-wider">{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Features */}
                <div id="features-section" className="grid md:grid-cols-3 gap-6 mb-24">
                    {[
                        { icon: <Zap className="w-6 h-6 text-indigo-400" />, bg: 'bg-indigo-500/10 group-hover:bg-indigo-500/20', border: 'hover:border-indigo-500/30', title: 'AI Image Matching', desc: 'Upload a photo and our AI instantly scans thousands of reports to find visual matches with high accuracy.' },
                        { icon: <MapPin className="w-6 h-6 text-cyan-400" />, bg: 'bg-cyan-500/10 group-hover:bg-cyan-500/20', border: 'hover:border-cyan-500/30', title: 'Smart Location Tracking', desc: 'Pinpoint exactly where items were lost or found. Our heatmap technology predicts potential match locations.' },
                        { icon: <ShieldCheck className="w-6 h-6 text-amber-400" />, bg: 'bg-amber-500/10 group-hover:bg-amber-500/20', border: 'hover:border-amber-500/30', title: 'Secure Verification', desc: 'Identity verification and secure chat ensure safe returns. Your personal details are always protected.' },
                    ].map(({ icon, bg, border, title, desc }) => (
                        <div key={title} className={`glass-panel p-8 rounded-2xl border border-white/5 ${border} transition-colors group`}>
                            <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center mb-6 transition-colors`}>{icon}</div>
                            <h3 className="text-xl font-semibold mb-3">{title}</h3>
                            <p className="text-slate-400 leading-relaxed">{desc}</p>
                        </div>
                    ))}
                </div>

                {/* CTA — Start Chat Now (ONLY this button navigates to chat) */}
                <div id="cta-section" className="glass-panel p-12 rounded-3xl text-center relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/20 blur-[80px] rounded-full pointer-events-none" />
                    <div className="relative z-10">
                        <h2 className="text-3xl md:text-4xl font-bold mb-6">Ready to find your item?</h2>
                        <p className="text-slate-400 mb-8 max-w-xl mx-auto">Don't wait. The sooner you report a lost item, the higher the chance of recovery.</p>
                        <button
                            id="start-chat-now"
                            onClick={() => onNavigate?.('intent')}
                            className="px-8 py-4 bg-white text-black hover:bg-slate-200 rounded-full font-bold transition-all hover:scale-105 inline-flex items-center gap-2"
                        >
                            Start Chat Now <ArrowRight className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </main>

            <footer className="border-t border-white/10 py-12 bg-[#08080f]">
                <div className="max-w-7xl mx-auto px-4 md:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="text-slate-500 text-sm">© 2024 Reclaim AI. All rights reserved.</div>
                    <div className="flex gap-6 text-sm text-slate-400">
                        <a href="#" className="hover:text-white transition-colors">Privacy</a>
                        <a href="#" className="hover:text-white transition-colors">Terms</a>
                        <a href="#" className="hover:text-white transition-colors">Support</a>
                    </div>
                </div>
            </footer>
        </div>
    );
}
