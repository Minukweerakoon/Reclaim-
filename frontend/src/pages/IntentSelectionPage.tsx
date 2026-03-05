import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import { useValidationStore } from '../store/useValidationStore';

function IntentSelectionPage() {
    const navigate = useNavigate();

    return (
        <div className="min-h-[calc(100vh-160px)] flex items-center justify-center animate-fade-in">
            <div className="max-w-5xl w-full">
                {/* Header */}
                <div className="mb-10 text-center">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-4">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                        </span>
                        Phase 0
                    </div>
                    <h1 className="text-5xl md:text-6xl font-bold mb-4 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                        Select Your Mission
                    </h1>
                    <p className="text-lg text-slate-400 mt-4 max-w-2xl mx-auto leading-relaxed">
                        Choose whether you lost something or found something. The command center will
                        tailor the conversation for your case.
                    </p>
                </div>

                {/* Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* I LOST IT */}
                    <button
                        type="button"
                        onClick={() => {
                            useChatStore.getState().resetChat();
                            useValidationStore.getState().reset();
                            navigate('/chatbot?intent=lost');
                        }}
                        className="glass-panel rounded-2xl p-8 text-left transition-all duration-300 group border border-red-500/25 hover:border-red-500/55 hover:shadow-[0_0_24px_rgba(239,68,68,0.1)]"
                    >
                        <div className="text-5xl mb-5">😟</div>
                        <div className="text-2xl font-bold text-white mb-3">I LOST IT</div>
                        <p className="text-slate-400 leading-relaxed">
                            Report a missing item and walk through the guided questions.
                        </p>
                    </button>

                    {/* I FOUND IT */}
                    <button
                        type="button"
                        onClick={() => {
                            useChatStore.getState().resetChat();
                            useValidationStore.getState().reset();
                            navigate('/chatbot?intent=found');
                        }}
                        className="glass-panel rounded-2xl p-8 text-left transition-all duration-300 group border border-indigo-500/25 hover:border-indigo-500/55 hover:shadow-[0_0_24px_rgba(99,102,241,0.12)]"
                    >
                        <div className="text-5xl mb-5">😊</div>
                        <div className="text-2xl font-bold text-white mb-3">I FOUND IT</div>
                        <p className="text-slate-400 leading-relaxed">
                            Log a found item so it can be matched quickly.
                        </p>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default IntentSelectionPage;
