import React, { useState } from 'react';
import { Sparkles, Shield, ArrowRight } from 'lucide-react';
import { supabase } from '../supabaseClient';

export function LoginPage({ onBack }) {
  const [loading, setLoading] = useState(false);

  const handleGoogleSignIn = async () => {
    setLoading(true);
    await supabase.auth.signInWithOAuth({
      provider: 'google',
    });
    setLoading(false);
  };

  return (
    <div className="min-h-screen w-full bg-[#08080f] flex items-center justify-center relative overflow-hidden px-4">
      {/* Aesthetic Background Glows */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

      {/* Back Button */}
      {onBack && (
        <button
          onClick={onBack}
          className="absolute top-6 left-6 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors z-20"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M10 12L6 8l4-4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Back to Home
        </button>
      )}

      <div className="relative z-10 w-full max-w-sm animate-fade-in">
        <div
          className="glass-panel rounded-3xl p-8 flex flex-col items-center text-center"
          style={{
            boxShadow:
              '0 0 60px rgba(99,102,241,0.08), 0 0 0 1px rgba(255,255,255,0.06)',
          }}
        >
          {/* Logo */}
          <div className="flex items-center gap-2.5 mb-6">
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <div className="absolute inset-0 rounded-xl shadow-[0_0_20px_rgba(99,102,241,0.3)]" />
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">
              Reclaim
            </span>
          </div>

          <h1 className="text-xl font-semibold text-white mb-2">
            Sign in to continue
          </h1>
          <p className="text-sm text-slate-400 mb-8 leading-relaxed max-w-xs">
            Find what's lost. Return what's found.
            <br />
            Sign in to start your AI-powered search.
          </p>

          {/* Google Sign In Button */}
          <button
            onClick={handleGoogleSignIn}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-5 py-3.5 bg-white hover:bg-slate-100 text-slate-800 rounded-xl font-medium text-sm transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed shadow-lg"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
                Signing in…
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path
                    d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
                    fill="#4285F4"
                  />
                  <path
                    d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
                    fill="#34A853"
                  />
                  <path
                    d="M3.964 10.71A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.042l3.007-2.332z"
                    fill="#FBBC05"
                  />
                  <path
                    d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z"
                    fill="#EA4335"
                  />
                </svg>
                Continue with Google
              </>
            )}
          </button>

          <div className="flex items-center gap-3 w-full my-5">
            <div className="flex-1 h-px bg-white/5" />
            <span className="text-[10px] text-slate-600 uppercase tracking-wider">
              or
            </span>
            <div className="flex-1 h-px bg-white/5" />
          </div>

          {/* Security Footer */}
          <div className="flex items-center gap-1.5 mt-6 text-[10px] text-slate-600">
            <Shield className="w-3 h-3" />
            <span>Your data is encrypted and never shared.</span>
          </div>
        </div>

        {/* Legal Links */}
        <p className="text-center text-[11px] text-slate-600 mt-4">
          By continuing, you agree to our{' '}
          <a href="#" className="text-slate-400 hover:text-white transition-colors">
            Terms
          </a>{' '}
          and{' '}
          <a href="#" className="text-slate-400 hover:text-white transition-colors">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  );
}