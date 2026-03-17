import { createClient } from '@supabase/supabase-js';

// These are frontend-safe public keys (anon key, not service role)
const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL as string) || '';
const supabaseAnonKey = (import.meta.env.VITE_SUPABASE_ANON_KEY as string) || '';

/** True when a real Supabase project is configured (not the placeholder). Use to avoid redirecting to a broken auth URL. */
export const isSupabaseConfigured =
    !!supabaseUrl &&
    !!supabaseAnonKey &&
    !supabaseUrl.includes('placeholder') &&
    supabaseAnonKey !== 'your-anon-key-here';

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('[Supabase] Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY in environment');
} else if (!isSupabaseConfigured) {
    console.warn('[Supabase] Using placeholder URL/key. Sign-in will not work until you set real values in .env');
}

export const supabase = createClient(supabaseUrl || 'https://placeholder.supabase.co', supabaseAnonKey || 'placeholder', {
    auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
    },
});
