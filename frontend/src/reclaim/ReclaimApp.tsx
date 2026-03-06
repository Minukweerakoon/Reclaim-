// @ts-nocheck
import { useEffect, useState } from 'react';
import { useNavigate, useLocation, Routes, Route } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { HomePage } from '../pages/HomePage';
import { LoginPage } from '../pages/LoginPage';
import { AdminDashboard } from './pages/AdminDashboard';
import { isAdminUser } from '../utils/admin';

/**
 * ReclaimApp — mounts the group project's Reclaim UI inside the NCC frontend.
 *
 * Uses the shared NCC supabaseClient (same Supabase project / session).
 * Uses a lightweight internal state for Home/Login and routes to
 * the protected app flow (Intent/Chatbot pages) when users choose chat actions.
 * /reclaim/admin is only accessible when isAdminUser(user).
 */
export default function ReclaimApp() {
    const navigate = useNavigate();
    const location = useLocation();
    const [user, setUser] = useState(null);
    const [authReady, setAuthReady] = useState(false);
    const [currentPage, setCurrentPage] = useState<'home' | 'login'>('home');
    const [pendingAction, setPendingAction] = useState<'home' | 'intent' | 'lost' | 'found' | null>(null);

    const isAdminRoute = location.pathname === '/reclaim/admin' || location.pathname.startsWith('/reclaim/admin/');

    const continueToAction = (action) => {
        if (action === 'intent') {
            navigate('/');
            return;
        }
        if (action === 'lost') {
            navigate('/chatbot?intent=lost');
            return;
        }
        if (action === 'found') {
            navigate('/chatbot?intent=found');
            return;
        }
        setCurrentPage('home');
    };

    useEffect(() => {
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null);
            setAuthReady(true);
        });

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setUser(session?.user ?? null);

            // After login from /reclaim, continue based on the action that triggered auth.
            if (session?.user && currentPage === 'login') {
                continueToAction(pendingAction || 'home');
                setPendingAction(null);
            }

            if (!session?.user) {
                setPendingAction(null);
            }
        });

        return () => subscription.unsubscribe();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentPage, pendingAction]);

    // Admin route guard: wait for auth, then require logged-in admin
    useEffect(() => {
        if (!isAdminRoute || !authReady) return;
        if (!user) {
            setPendingAction(null);
            setCurrentPage('login');
            navigate('/reclaim');
            return;
        }
        if (!isAdminUser(user)) {
            navigate('/reclaim');
            return;
        }
    }, [isAdminRoute, authReady, user, navigate]);

    const handleNavigate = (action: 'home' | 'login' | 'intent' | 'lost' | 'found') => {
        if (action === 'home') {
            setCurrentPage('home');
            navigate('/reclaim');
            return;
        }

        // Explicit login from top-right button should only authenticate and return to home.
        if (action === 'login') {
            setPendingAction('home');
            setCurrentPage('login');
            return;
        }

        if (!user) {
            setPendingAction(action);
            setCurrentPage('login');
            return;
        }

        continueToAction(action);
    };

    const handleSignOut = async () => {
        await supabase.auth.signOut();
        setUser(null);
        setCurrentPage('home');
        if (isAdminRoute) navigate('/reclaim');
    };

    if (currentPage === 'login') {
        return <LoginPage onBack={() => { setCurrentPage('home'); navigate('/reclaim'); }} />;
    }

    if (isAdminRoute) {
        if (!authReady) return null; // wait for session check
        if (!user) return null;
        if (!isAdminUser(user)) return null;
        return <AdminDashboard user={user} onSignOut={handleSignOut} />;
    }

    return (
        <HomePage
            onNavigate={handleNavigate}
            user={user}
            onSignOut={handleSignOut}
            showAdminLink={user ? isAdminUser(user) : false}
        />
    );
}

