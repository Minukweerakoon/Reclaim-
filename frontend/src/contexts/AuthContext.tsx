import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { User, Session } from '@supabase/supabase-js';
import { supabase } from '../supabaseClient';
import { useQueryClient } from '@tanstack/react-query';
import { useValidationStore } from '../store/useValidationStore';

interface AuthContextValue {
    user: User | null;
    session: Session | null;
    loading: boolean;
    phoneNumber: string;
    phoneRequired: boolean;
    signIn: (email: string, password: string) => Promise<void>;
    signUp: (email: string, password: string) => Promise<void>;
    signOutUser: () => Promise<void>;
    updatePhoneNumber: (phoneNumber: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);
    const queryClient = useQueryClient();
    const { reset: resetValidationStore } = useValidationStore();

    const getPhoneNumberFromUser = (authUser: User | null) => {
        if (!authUser) return '';
        const metadata = authUser.user_metadata || {};
        const value = metadata.phone_number || metadata.phone || '';
        return typeof value === 'string' ? value.trim() : '';
    };

    const phoneNumber = getPhoneNumberFromUser(user);
    const phoneRequired = Boolean(user) && !phoneNumber;

    useEffect(() => {
        // Restore existing session on mount
        supabase.auth.getSession().then(({ data: { session } }) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        // Listen for auth state changes (sign in, sign out, token refresh)
        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
            setSession(session);
            setUser(session?.user ?? null);
            setLoading(false);
        });

        return () => subscription.unsubscribe();
    }, []);

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            session,
            loading,
            phoneNumber,
            phoneRequired,
            signIn: async (email, password) => {
                const { error } = await supabase.auth.signInWithPassword({ email, password });
                if (error) throw error;
            },
            signUp: async (email, password) => {
                const { error } = await supabase.auth.signUp({ email, password });
                if (error) throw error;
            },
            signOutUser: async () => {
                await supabase.auth.signOut();
                queryClient.clear();
                resetValidationStore();
            },
            updatePhoneNumber: async (newPhoneNumber) => {
                const cleanPhone = String(newPhoneNumber || '').trim();
                const { data, error } = await supabase.auth.updateUser({
                    data: {
                        phone_number: cleanPhone,
                    },
                });
                if (error) throw error;
                if (data?.user) {
                    setUser(data.user);
                }
            },
        }),
        [user, session, loading, phoneNumber, phoneRequired, queryClient, resetValidationStore]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}
