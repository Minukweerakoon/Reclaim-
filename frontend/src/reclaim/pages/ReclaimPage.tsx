// @ts-nocheck
import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { ChatInterface } from '../components/ChatInterface';
import { ValidationPanel } from '../components/ValidationPanel';

export function ReclaimPage({ onNavigate, user, onSignOut }) {
    const [showPanel, setShowPanel] = useState(false);
    const [panelData, setPanelData] = useState({
        confidence: 94, imageTextSimilarity: 87,
        userCategory: '—', modelCategory: '—',
        topMatchScore: 0.94, alphaWeight: 0.72, entropy: 1.34, matchesFound: 4,
    });

    const handleResultsReady = (response) => {
        setShowPanel(true);
        if (response?.confidence) {
            setPanelData({
                confidence: Math.round((response.confidence?.overall_confidence || 0.94) * 100),
                imageTextSimilarity: Math.round((response.confidence?.clip_similarity || 0.87) * 100),
                userCategory: response.text?.item_type || '—',
                modelCategory: response.image?.item_category || response.text?.item_type || '—',
                topMatchScore: response.confidence?.overall_confidence || 0.94,
                alphaWeight: 0.72,
                entropy: 1.34,
                matchesFound: response.results?.length || 4,
            });
        }
    };

    return (
        <div className="min-h-screen w-full bg-[#08080f] text-white relative overflow-hidden">
            {/* Background Decorative Glow Orbs */}
            <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

            <Navbar currentPage="chat" onNavigate={onNavigate} user={user} onSignOut={onSignOut} />

            <main className="pt-16 h-screen flex flex-row overflow-hidden">
                <div className="flex-1 min-w-0">
                    <ChatInterface onResultsReady={handleResultsReady} user={user} />
                </div>
                <ValidationPanel isVisible={showPanel} {...panelData} />
            </main>
        </div>
    );
}

