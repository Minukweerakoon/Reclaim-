import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../api/reports';
import { ErrorMessage, formatErrorMessage } from '../components/ErrorMessage';
import { LoadingSpinner } from '../components/LoadingSpinner';

const normalizeScore = (value?: number) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return 0;
    }
    if (value > 1) return Math.min(value / 100, 1);
    return Math.max(0, Math.min(1, value));
};

const average = (values: number[]) => {
    if (!values.length) return 0;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
};

function Monitor() {
    const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

    const { data: reportsData, isLoading, isError, error, refetch } = useQuery({
        queryKey: ['reports'],
        queryFn: () => reportsApi.getMyReports(),
        refetchInterval: 10000,
    });

    const { data: selectedReport, isLoading: isLoadingReport } = useQuery({
        queryKey: ['report', selectedReportId],
        queryFn: () => reportsApi.getReport(selectedReportId!),
        enabled: !!selectedReportId,
    });

    const reports = reportsData?.reports || [];
    const confidence = normalizeScore(selectedReport?.confidence?.overall_confidence);

    const sortedReports = useMemo(() => {
        return [...reports]
            .filter((report) => Boolean(report.timestamp))
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    }, [reports]);

    const confidenceSeries = useMemo(() => {
        return sortedReports
            .slice(0, 12)
            .reverse()
            .map((report) => normalizeScore(report.confidence?.overall_confidence));
    }, [sortedReports]);

    const confidenceDrift = useMemo(() => {
        const recent = confidenceSeries.slice(-3);
        const previous = confidenceSeries.slice(-6, -3);
        const recentAvg = average(recent);
        const previousAvg = average(previous);
        return {
            recentAvg,
            previousAvg,
            delta: recentAvg - previousAvg,
        };
    }, [confidenceSeries]);

    const sparklinePoints = useMemo(() => {
        if (confidenceSeries.length < 2) return '';
        const width = 160;
        const height = 48;
        const step = width / (confidenceSeries.length - 1);
        return confidenceSeries
            .map((value, index) => {
                const x = index * step;
                const y = height - value * height;
                return `${x},${y}`;
            })
            .join(' ');
    }, [confidenceSeries]);

    const temporalHeatmap = useMemo(() => {
        const days = 7;
        const buckets = 6;
        const today = new Date();
        const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const labels = Array.from({ length: days }, (_, index) => {
            const day = new Date(midnight);
            day.setDate(day.getDate() - (days - 1 - index));
            return day.toLocaleDateString('en-US', { weekday: 'short' });
        });

        const matrix = Array.from({ length: days }, () => Array.from({ length: buckets }, () => [] as number[]));

        sortedReports.forEach((report) => {
            if (!report.timestamp) return;
            const timestamp = new Date(report.timestamp);
            const reportDay = new Date(timestamp.getFullYear(), timestamp.getMonth(), timestamp.getDate());
            const diffDays = Math.floor((midnight.getTime() - reportDay.getTime()) / (24 * 60 * 60 * 1000));
            if (diffDays < 0 || diffDays >= days) return;
            const dayIndex = days - 1 - diffDays;
            const bucket = Math.min(buckets - 1, Math.floor(timestamp.getHours() / 4));

            const alignmentPenalty = report.cross_modal?.image_text?.valid === false ? 0.2 : 0;
            const discrepancyPenalty = alignmentPenalty > 0 ? 0.4 : 0;
            const confidencePenalty = normalizeScore(report.confidence?.overall_confidence) < 0.5 ? 0.2 : 0;
            const consistencyScore = Math.max(0, 1 - (alignmentPenalty + discrepancyPenalty + confidencePenalty));

            matrix[dayIndex][bucket].push(consistencyScore);
        });

        const averaged = matrix.map((row) => row.map((cell) => average(cell)));
        return { labels, buckets, values: averaged };
    }, [sortedReports]);

    const lineageCards = useMemo(() => sortedReports.slice(0, 3), [sortedReports]);

    const timeline = useMemo(
        () => [
            { label: 'INGEST', status: 'done', time: '12ms' },
            { label: 'PRE-PROCESS', status: 'done', time: '45ms' },
            { label: 'FEATURE', status: 'done', time: '28ms' },
            { label: 'ALIGN', status: selectedReport ? 'done' : 'pending', time: selectedReport ? '32ms' : 'Pending' },
            { label: 'DECISION', status: selectedReport ? 'done' : 'pending', time: selectedReport ? 'Ready' : 'Pending' },
        ],
        [selectedReport]
    );

    return (
        <div className="animate-fade-in">
            {/* Page Title */}
            <div className="mb-8 text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-medium mb-4">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                    </span>
                    Real-Time Analytics
                </div>
                <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                    Monitor Dashboard
                </h1>
                <p className="text-slate-400 max-w-2xl mx-auto">
                    System health metrics, confidence trends, and report lineage tracking.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
                <aside className="glass-panel rounded-2xl overflow-hidden flex flex-col">
                <div className="p-4 border-b border-white/10 flex items-center justify-between">
                    <div>
                        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-slate-400">Latest Submissions</h2>
                        <p className="text-[10px] text-slate-500 mt-1">{reports.length} active reports</p>
                    </div>
                    <span className="text-[10px] text-primary bg-primary/10 border border-primary/20 px-2 py-1 rounded">LIVE</span>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {isLoading ? (
                        <LoadingSpinner center label="Loading reports..." />
                    ) : isError ? (
                        <div className="p-4">
                            <ErrorMessage
                                title="Failed to load reports"
                                message={formatErrorMessage(error)}
                                onRetry={() => refetch()}
                                size="sm"
                            />
                        </div>
                    ) : reports.length === 0 ? (
                        <div className="p-4 text-center text-slate-400">No reports found</div>
                    ) : (
                        reports.map((report) => {
                            const reportConfidence = normalizeScore(report.confidence?.overall_confidence);
                            const riskClass = reportConfidence >= 0.8 ? 'bg-accent-emerald' : reportConfidence >= 0.5 ? 'bg-accent-amber' : 'bg-accent-rose';
                            return (
                                <button
                                    key={report.id}
                                    onClick={() => setSelectedReportId(report.id ?? null)}
                                    className={`w-full text-left p-4 border-b border-white/5 transition-colors ${selectedReportId === report.id
                                        ? 'bg-primary/10 border-l-2 border-primary'
                                        : 'hover:bg-white/5'}
                                    `}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-sm font-bold text-white">ID-{(report.id ?? report.request_id).slice(0, 6).toUpperCase()}</span>
                                        <span className={`text-[10px] uppercase tracking-widest text-white px-2 py-0.5 rounded ${riskClass}`}>
                                            {reportConfidence >= 0.8 ? 'HIGH' : reportConfidence >= 0.5 ? 'MED' : 'LOW'}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-[10px] text-slate-500">
                                        <div className="flex gap-2">
                                            {report.image && <span>IMG</span>}
                                            {report.audio && <span>VOICE</span>}
                                            {report.text && <span>TEXT</span>}
                                        </div>
                                        <span className="font-mono">{new Date(report.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                </button>
                            );
                        })
                    )}
                </div>
            </aside>

            <section className="glass-panel rounded-2xl overflow-hidden flex flex-col p-6 gap-6 overflow-y-auto">
                {selectedReport ? (
                    <>
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <h2 className="text-xl font-bold text-white">Submission {(selectedReport.id ?? selectedReport.request_id).slice(0, 8)} Analysis</h2>
                                    <span className="text-[10px] uppercase tracking-widest text-primary bg-primary/10 border border-primary/20 px-2 py-1 rounded">Validation Deep-Dive</span>
                                </div>
                                <p className="text-[11px] text-slate-500 font-mono">
                                    Generated {new Date(selectedReport.timestamp).toLocaleString()}
                                </p>
                            </div>
                            <div className="text-right">
                                <div className="text-3xl font-bold text-primary">{Math.round(confidence * 100)}%</div>
                                <div className="text-[11px] text-slate-400 uppercase tracking-widest">Confidence</div>
                            </div>
                        </div>

                        <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                            <div className="flex justify-between">
                                {timeline.map((step, index) => (
                                    <div key={step.label} className="flex flex-col items-center flex-1 relative">
                                        <div
                                            className={`w-8 h-8 rounded-full flex items-center justify-center z-10 ${step.status === 'done'
                                                ? 'bg-primary text-white shadow-neon-cyan'
                                                : 'bg-slate-800 text-slate-500 border border-slate-600'
                                                }`}
                                        >
                                            <span className="text-[10px] font-bold">{index + 1}</span>
                                        </div>
                                        <span className={`text-[10px] font-bold mt-2 ${step.status === 'done' ? 'text-white' : 'text-slate-500'}`}>
                                            {step.label}
                                        </span>
                                        <span className={`text-[9px] font-mono ${step.status === 'done' ? 'text-accent-emerald' : 'text-slate-600'}`}>
                                            {step.time}
                                        </span>
                                        {index < timeline.length - 1 && (
                                            <div className="absolute top-4 left-[50%] w-full h-[2px] bg-slate-700">
                                                <div className="h-full bg-primary" style={{ width: step.status === 'done' ? '100%' : '30%' }} />
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Confidence Drift</div>
                                <div className="flex items-center justify-between mb-3">
                                    <div>
                                        <div className="text-2xl font-bold text-white">{Math.round(confidenceDrift.recentAvg * 100)}%</div>
                                        <div className="text-[10px] text-slate-500 uppercase">Recent average</div>
                                    </div>
                                    <div className={`text-xs font-mono ${confidenceDrift.delta >= 0 ? 'text-accent-emerald' : 'text-alert-red'}`}>
                                        {confidenceDrift.delta >= 0 ? '+' : ''}{Math.round(confidenceDrift.delta * 100)}%
                                    </div>
                                </div>
                                {sparklinePoints ? (
                                    <svg viewBox="0 0 160 48" className="w-full h-12">
                                        <polyline
                                            points={sparklinePoints}
                                            fill="none"
                                            stroke="#06b6d4"
                                            strokeWidth="2"
                                            strokeLinejoin="round"
                                            strokeLinecap="round"
                                        />
                                    </svg>
                                ) : (
                                    <div className="text-[10px] text-slate-500">Not enough data for drift.</div>
                                )}
                            </div>

                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Temporal Consistency</div>
                                <div className="grid grid-cols-7 gap-1 text-[9px] text-slate-500 mb-2">
                                    {temporalHeatmap.labels.map((label) => (
                                        <div key={label} className="text-center">{label}</div>
                                    ))}
                                </div>
                                <div className="grid grid-cols-7 gap-1">
                                    {temporalHeatmap.values.map((row, rowIndex) => (
                                        row.map((value, colIndex) => {
                                            const alpha = 0.15 + value * 0.75;
                                            return (
                                                <div
                                                    key={`${rowIndex}-${colIndex}`}
                                                    className="h-5 rounded border border-white/5"
                                                    style={{ backgroundColor: `rgba(6, 182, 212, ${alpha})` }}
                                                />
                                            );
                                        })
                                    ))}
                                </div>
                                <div className="flex justify-between text-[9px] text-slate-500 mt-2">
                                    <span>00-04</span>
                                    <span>20-24</span>
                                </div>
                            </div>

                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">QA Lineage</div>
                                <div className="space-y-3">
                                    {lineageCards.length ? lineageCards.map((report) => (
                                        <div key={report.id} className="bg-slate-900/60 border border-white/10 rounded-lg p-3">
                                            <div className="flex items-center justify-between">
                                                <span className="text-xs font-bold text-white">ID-{(report.id || report.request_id || '').slice(0, 6).toUpperCase()}</span>
                                                <span className="text-[10px] text-slate-500 font-mono">
                                                    {new Date(report.timestamp).toLocaleTimeString()}
                                                </span>
                                            </div>
                                            <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-2">
                                                {report.input_types?.includes('text') && <span>TXT</span>}
                                                {report.input_types?.includes('image') && <span>IMG</span>}
                                                {report.input_types?.includes('voice') && <span>VOICE</span>}
                                                <span className="ml-auto">{report.confidence?.routing?.replace(/_/g, ' ') || ''}</span>
                                            </div>
                                        </div>
                                    )) : (
                                        <div className="text-[10px] text-slate-500">No lineage data available.</div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Modality Scores</div>
                                <div className="flex justify-around">
                                    {[
                                        { label: 'Image', value: normalizeScore(selectedReport.image?.overall_score), color: '#06b6d4' },
                                        { label: 'Text', value: normalizeScore(selectedReport.text?.overall_score), color: '#10b981' },
                                        { label: 'Voice', value: normalizeScore(selectedReport.voice?.confidence), color: '#f43f5e' },
                                    ].map((item) => (
                                        <div key={item.label} className="flex flex-col items-center gap-3">
                                            <div
                                                className="relative w-[72px] h-[72px] rounded-full flex items-center justify-center"
                                                style={{ background: `conic-gradient(${item.color} ${Math.round(item.value * 100)}%, #334155 0)` }}
                                            >
                                                <div className="absolute w-[56px] h-[56px] rounded-full bg-slate-900 flex items-center justify-center">
                                                    <span className="text-xs font-bold text-white">{Math.round(item.value * 100)}%</span>
                                                </div>
                                            </div>
                                            <span className="text-[10px] uppercase tracking-widest text-slate-400">{item.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Cross-Modal Alignment</div>
                                <div className="mb-4">
                                    <div className="flex justify-between text-[10px] text-slate-400 uppercase">
                                        <span>CLIP similarity</span>
                                        <span className="text-primary">{Math.round(normalizeScore(selectedReport.cross_modal?.image_text?.similarity) * 100)}%</span>
                                    </div>
                                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                                        <div className="h-full bg-primary" style={{ width: `${Math.round(normalizeScore(selectedReport.cross_modal?.image_text?.similarity) * 100)}%` }} />
                                    </div>
                                </div>
                                <div className="text-[10px] text-slate-500">
                                    {selectedReport.cross_modal?.image_text?.valid ? 'Modalities align successfully.' : 'Potential alignment conflict.'}
                                </div>
                            </div>

                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Spatial Plausibility</div>
                                <div className="relative w-full h-24 rounded bg-slate-800 border border-slate-700 mb-4 overflow-hidden">
                                    <div className="absolute inset-0 flex items-center justify-center opacity-20">
                                        <div className="text-4xl text-slate-600">MAP</div>
                                    </div>
                                    <div className="absolute inset-0 flex items-center justify-center">
                                        <div className="w-4 h-4 bg-accent-emerald rounded-full animate-ping opacity-50"></div>
                                        <div className="w-2 h-2 bg-accent-emerald rounded-full absolute"></div>
                                    </div>
                                </div>
                                <div className="text-[10px] text-slate-500">
                                    {selectedReport.cross_modal?.spatial_temporal?.explanation || 'Spatial context verified.'}
                                </div>
                            </div>
                        </div>

                        {selectedReport.cross_modal?.image_text && !selectedReport.cross_modal.image_text.valid && (
                            <div className="bg-alert-red/10 border border-alert-red/30 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-alert-red mb-3">Discrepancy Engine</div>
                                <div className="space-y-3">
                                    <div className="bg-slate-900/70 border border-alert-red/20 rounded-lg p-3">
                                        <div className="text-xs text-alert-red uppercase">Cross-Modal Mismatch</div>
                                        <div className="text-xs text-slate-300 mt-1">{selectedReport.cross_modal.image_text.feedback}</div>
                                    </div>
                                    {selectedReport.cross_modal.image_text.suggestions?.map((s: string, i: number) => (
                                        <div key={i} className="bg-slate-900/70 border border-alert-red/20 rounded-lg p-3">
                                            <div className="text-xs text-alert-red uppercase">Suggestion</div>
                                            <div className="text-xs text-slate-300 mt-1">{s}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                ) : isLoadingReport && selectedReportId ? (
                    <LoadingSpinner center label="Loading report details..." />
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-500">
                        <div className="text-3xl mb-3">Select a report</div>
                        <p className="text-sm">Choose a submission to open the analysis deck.</p>
                    </div>
                )}
            </section>
            </div>
        </div>
    );
}

export default Monitor;
