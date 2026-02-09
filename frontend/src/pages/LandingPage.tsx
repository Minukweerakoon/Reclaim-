import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Zap, Share2, Shield, ArrowRight } from 'lucide-react';

export const LandingPage: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            {/* Navbar */}
            <nav className="landing-nav">
                <div className="landing-container nav-content">
                    <div className="logo-section">
                        <span className="logo-icon">🔍</span>
                        <span className="logo-text">Lost<span className="text-highlight">Found</span>_AI</span>
                    </div>
                    <div className="nav-links">
                        <a href="#features">Features</a>
                        <a href="#about">About</a>
                        <button className="btn-primary" onClick={() => navigate('/auth')}>
                            Get Started
                        </button>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="hero-section">
                <div className="hero-background"></div>
                <div className="landing-container hero-content">
                    <h1 className="hero-title">
                        Never Lose Track <br />
                        <span className="hero-gradient-text">Again.</span>
                    </h1>
                    <p className="hero-subtitle">
                        AI-powered validation ensures your lost item reports are complete, accurate,
                        and ready for matching in seconds.
                    </p>
                    <div className="hero-actions">
                        <button className="btn-large btn-gradient" onClick={() => navigate('/auth')}>
                            Report Lost Item <ArrowRight size={20} />
                        </button>
                        <button className="btn-large btn-outline" onClick={() => navigate('/auth')}>
                            I Found Something
                        </button>
                    </div>

                    {/* Stats Bar */}
                    <div className="hero-stats">
                        <div className="stat-item">
                            <span className="stat-value">92%</span>
                            <span className="stat-label">Validation Accuracy</span>
                        </div>
                        <div className="stat-separator"></div>
                        <div className="stat-item">
                            <span className="stat-value">&lt; 3s</span>
                            <span className="stat-label">Response Time</span>
                        </div>
                        <div className="stat-separator"></div>
                        <div className="stat-item">
                            <span className="stat-value">10k+</span>
                            <span className="stat-label">Items Matched</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Features Section */}
            <section id="features" className="features-section">
                <div className="landing-container">
                    <h2 className="section-title">Why use AI Validation?</h2>
                    <div className="features-grid">
                        <div className="feature-card">
                            <div className="feature-icon-wrapper color-purple">
                                <Check size={28} />
                            </div>
                            <h3>Multimodal Validation</h3>
                            <p>Upload photos, describe in text, or record voice. Our system cross-references everything to ensure consistency.</p>
                        </div>

                        <div className="feature-card">
                            <div className="feature-icon-wrapper color-orange">
                                <Zap size={28} />
                            </div>
                            <h3>Real-Time Feedback</h3>
                            <p>Get instant AI-powered suggestions. Is your photo too blurry? Description too vague? We'll let you know immediately.</p>
                        </div>

                        <div className="feature-card">
                            <div className="feature-icon-wrapper color-blue">
                                <Share2 size={28} />
                            </div>
                            <h3>Smart Matching</h3>
                            <p>Advanced algorithms match your verified report against thousands of found items in our database in seconds.</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="landing-footer">
                <div className="landing-container footer-content">
                    <div className="footer-brand">
                        <span>© 2026 AI Lost & Found System</span>
                    </div>
                    <div className="footer-links">
                        <a href="#">Privacy Policy</a>
                        <a href="#">Terms of Service</a>
                        <a href="#">Contact Support</a>
                    </div>
                </div>
            </footer>

            {/* Inline Styles for MVP speed - normally would be in CSS */}
            <style>{`
                .landing-page {
                    min-height: 100vh;
                    background: #0f172a;
                    color: white;
                    font-family: 'Inter', sans-serif;
                    overflow-x: hidden;
                }
                .landing-container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                }
                
                /* Nav */
                .landing-nav {
                    padding: 1.5rem 0;
                    position: fixed;
                    top: 0;
                    width: 100%;
                    z-index: 50;
                    background: rgba(15, 23, 42, 0.8);
                    backdrop-filter: blur(12px);
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }
                .nav-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .logo-text { font-weight: 700; font-size: 1.25rem; letter-spacing: -0.02em; }
                .text-highlight { background: linear-gradient(135deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
                .nav-links { display: flex; gap: 2rem; align-items: center; }
                .nav-links a { color: #94a3b8; text-decoration: none; font-size: 0.95rem; transition: color 0.2s; }
                .nav-links a:hover { color: white; }
                
                /* Buttons */
                .btn-primary {
                    background: #3b82f6;
                    color: white;
                    border: none;
                    padding: 0.6rem 1.2rem;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                .btn-primary:hover { transform: translateY(-1px); background: #2563eb; }
                
                .btn-large {
                    padding: 1rem 2rem;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 1.1rem;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.75rem;
                    cursor: pointer;
                }
                .btn-gradient {
                    background: linear-gradient(135deg, #4f46e5, #9333ea);
                    color: white;
                    border: none;
                    box-shadow: 0 10px 25px rgba(79, 70, 229, 0.4);
                    transition: all 0.3s;
                }
                .btn-gradient:hover {
                     transform: translateY(-2px);
                     box-shadow: 0 15px 35px rgba(79, 70, 229, 0.5);
                }
                .btn-outline {
                    background: transparent;
                    color: white;
                    border: 1px solid rgba(255,255,255,0.2);
                    margin-left: 1rem;
                    transition: all 0.2s;
                }
                .btn-outline:hover { background: rgba(255,255,255,0.1); }
                
                /* Hero */
                .hero-section {
                    padding-top: 180px;
                    padding-bottom: 120px;
                    text-align: center;
                    position: relative;
                }
                .hero-background {
                    position: absolute;
                    top: -20%;
                    left: 50%;
                    transform: translateX(-50%);
                    width: 100%;
                    height: 1000px;
                    background: radial-gradient(circle at 50% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 50%);
                    z-index: -1;
                    pointer-events: none;
                }
                .hero-title {
                    font-size: 4.5rem;
                    line-height: 1.1;
                    font-weight: 800;
                    margin-bottom: 1.5rem;
                    letter-spacing: -0.03em;
                }
                .hero-gradient-text {
                    background: linear-gradient(135deg, #60a5fa, #a78bfa);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }
                .hero-subtitle {
                    font-size: 1.25rem;
                    color: #94a3b8;
                    max-width: 600px;
                    margin: 0 auto 3rem;
                    line-height: 1.6;
                }
                
                .hero-stats {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 2.5rem;
                    margin-top: 5rem;
                    padding: 2rem;
                    background: rgba(255,255,255,0.03);
                    border: 1px solid rgba(255,255,255,0.05);
                    border-radius: 20px;
                    display: inline-flex;
                    backdrop-filter: blur(5px);
                }
                .stat-item {
                    display: flex;
                    flex-direction: column;
                    gap: 0.25rem;
                }
                .stat-value { font-size: 2rem; font-weight: 700; color: white; }
                .stat-label { font-size: 0.85rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; }
                .stat-separator { width: 1px; height: 40px; background: rgba(255,255,255,0.1); }
                
                /* Features */
                .features-section { padding: 5rem 0; background: #0b1120; }
                .section-title { text-align: center; font-size: 2.5rem; margin-bottom: 4rem; font-weight: 700; }
                .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
                .feature-card {
                    background: rgba(30, 41, 59, 0.5);
                    padding: 2.5rem;
                    border-radius: 20px;
                    border: 1px solid rgba(255,255,255,0.05);
                    transition: transform 0.3s;
                }
                .feature-card:hover { transform: translateY(-5px); background: rgba(30, 41, 59, 0.8); }
                .feature-icon-wrapper {
                    width: 60px; height: 60px;
                    border-radius: 16px;
                    display: flex; align-items: center; justifyContent: center;
                    margin-bottom: 1.5rem;
                }
                .color-purple { background: rgba(147, 51, 234, 0.2); color: #c084fc; }
                .color-orange { background: rgba(249, 115, 22, 0.2); color: #fb923c; }
                .color-blue { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
                .feature-card h3 { font-size: 1.5rem; margin-bottom: 1rem; font-weight: 600; }
                .feature-card p { color: #94a3b8; line-height: 1.6; }
                
                /* Footer */
                .landing-footer { padding: 3rem 0; font-size: 0.9rem; color: #64748b; border-top: 1px solid rgba(255,255,255,0.05); background: #0b1120; }
                .footer-content { display: flex; justify-content: space-between; }
                .footer-links { display: flex; gap: 2rem; }
                .footer-links a { color: #64748b; text-decoration: none; }
                .footer-links a:hover { color: white; }
            `}</style>
        </div>
    );
};
