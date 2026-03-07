// @ts-nocheck
import React, { useEffect, useRef, useState } from 'react';
import { LogOut, Phone } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { PhoneNumberModal } from './PhoneNumberModal';

export function ProfileDropdown({ user, onClose, onSignOut }) {
    const ref = useRef(null);
    const [phoneModalOpen, setPhoneModalOpen] = useState(false);
    const { phoneNumber, updatePhoneNumber } = useAuth();

    useEffect(() => {
        const handler = (e) => {
            if (ref.current && !ref.current.contains(e.target)) onClose();
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [onClose]);

    const displayName = user?.user_metadata?.full_name || user?.email || 'User';
    const avatarUrl = user?.user_metadata?.avatar_url ||
        `https://ui-avatars.com/api/?name=${encodeURIComponent(displayName)}`;

    return (
        <>
            <div ref={ref} className="absolute top-full right-0 mt-2 w-72 glass-panel rounded-2xl border border-white/8 shadow-[0_20px_60px_rgba(0,0,0,0.5)] z-50 overflow-hidden animate-fade-in">
            <div className="p-4 border-b border-white/5">
                <div className="flex items-center gap-3">
                    <img src={avatarUrl} alt={displayName} className="w-10 h-10 rounded-full object-cover border-2 border-indigo-500/30" />
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-white truncate">{displayName}</p>
                        <p className="text-xs text-slate-400 truncate">{user.email}</p>
                    </div>
                </div>
                <button
                    onClick={() => setPhoneModalOpen(true)}
                    className="mt-3 w-full flex items-center justify-between px-3 py-2 bg-white/[0.04] hover:bg-white/[0.07] border border-white/5 rounded-lg transition-colors"
                >
                    <div className="flex items-center gap-2 min-w-0">
                        <Phone className="w-3.5 h-3.5 text-indigo-300" />
                        <span className="text-xs text-slate-300">Mobile Number</span>
                    </div>
                    <span className="text-xs font-medium text-indigo-300 truncate max-w-[130px]">
                        {phoneNumber || 'Add now'}
                    </span>
                </button>
            </div>
            <div className="p-2">
                <button onClick={onSignOut} className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all">
                    <LogOut className="w-4 h-4" /> Sign out
                </button>
            </div>
            </div>

            <PhoneNumberModal
                open={phoneModalOpen}
                required={false}
                initialPhoneNumber={phoneNumber}
                onSave={updatePhoneNumber}
                onClose={() => setPhoneModalOpen(false)}
            />
        </>
    );
}

