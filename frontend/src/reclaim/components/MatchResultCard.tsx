// @ts-nocheck
import React, { useState } from 'react';
import { MapPin, CheckCircle2, ChevronRight, Clock3 } from 'lucide-react';

export function MatchResultCard({ image_url, final_category, score, location, reported_time, isBestMatch, onContact }) {
    const [revealSensitive, setRevealSensitive] = useState(false);
    const confidence = score ? Math.round(score * 100) : 0;
    const title = final_category || 'Matched Item';
    const category = final_category || 'Unknown';
    const date = reported_time || 'Recently reported';
    const categoryLower = String(category).toLowerCase();
    const isSensitiveCard = ['card', 'id', 'license', 'passport', 'credit', 'debit'].some((keyword) => categoryLower.includes(keyword));

    const startReveal = () => setRevealSensitive(true);
    const stopReveal = () => setRevealSensitive(false);

    return (
        <div className={`group relative w-full overflow-hidden rounded-2xl border transition-all duration-300 hover:scale-[1.01] ${isBestMatch
                ? 'bg-amber-500/5 border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.1)]'
                : 'bg-[#1a1a2e]/80 border-white/10 hover:border-white/20'
            }`}>
            {isBestMatch && (
                <div className="absolute top-0 right-0 bg-amber-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-bl-lg z-10">
                    BEST MATCH
                </div>
            )}
            <div className="flex flex-col sm:flex-row p-3.5 gap-3 sm:gap-4">
                <div className="relative w-full h-40 sm:w-24 sm:h-24 flex-shrink-0 rounded-xl overflow-hidden bg-black/40 border border-white/5">
                    <img
                        src={image_url}
                        alt={title}
                        className={`w-full h-full object-cover transition-transform duration-500 group-hover:scale-110 ${isSensitiveCard && !revealSensitive ? 'blur-[2px]' : ''}`}
                    />
                    {isSensitiveCard && !revealSensitive && (
                        <div className="absolute inset-x-0 top-0 h-1/2 backdrop-blur-md bg-slate-900/25 pointer-events-none" />
                    )}
                    {isSensitiveCard && (
                        <button
                            type="button"
                            onMouseDown={startReveal}
                            onMouseUp={stopReveal}
                            onMouseLeave={stopReveal}
                            onTouchStart={startReveal}
                            onTouchEnd={stopReveal}
                            onTouchCancel={stopReveal}
                            className="absolute bottom-1 right-1 text-[9px] px-1.5 py-0.5 rounded bg-black/60 text-white border border-white/20"
                            title="Hold to reveal"
                        >
                            Hold
                        </button>
                    )}
                </div>
                <div className="flex-1 min-w-0 flex flex-col justify-between">
                    <div>
                        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2">
                            <h3 className="text-base font-semibold text-white break-words pr-2">{title}</h3>
                            <div className={`self-start flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full whitespace-nowrap ${confidence > 90
                                    ? 'bg-green-500/20 text-green-400 border border-green-500/20'
                                    : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20'
                                }`}>
                                <CheckCircle2 className="w-3 h-3" />
                                {confidence}% Match
                            </div>
                        </div>
                        <div className="flex items-center gap-1 mt-1 text-xs text-slate-400 flex-wrap">
                            <span className="bg-white/5 px-1.5 py-0.5 rounded text-[10px] border border-white/5">{category}</span>
                            <span>•</span>
                            <span className="truncate inline-flex items-center gap-1"><Clock3 className="w-3 h-3" />{date}</span>
                        </div>
                    </div>
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mt-3">
                        <div className="flex items-center gap-1 text-xs text-slate-400 min-w-0 sm:max-w-[170px]">
                            <MapPin className="w-3 h-3 flex-shrink-0" />
                            <span className="truncate">{location}</span>
                        </div>
                        <button onClick={onContact} className="self-start sm:self-auto flex items-center gap-1 text-xs font-medium text-white bg-white/10 hover:bg-white/20 px-3 py-1.5 rounded-lg transition-colors">
                            Contact <ChevronRight className="w-3 h-3" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
