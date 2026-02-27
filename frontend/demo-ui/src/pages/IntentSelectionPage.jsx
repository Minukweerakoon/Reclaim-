import { useNavigate } from 'react-router-dom';

function IntentSelectionPage() {
    const navigate = useNavigate();

    return (
        <div className="min-h-[calc(100vh-160px)] flex items-center justify-center">
            <div className="max-w-5xl w-full animate-fade-in">
                {/* Header */}
                <div className="mb-10 text-center">
                    <div className="text-[11px] uppercase tracking-[0.4em] text-slate-500 mb-2">Phase 0</div>
                    <h1 className="text-3xl md:text-4xl font-bold text-white">Select Your Mission</h1>
                    <p className="text-sm text-slate-400 mt-3 max-w-lg mx-auto">
                        Choose whether you lost something or found something. The command center will
                        tailor the conversation for your case.
                    </p>
                </div>

                {/* Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* I LOST IT */}
                    <button
                        type="button"
                        onClick={() => navigate('/chatbot?intent=lost')}
                        className="glass-panel rounded-2xl p-8 text-left transition-all duration-300 group"
                        style={{ border: '1px solid rgba(239,68,68,0.25)' }}
                        onMouseEnter={e => {
                            e.currentTarget.style.border = '1px solid rgba(239,68,68,0.55)';
                            e.currentTarget.style.boxShadow = '0 0 24px rgba(239,68,68,0.1)';
                        }}
                        onMouseLeave={e => {
                            e.currentTarget.style.border = '1px solid rgba(239,68,68,0.25)';
                            e.currentTarget.style.boxShadow = 'none';
                        }}
                    >
                        <div className="text-4xl mb-5">😟</div>
                        <div className="text-xl font-semibold text-white mb-2">I LOST IT</div>
                        <p className="text-sm text-slate-400">
                            Report a missing item and walk through the guided questions.
                        </p>
                    </button>

                    {/* I FOUND IT */}
                    <button
                        type="button"
                        onClick={() => navigate('/chatbot?intent=found')}
                        className="glass-panel rounded-2xl p-8 text-left transition-all duration-300 group"
                        style={{ border: '1px solid rgba(99,102,241,0.25)' }}
                        onMouseEnter={e => {
                            e.currentTarget.style.border = '1px solid rgba(99,102,241,0.55)';
                            e.currentTarget.style.boxShadow = '0 0 24px rgba(99,102,241,0.12)';
                        }}
                        onMouseLeave={e => {
                            e.currentTarget.style.border = '1px solid rgba(99,102,241,0.25)';
                            e.currentTarget.style.boxShadow = 'none';
                        }}
                    >
                        <div className="text-4xl mb-5">😊</div>
                        <div className="text-xl font-semibold text-white mb-2">I FOUND IT</div>
                        <p className="text-sm text-slate-400">
                            Log a found item so it can be matched quickly.
                        </p>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default IntentSelectionPage;
