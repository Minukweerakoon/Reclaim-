// @ts-nocheck
import React, { useEffect, useRef, useState } from 'react';
import { LogOut, Copy, CheckCircle2 } from 'lucide-react';

export function ProfileDropdown({ user, onClose, onSignOut }) {
    const ref = useRef(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const handler = (e) => {
            if (ref.current && !ref.current.contains(e.target)) onClose();
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [onClose]);

    const copyId = () => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(user.id)
                .then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); })
                .catch((err) => console.error('Failed to copy: ', err));
        }
    };

    const displayName = user?.user_metadata?.full_name || user?.email || 'User';
    const avatarUrl = user?.user_metadata?.avatar_url ||
        `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}`;

    return (
        <div ref={ref} className="absolute top-full right-0 mt-2 w-64 glass-panel rounded-2xl border border-white/8 shadow-[0_20px_60px_rgba(0,0,0,0.5)] z-50 overflow-hidden animate-fade-in">
            <div className="p-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <img src={avatarUrl} alt={displayName} className="w-10 h-10 rounded-full object-cover border-2 border-indigo-500/30" />
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-white truncate">{displayName}</p>
                        <p className="text-xs text-slate-400 truncate">{user.email}</p>
                    </div>
                </div>
                <button onClick={copyId} className="mt-3 w-full flex items-center justify-between px-2.5 py-1.5 bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 rounded-lg transition-colors group">
                    <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[9px] text-slate-500 uppercase tracking-wider flex-shrink-0">ID</span>
                        <span className="text-[11px] font-mono text-slate-400 truncate">{user.id}</span>
                    </div>
                    {copied ? <CheckCircle2 className="w-3 h-3 text-green-400 flex-shrink-0" /> : <Copy className="w-3 h-3 text-slate-600 group-hover:text-slate-400 flex-shrink-0 transition-colors" />}
                </button>
            </div>
            <div className="px-4 py-3 border-b border-white/5">
                <p className="text-[9px] text-slate-600 uppercase tracking-wider mb-2">Auto-filled in reports</p>
                <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500">user_id</span>
                        <span className="text-[10px] font-mono text-indigo-400">{user.id}</span>
                    </div>
                    <div className="flex items-center justify-between">
                        <span className="text-[10px] text-slate-500">user_email</span>
                        <span className="text-[10px] text-slate-300 truncate max-w-[130px]">{user.email}</span>
                    </div>
                </div>
            </div>
            <div className="p-2">
                <button onClick={onSignOut} className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all">
                    <LogOut className="w-4 h-4" /> Sign out
                </button>
            </div>
        </div>
    );
}

