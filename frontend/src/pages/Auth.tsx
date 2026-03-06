import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function Auth() {
    const navigate = useNavigate();
    const location = useLocation();
    const { signIn, signUp } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const redirectPath = (location.state as { from?: string })?.from || '/';

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError(null);
        setIsSubmitting(true);

        try {
            if (isRegister) {
                await signUp(email, password);
            } else {
                await signIn(email, password);
            }
            navigate(redirectPath, { replace: true });
        } catch (err: unknown) {
            const message = err instanceof Error ? err.message : 'Authentication failed. Please try again.';
            setError(message);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background-dark grid-bg flex items-center justify-center px-6">
            <div className="w-full max-w-md glass-panel-heavy rounded-2xl p-8 border border-white/10">
                <div className="flex items-center gap-3 mb-6">
                    <div className="h-10 w-10 rounded-lg bg-primary/20 border border-primary/40 flex items-center justify-center shadow-neon-cyan">
                        <span className="text-primary text-xs font-mono">NC</span>
                    </div>
                    <div>
                        <div className="text-sm uppercase tracking-[0.3em] font-tech text-white neon-text-cyan">AI Powered Lost and Found</div>
                        <div className="text-[10px] text-slate-400 uppercase tracking-widest">Secure access</div>
                    </div>
                </div>

                <h1 className="text-xl font-semibold text-white mb-2">
                    {isRegister ? 'Create your account' : 'Welcome back'}
                </h1>
                <p className="text-sm text-slate-400 mb-6">
                    {isRegister
                        ? 'Register to start validating lost or found items.'
                        : 'Sign in to continue your validation workflow.'}
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="text-[11px] uppercase tracking-widest text-slate-400">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            className="mt-2 w-full bg-slate-900/80 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                            placeholder="you@example.com"
                            required
                        />
                    </div>
                    <div>
                        <label className="text-[11px] uppercase tracking-widest text-slate-400">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            className="mt-2 w-full bg-slate-900/80 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                            placeholder="Minimum 6 characters"
                            required
                        />
                    </div>

                    {error && (
                        <div className="text-xs text-alert-red bg-alert-red/10 border border-alert-red/30 rounded-lg p-3">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="w-full bg-primary/20 text-primary border border-primary/50 hover:bg-primary/30 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-bold uppercase tracking-widest py-3 rounded-lg transition-all"
                    >
                        {isSubmitting ? 'Processing...' : isRegister ? 'Create account' : 'Sign in'}
                    </button>
                </form>

                <div className="mt-6 text-xs text-slate-400">
                    {isRegister ? 'Already have an account?' : 'Need an account?'}
                    <button
                        type="button"
                        onClick={() => setIsRegister((prev) => !prev)}
                        className="ml-2 text-primary hover:text-white transition-colors"
                    >
                        {isRegister ? 'Sign in' : 'Register'}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Auth;
