import React from 'react';
import { MapPin, CheckCircle2, ChevronRight } from 'lucide-react';

export function MatchResultCard({
  image_url,
  final_category,
  score,
  location,
  reported_time,
  isBestMatch,
}) {
  const confidence = score ? Math.round(score * 100) : 0;
  const title = final_category || "Matched Item";
  const category = final_category || "Unknown";
  const date = reported_time || "Recently reported";
  const image = image_url;

  return (
    <div
      className={`group relative w-full overflow-hidden rounded-2xl border transition-all duration-300 hover:scale-[1.02] ${
        isBestMatch 
          ? 'bg-amber-500/5 border-amber-500/30 shadow-[0_0_30px_rgba(245,158,11,0.1)]' 
          : 'bg-[#1a1a2e]/80 border-white/10 hover:border-white/20'
      }`}
    >
      {/* Best Match Badge */}
      {isBestMatch && (
        <div className="absolute top-0 right-0 bg-amber-500 text-black text-[10px] font-bold px-2 py-0.5 rounded-bl-lg z-10">
          BEST MATCH
        </div>
      )}

      <div className="flex p-3 gap-4">
        {/* Thumbnail Image */}
        <div className="relative w-20 h-20 flex-shrink-0 rounded-xl overflow-hidden bg-black/40 border border-white/5">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
          />
        </div>

        {/* Content Section */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-start">
              <h3 className="text-sm font-semibold text-white truncate pr-2">
                {title}
              </h3>
              
              {/* Confidence Indicator */}
              <div
                className={`flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  confidence > 90 
                    ? 'bg-green-500/20 text-green-400 border border-green-500/20' 
                    : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20'
                }`}
              >
                <CheckCircle2 className="w-3 h-3" />
                {confidence}% Match
              </div>
            </div>

            {/* Category & Date Metadata */}
            <div className="flex items-center gap-1 mt-1 text-xs text-slate-400">
              <span className="bg-white/5 px-1.5 py-0.5 rounded text-[10px] border border-white/5">
                {category}
              </span>
              <span>•</span>
              <span className="truncate">{date}</span>
            </div>
          </div>

          {/* Footer: Location & Action */}
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center gap-1 text-xs text-slate-400 truncate max-w-[120px]">
              <MapPin className="w-3 h-3 flex-shrink-0" />
              <span className="truncate">{location}</span>
            </div>
            <button className="flex items-center gap-1 text-xs font-medium text-white bg-white/10 hover:bg-white/20 px-2 py-1 rounded-lg transition-colors">
              Contact
              <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}