import React, { useState } from 'react';
import { Navbar } from '../components/Navbar';
import { ChatInterface } from '../components/ChatInterface';
import { ValidationPanel } from '../components/ValidationPanel';

export function ReclaimPage({ onNavigate, user, onSignOut }) {
  // Controls the visibility of the side panel when AI results are ready
  const [showPanel, setShowPanel] = useState(false);

  return (
    <div className="min-h-screen w-full bg-[#08080f] text-white relative overflow-hidden">
      {/* Background Decorative Glow Orbs */}
      <div className="fixed top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-600/10 blur-[120px] pointer-events-none" />
      <div className="fixed bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-600/10 blur-[120px] pointer-events-none" />

      <Navbar
        currentPage="chat"
        onNavigate={onNavigate}
        user={user}
        onSignOut={onSignOut}
      />

      <main className="pt-16 h-screen flex flex-row overflow-hidden">
        {/* Chat Interface - Main Column */}
        <div className="flex-1 min-w-0">
          <ChatInterface onResultsReady={() => setShowPanel(true)} />
        </div>

        {/* Validation Panel - Sidebar 
            This appears once 'onResultsReady' is triggered from the chat.
            The values below represent the AI confidence scores for the top match.
        */}
        <ValidationPanel
          isVisible={showPanel}
          confidence={94}
          imageTextSimilarity={87}
          userCategory="Wallet"
          modelCategory="Wallet"
          topMatchScore={0.94}
          alphaWeight={0.72}
          entropy={1.34}
          matchesFound={4}
        />
      </main>
    </div>
  );
}