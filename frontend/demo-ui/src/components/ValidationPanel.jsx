import React, { useState } from 'react';
import {
  Info,
  TrendingUp,
  Tag,
  BarChart2,
  CheckCircle2,
  AlertTriangle,
  XCircle,
} from 'lucide-react';

/**
 * Renders a circular progress indicator using SVG.
 * The dash offset is calculated based on the circumference: 2 * π * r
 */
function CircularProgress({ value, size = 96 }) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (value / 100) * circumference;

  const color = value >= 80 ? '#22c55e' : value >= 50 ? '#f59e0b' : '#ef4444';
  const glowColor =
    value >= 80
      ? 'rgba(34,197,94,0.3)'
      : value >= 50
        ? 'rgba(245,158,11,0.3)'
        : 'rgba(239,68,68,0.3)';

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.06)"
          strokeWidth="6"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{
            transition: 'stroke-dashoffset 1s ease-out',
            filter: `drop-shadow(0 0 6px ${glowColor})`,
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-bold text-white leading-none">
          {value}%
        </span>
        <span className="text-[9px] text-slate-500 mt-0.5 uppercase tracking-wider">
          score
        </span>
      </div>
    </div>
  );
}

function Tooltip({ text }) {
  const [show, setShow] = useState(false);
  return (
    <div className="relative inline-flex">
      <button
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        className="text-slate-500 hover:text-slate-300 transition-colors"
      >
        <Info className="w-3 h-3" />
      </button>
      {show && (
        <div className="absolute bottom-5 left-1/2 -translate-x-1/2 w-44 bg-[#1a1a2e] border border-white/10 rounded-lg p-2 text-[10px] text-slate-300 leading-relaxed z-50 shadow-xl">
          {text}
        </div>
      )}
    </div>
  );
}

function SectionHeader({ icon, title }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <div className="text-indigo-400">{icon}</div>
      <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
        {title}
      </span>
    </div>
  );
}

export function ValidationPanel({
  isVisible,
  confidence,
  imageTextSimilarity,
  userCategory,
  modelCategory,
  topMatchScore,
  alphaWeight,
  entropy,
  matchesFound,
}) {
  const alignmentThreshold = 75;
  const alignmentStatus =
    imageTextSimilarity >= alignmentThreshold + 10
      ? 'Aligned'
      : imageTextSimilarity >= alignmentThreshold
        ? 'Low Alignment'
        : 'Mismatch';

  const modelOverride = userCategory !== modelCategory;
  const finalCategory = modelCategory;

  const confidenceColor =
    confidence >= 80
      ? 'text-green-400'
      : confidence >= 50
        ? 'text-amber-400'
        : 'text-red-400';

  const alignmentColor =
    alignmentStatus === 'Aligned'
      ? 'bg-green-500/15 text-green-400 border-green-500/20'
      : alignmentStatus === 'Low Alignment'
        ? 'bg-amber-500/15 text-amber-400 border-amber-500/20'
        : 'bg-red-500/15 text-red-400 border-red-500/20';

  const AlignmentIcon =
    alignmentStatus === 'Aligned'
      ? CheckCircle2
      : alignmentStatus === 'Low Alignment'
        ? AlertTriangle
        : XCircle;

  if (!isVisible) {
    return (
      <div className="w-72 flex-shrink-0 hidden lg:flex flex-col gap-3 pt-6 pr-4 pb-4 opacity-40">
        <div className="glass-panel rounded-2xl p-5 flex flex-col items-center justify-center gap-2 h-40">
          <BarChart2 className="w-6 h-6 text-slate-500" />
          <p className="text-xs text-slate-500 text-center">
            Validation panel
            <br />
            appears after results
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-72 flex-shrink-0 hidden lg:flex flex-col gap-3 pt-6 pr-4 pb-4 overflow-y-auto animate-fade-in">
      {/* A. Overall Confidence Score */}
      <div className="glass-panel rounded-2xl p-4 border border-white/5">
        <SectionHeader
          icon={<TrendingUp className="w-3.5 h-3.5" />}
          title="Match Confidence"
        />
        <div className="flex items-center gap-4">
          <CircularProgress value={confidence} />
          <div className="flex-1">
            <p className={`text-2xl font-bold ${confidenceColor}`}>
              {confidence}%
            </p>
            <p className="text-xs text-slate-400 mt-0.5">
              {confidence >= 80
                ? 'High confidence match'
                : confidence >= 50
                  ? 'Moderate confidence'
                  : 'Low confidence'}
            </p>
          </div>
        </div>
      </div>

      {/* B. Image-Text Alignment */}
      <div className="glass-panel rounded-2xl p-4 border border-white/5">
        <SectionHeader
          icon={<CheckCircle2 className="w-3.5 h-3.5" />}
          title="Image–Text Alignment"
        />
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <span className="text-lg font-bold text-white">
              {imageTextSimilarity}%
            </span>
            <span className="text-xs text-slate-500">similarity</span>
          </div>
          <div className="flex items-center gap-1">
            <span
              className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${alignmentColor}`}
            >
              <AlignmentIcon className="w-2.5 h-2.5" />
              {alignmentStatus}
            </span>
            <Tooltip text="Measures how well the uploaded image matches the text description. Threshold is 75%." />
          </div>
        </div>
        <div className="relative h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${imageTextSimilarity}%`,
              background:
                alignmentStatus === 'Aligned'
                  ? '#22c55e'
                  : alignmentStatus === 'Low Alignment'
                    ? '#f59e0b'
                    : '#ef4444',
            }}
          />
        </div>
      </div>

      {/* C. Category Comparison */}
      <div className="glass-panel rounded-2xl p-4 border border-white/5">
        <SectionHeader
          icon={<Tag className="w-3.5 h-3.5" />}
          title="Category Comparison"
        />
        <div className="space-y-2">
          {[
            { label: 'User Category', value: userCategory, highlight: false },
            { label: 'Model Category', value: modelCategory, highlight: modelOverride },
            { label: 'Final Category', value: finalCategory, highlight: false, bold: true },
          ].map(({ label, value, highlight, bold }) => (
            <div
              key={label}
              className={`flex items-center justify-between px-2.5 py-1.5 rounded-lg ${highlight ? 'bg-blue-500/10 border border-blue-500/15' : 'bg-white/[0.03]'}`}
            >
              <span className="text-[10px] text-slate-400">{label}</span>
              <span className={`text-xs ${bold ? 'font-semibold text-white' : 'text-slate-200'}`}>
                {value}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* D. Retrieval Analytics */}
      <div className="glass-panel rounded-2xl p-4 border border-white/5">
        <SectionHeader
          icon={<BarChart2 className="w-3.5 h-3.5" />}
          title="Retrieval Analytics"
        />
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Top Match', value: topMatchScore.toFixed(2), sub: 'score' },
            { label: 'Alpha Weight', value: alphaWeight.toFixed(2), sub: 'weight' },
            { label: 'Entropy', value: entropy.toFixed(2), sub: 'value' },
            { label: 'Matches', value: String(matchesFound), sub: 'found' },
          ].map(({ label, value, sub }) => (
            <div key={label} className="bg-white/[0.03] border border-white/5 rounded-xl p-2.5">
              <p className="text-[9px] text-slate-500 uppercase tracking-wider mb-1">{label}</p>
              <p className="text-base font-bold text-white leading-none">{value}</p>
              <p className="text-[9px] text-slate-500 mt-0.5">{sub}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}