// @ts-nocheck
import { useEffect, useState } from 'react';
import { supabase } from './supabaseClient';
import { HomePage } from './pages/HomePage';
import { LoginPage } from './pages/LoginPage';
import { ReclaimPage } from './pages/ReclaimPage';

/**
 * ReclaimApp — mounts the group project's Reclaim UI inside the NCC frontend.
 *
 * Uses the shared NCC supabaseClient (same Supabase project / session).
 * Navigates internally via state — no React Router needed here.
 *
 * Flow:
 *   HomePage → "Start Chat Now" → (if not authed) LoginPage → ReclaimPage
 *                                → (if authed)    ReclaimPage
 */
export default function ReclaimApp() {
    const [user, setUser] = useState(null);
    const [currentPage, setCurrentPage] = useState<'home' | 'login' | 'chat'>('home');

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null);
        });

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);
            // After login, proceed to chat
            if (session?.user && currentPage === 'login') setCurrentPage('chat');
        });

        return () => subscription.unsubscribe();
    }, []);

    const handleNavigate = (page: 'home' | 'chat') => {
        if (page === 'chat' && !user) {
            setCurrentPage('login');
            return;
        }
        setCurrentPage(page);
    };

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        setUser(null);
        setCurrentPage('home');
    };

    if (currentPage === 'login') {
        return <LoginPage onBack={() => setCurrentPage('home')} />;
    }

    if (currentPage === 'chat') {
        return <ReclaimPage onNavigate={handleNavigate} user={user} onSignOut={handleSignOut} />;
    }

    return <HomePage onNavigate={handleNavigate} user={user} onSignOut={handleSignOut} />;
}

