import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, Lock, Mail, User, ArrowRight } from 'lucide-react';

type AuthMode = 'login' | 'register';

export const AuthPage: React.FC = () => {
    const navigate = useNavigate();
    const [mode, setMode] = useState<AuthMode>('login');
    const [isLoading, setIsLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const { register, handleSubmit, formState: { errors } } = useForm();

    const onSubmit = async (data: any) => {
        setIsLoading(true);
        // Simulate API delay
        setTimeout(() => {
            setIsLoading(false);
            // Mock authentication success
            navigate('/validate');
        }, 1500);
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                {/* Header */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-white mb-2">
                        {mode === 'login' ? 'Welcome Back' : 'Create Account'}
                    </h1>
                    <p className="text-slate-400">
                        {mode === 'login'
                            ? 'Enter your credentials to access your reports'
                            : 'Join thousands of users finding their lost items'}
                    </p>
                </div>

                {/* Validation Card */}
                <div className="auth-card">
                    {/* Tabs */}
                    <div className="auth-tabs">
                        <button
                            className={`tab-btn ${mode === 'login' ? 'active' : ''}`}
                            onClick={() => setMode('login')}
                        >
                            Log In
                        </button>
                        <button
                            className={`tab-btn ${mode === 'register' ? 'active' : ''}`}
                            onClick={() => setMode('register')}
                        >
                            Register
                        </button>
                    </div>

                    <form onSubmit={handleSubmit(onSubmit)} className="auth-form">

                        {mode === 'register' && (
                            <div className="form-group">
                                <label>Full Name</label>
                                <div className="input-wrapper">
                                    <User className="input-icon" size={18} />
                                    <input
                                        {...register('fullName', { required: true })}
                                        type="text"
                                        placeholder="John Doe"
                                        className="form-input"
                                    />
                                </div>
                                {errors.fullName && <span className="error-text">Name is required</span>}
                            </div>
                        )}

                        <div className="form-group">
                            <label>Email Address</label>
                            <div className="input-wrapper">
                                <Mail className="input-icon" size={18} />
                                <input
                                    {...register('email', { required: true, pattern: /^\S+@\S+$/i })}
                                    type="email"
                                    placeholder="you@example.com"
                                    className="form-input"
                                />
                            </div>
                            {errors.email && <span className="error-text">Valid email is required</span>}
                        </div>

                        <div className="form-group">
                            <label>Password</label>
                            <div className="input-wrapper">
                                <Lock className="input-icon" size={18} />
                                <input
                                    {...register('password', { required: true, minLength: 6 })}
                                    type={showPassword ? "text" : "password"}
                                    placeholder="••••••••"
                                    className="form-input"
                                />
                                <button
                                    type="button"
                                    className="toggle-password"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            {errors.password && <span className="error-text">Password must be at least 6 characters</span>}
                        </div>

                        {mode === 'login' && (
                            <div className="flex justify-between items-center text-sm mb-6">
                                <label className="flex items-center gap-2 text-slate-400 cursor-pointer">
                                    <input type="checkbox" className="rounded bg-slate-800 border-slate-700" />
                                    Remember me
                                </label>
                                <a href="#" className="text-blue-400 hover:text-blue-300">Forgot password?</a>
                            </div>
                        )}

                        <button type="submit" className="submit-btn" disabled={isLoading}>
                            {isLoading ? (
                                <span className="loading-spinner"></span>
                            ) : (
                                <>
                                    {mode === 'login' ? 'Sign In' : 'Create Account'}
                                    <ArrowRight size={18} />
                                </>
                            )}
                        </button>
                    </form>
                </div>

                <p className="text-center mt-6 text-slate-500 text-sm">
                    {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
                    <button
                        onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                        className="text-blue-400 hover:text-blue-300 font-medium"
                    >
                        {mode === 'login' ? 'Sign up' : 'Log in'}
                    </button>
                </p>
            </div>

            <style>{`
                .auth-page {
                    min-height: 100vh;
                    background: #0f172a;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 2rem;
                    background-image: radial-gradient(circle at top right, rgba(79, 70, 229, 0.1), transparent 40%),
                                      radial-gradient(circle at bottom left, rgba(147, 51, 234, 0.1), transparent 40%);
                }
                .auth-container { width: 100%; max-width: 440px; }
                
                .auth-card {
                    background: rgba(30, 41, 59, 0.5);
                    backdrop-filter: blur(12px);
                    border: 1px solid rgba(255,255,255,0.05);
                    border-radius: 20px;
                    padding: 2rem;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                }
                
                .auth-tabs {
                    display: flex;
                    background: rgba(15, 23, 42, 0.6);
                    padding: 4px;
                    border-radius: 12px;
                    margin-bottom: 2rem;
                }
                .tab-btn {
                    flex: 1;
                    padding: 0.75rem;
                    border-radius: 10px;
                    font-size: 0.95rem;
                    font-weight: 500;
                    color: #94a3b8;
                    transition: all 0.2s;
                }
                .tab-btn.active {
                    background: #334155;
                    color: white;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }
                
                .form-group { margin-bottom: 1.25rem; }
                .form-group label { display: block; color: #cbd5e1; font-size: 0.9rem; margin-bottom: 0.5rem; }
                .input-wrapper {
                    position: relative;
                    display: flex;
                    align-items: center;
                }
                .input-icon {
                    position: absolute;
                    left: 1rem;
                    color: #64748b;
                    pointer-events: none;
                }
                .form-input {
                    width: 100%;
                    background: #1e293b;
                    border: 1px solid #334155;
                    color: white;
                    padding: 0.85rem 1rem 0.85rem 2.75rem;
                    border-radius: 10px;
                    font-size: 0.95rem;
                    transition: all 0.2s;
                }
                .form-input:focus {
                    outline: none;
                    border-color: #6366f1;
                    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
                }
                .toggle-password {
                    position: absolute;
                    right: 1rem;
                    color: #64748b;
                    transition: color 0.2s;
                }
                .toggle-password:hover { color: #94a3b8; }
                
                .error-text { color: #f87171; font-size: 0.8rem; margin-top: 0.25rem; display: block; }
                
                .submit-btn {
                    width: 100%;
                    background: linear-gradient(135deg, #4f46e5, #9333ea);
                    color: white;
                    padding: 0.85rem;
                    border-radius: 10px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                    transition: all 0.2s;
                    margin-top: 1rem;
                }
                .submit-btn:hover:not(:disabled) {
                    transform: translateY(-1px);
                    box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.4);
                }
                .submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }
                
                .loading-spinner {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-top-color: white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                }
                @keyframes spin { to { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};
