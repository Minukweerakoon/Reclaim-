/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#06b6d4',
                'primary-dim': '#0590a3',
                'neon-purple': '#8b5cf6',
                'neon-green': '#10b981',
                'alert-red': '#ef4444',
                'accent-cyan': '#06b6d4',
                'accent-amber': '#f59e0b',
                'accent-rose': '#f43f5e',
                'accent-emerald': '#10b981',
                'background-dark': '#0b1426',
                'surface-dark': '#0f172a',
                'surface-border': 'rgba(255, 255, 255, 0.12)',
            },
            fontFamily: {
                sans: ['Space Grotesk', 'system-ui', 'sans-serif'],
                display: ['Space Grotesk', 'system-ui', 'sans-serif'],
                tech: ['Orbitron', 'system-ui', 'sans-serif'],
                mono: ['JetBrains Mono', 'monospace'],
            },
            boxShadow: {
                'neon-cyan': '0 0 12px rgba(6, 182, 212, 0.4), 0 0 24px rgba(6, 182, 212, 0.2)',
                'neon-purple': '0 0 12px rgba(139, 92, 246, 0.35), 0 0 24px rgba(139, 92, 246, 0.2)',
            },
            animation: {
                'scan-vertical': 'scanVertical 3s linear infinite',
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'spin-slow': 'spin 12s linear infinite',
                'radar-sweep': 'radarSweep 4s linear infinite',
            },
            keyframes: {
                scanVertical: {
                    '0%': { top: '0%', opacity: '0' },
                    '10%': { opacity: '1' },
                    '90%': { opacity: '1' },
                    '100%': { top: '100%', opacity: '0' },
                },
                radarSweep: {
                    '0%': { transform: 'rotate(0deg)' },
                    '100%': { transform: 'rotate(360deg)' },
                },
            },
        },
    },
    plugins: [
        require('@tailwindcss/forms'),
    ],
}
