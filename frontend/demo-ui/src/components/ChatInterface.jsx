import React, { useEffect, useState, useRef } from 'react';
import {
  Send,
  Paperclip,
  X,
  MapPin,
  Search,
  Mic,
  Play,
  Square,
  Camera,
  Clock,
  FileText,
  Tag,
  CheckCircle2,
  SkipForward,
} from 'lucide-react';
import { ChatBubble } from './ChatBubble';
import { MatchResultCard } from './MatchResultCard';
import { processItem } from '../App';

const STEP_ORDER = [
  'GREETING',
  'ITEM_TYPE',
  'IMAGE',
  'LOCATION',
  'TIME',
  'DESCRIPTION',
  'CATEGORY',
  'LOADING',
  'RESULTS',
];

export function ChatInterface({ onResultsReady, user }) {
  const [messages, setMessages] = useState([
    {
      id: '1',
      sender: 'ai',
      text: "Hi! I'm Reclaim AI. Are you reporting a lost item, or did you find something?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [currentStep, setCurrentStep] = useState('GREETING');
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [formData, setFormData] = useState({
    status: null,
    location: '',
    time: '',
    description: '',
    category: '',
  });

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const addMessage = (text, sender, type = 'text', extra = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        sender,
        text,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        type,
        ...extra,
      },
    ]);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const triggerSearch = async () => {
    try {
      setCurrentStep('LOADING');
      setIsTyping(true);
      addMessage('Scanning database with AI…', 'ai');

      const response = await processItem({
        status: formData.status,
        file: selectedFile,
        userCategory: formData.category,
        userId: user?.id || 'guest',
        userEmail: user?.email || 'guest@test.com',
      });

      setIsTyping(false);

      if (response.results && response.results.length > 0) {
        addMessage('I found potential matches! Here they are:', 'ai');
        addMessage('', 'ai', 'results', {
          results: response.results.slice(0, 4).map((r, index) => ({
            id: r.id,
            image: r.image_url,
            title: r.category,
            confidence: Math.round(r.score * 100),
            category: r.category,
            location: 'Reported location',
            date: 'Recently',
            isBestMatch: index === 0,
          })),
        });
      } else {
        addMessage('No matches found at the moment.', 'ai');
      }

      setCurrentStep('RESULTS');
      onResultsReady?.(response);
    } catch (err) {
      console.error(err);
      addMessage('Something went wrong while processing.', 'ai');
    }
  };

  const handleSend = () => {
    if (!inputValue.trim() && !selectedFile) return;

    switch (currentStep) {
      case 'GREETING':
        setFormData((prev) => ({ ...prev, status: inputValue.includes('found') ? 'found' : 'lost' }));
        setCurrentStep('IMAGE');
        break;
      case 'LOCATION':
        setFormData((prev) => ({ ...prev, location: inputValue }));
        setCurrentStep('TIME');
        break;
      case 'TIME':
        setFormData((prev) => ({ ...prev, time: inputValue }));
        setCurrentStep('DESCRIPTION');
        break;
      case 'DESCRIPTION':
        setFormData((prev) => ({ ...prev, description: inputValue }));
        setCurrentStep('CATEGORY');
        break;
      case 'CATEGORY':
        setFormData((prev) => ({ ...prev, category: inputValue }));
        triggerSearch();
        break;
      default:
        break;
    }

    addMessage(inputValue || 'Photo attached', 'user', selectedFile ? 'image' : 'text', {
      imageUrl: previewUrl,
    });

    setInputValue('');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] max-w-2xl mx-auto relative">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg.text} sender={msg.sender} timestamp={msg.timestamp}>
            {msg.type === 'image' && msg.imageUrl && (
              <div className="mt-2 rounded-lg overflow-hidden border border-white/10">
                <img src={msg.imageUrl} alt="Uploaded" className="max-w-full h-auto max-h-48 object-cover" />
              </div>
            )}
            {msg.type === 'results' && msg.results && (
              <div className="mt-4 space-y-3 w-full">
                {msg.results.map((result) => (
                  <MatchResultCard key={result.id} {...result} />
                ))}
              </div>
            )}
          </ChatBubble>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 glass-panel border-t border-white/5 mx-4 mb-4 rounded-2xl">
        {previewUrl && (
          <div className="flex items-center gap-2 mb-3 bg-white/5 p-2 rounded-lg w-fit">
            <img src={previewUrl} alt="Preview" className="w-10 h-10 rounded object-cover" />
            <button onClick={() => { setSelectedFile(null); setPreviewUrl(null); }} className="p-1 hover:bg-white/10 rounded-full">
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        <div className="flex items-center gap-3">
          <label className="p-2.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-full transition-colors cursor-pointer">
            <Paperclip className="w-5 h-5" />
            <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
          </label>

          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Type your reply..."
            className="w-full bg-black/20 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none"
          />

          <button
            onClick={handleSend}
            className="p-3 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}