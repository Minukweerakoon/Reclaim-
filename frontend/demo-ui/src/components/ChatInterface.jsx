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
import { processItem } from '../supabaseClient';

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
        id: crypto.randomUUID ? crypto.randomUUID() : Date.now().toString() + Math.random().toString(36),
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

  const triggerSearch = async (finalFormData) => {
    try {
      setCurrentStep('LOADING');
      setIsTyping(true);

      // Only show scanning for lost items
      if (finalFormData.status === 'lost') {
        addMessage('Scanning database with AI…', 'ai');
      } else {
        addMessage('Registering found item…', 'ai');
      }

      const response = await processItem({
        status: finalFormData.status,
        file: selectedFile,
        userCategory: finalFormData.category,
        location: finalFormData.location,
        time: finalFormData.time,
        description: finalFormData.description,
        userId: user?.id || 'guest',
        userEmail: user?.email || 'guest@test.com',
      });
      console.log("REAL RESPONSE:", response);

      setIsTyping(false);

      // Clear image only AFTER backend processing
      setSelectedFile(null);
      setPreviewUrl(null);

      // If LOST → show matches
      if (finalFormData.status === 'lost') {
        if (response?.results && response.results.length > 0) {
          addMessage('I found potential matches! Here they are:', 'ai');
          addMessage('', 'ai', 'results', {
            results: response.results.slice(0, 4).map((r, index) => ({
              id: r.id,
              image_url: r.image_url,
              final_category: r.category,
              score: r.score,
              location: r.location || 'Reported location',
              reported_time: null,
              isBestMatch: index === 0,
            })),
          });
        } else {
          addMessage('No matches found at the moment.', 'ai');
        }
      } 
      // If FOUND → just confirm success
      else {
        addMessage('Item successfully registered and indexed. We will notify the owner if a match is found.', 'ai');
      }

      setCurrentStep('RESULTS');
      onResultsReady?.(response);
    } catch (err) {
      console.error('PROCESS ERROR:', err);
      addMessage(`Processing failed: ${err.message || 'Unknown error'}`, 'ai');
    }
  };

  const resetChat = () => {
    setMessages([
      {
        id: Date.now().toString(),
        sender: 'ai',
        text: "Hi! I'm Reclaim AI. Are you reporting a lost item, or did you find something?",
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      },
    ]);
    setCurrentStep('GREETING');
    setSelectedFile(null);
    setPreviewUrl(null);
    setFormData({
      status: null,
      location: '',
      time: '',
      description: '',
      category: '',
    });
  };

  const handleSend = () => {
    // Allow image-only send during IMAGE step
    if (currentStep !== 'IMAGE' && !inputValue.trim()) return;
    if (currentStep === 'IMAGE' && !selectedFile) return;

    // Show user message
    if (currentStep === 'IMAGE' && selectedFile) {
      // Only attach image during IMAGE step
      addMessage('Photo attached', 'user', 'image', {
        imageUrl: previewUrl,
      });
    } else {
      addMessage(inputValue, 'user', 'text');
    }

    const value = inputValue.trim();
    setInputValue('');

    switch (currentStep) {
      case 'GREETING': {
        const status = value.toLowerCase().includes('found') ? 'found' : 'lost';
        setFormData((prev) => ({ ...prev, status }));
        setCurrentStep('IMAGE');
        addMessage(
          `Got it — you're reporting a ${status} item. Please upload a photo of the item.`,
          'ai'
        );
        break;
      }

      case 'IMAGE': {
        if (!selectedFile) {
          addMessage('Please upload an image before continuing.', 'ai');
          return;
        }
        setCurrentStep('LOCATION');
        addMessage('Where did this happen? Please enter the location.', 'ai');
        break;
      }

      case 'LOCATION': {
        setFormData((prev) => ({ ...prev, location: value }));
        setCurrentStep('TIME');
        addMessage('When did this happen? (Approximate time is fine)', 'ai');
        break;
      }

      case 'TIME': {
        setFormData((prev) => ({ ...prev, time: value }));
        setCurrentStep('DESCRIPTION');
        addMessage(
          'Please describe the item in detail (color, brand, unique marks).',
          'ai'
        );
        break;
      }

      case 'DESCRIPTION': {
        setFormData((prev) => ({ ...prev, description: value }));
        setCurrentStep('CATEGORY');
        addMessage(
          'What category best fits this item? (e.g. wallet, phone, keys)',
          'ai'
        );
        break;
      }

      case 'CATEGORY': {
        const updatedData = { ...formData, category: value };
        setFormData(updatedData);
        triggerSearch(updatedData);
        break;
      }

      default:
        break;
    }
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