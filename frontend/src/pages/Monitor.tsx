import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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


const getReportTimestamp = (report: Record<string, any>) => {
    return report.timestamp || report.created_at || report.createdAt || null;
};

const getReportIntent = (report: Record<string, any>) => {
    return report.intention || report.item_type || 'lost';
};

const getReportCategory = (report: Record<string, any>) => {
    return report.user_category || report.item_type_name || report.item_name || report.item || '';
};

const getReportItemStatus = (report: Record<string, any>) => {
    return report.item_status || report.status || 'open';
};

const getReportInputTypes = (report: Record<string, any>) => {
    return report.input_types || report.validation_summary?.input_types || [];
};

const getReportConfidence = (report: Record<string, any>) => {
    return normalizeScore(
        report.confidence?.overall_confidence ??
        report.confidence_score ??
        report.validation_summary?.overall_confidence ??
        report.validation_summary?.confidence?.overall_confidence
    );
};

function Monitor() {
    const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
    const queryClient = useQueryClient();

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

    const updateStatusMutation = useMutation({
        mutationFn: ({ reportId, itemStatus }: { reportId: string; itemStatus: string }) =>
            reportsApi.updateReportStatus(reportId, itemStatus),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['reports'] });
            if (selectedReportId) {
                queryClient.invalidateQueries({ queryKey: ['report', selectedReportId] });
            }
        },
    });

    const reports = reportsData?.reports || [];
    const confidence = selectedReport ? getReportConfidence(selectedReport) : 0;

    const sortedReports = useMemo(() => {
        return [...reports]
            .filter((report) => Boolean(getReportTimestamp(report)))
            .sort((a, b) => {
                const aTime = getReportTimestamp(a);
                const bTime = getReportTimestamp(b);
                return new Date(bTime || 0).getTime() - new Date(aTime || 0).getTime();
            });
    }, [reports]);
    const listReports = sortedReports.length ? sortedReports : reports;
    const selectedTimestamp = selectedReport ? getReportTimestamp(selectedReport) : null;
    const selectedIntent = selectedReport ? getReportIntent(selectedReport) : '';
    const selectedCategory = selectedReport ? getReportCategory(selectedReport) : '';
    const selectedInputTypes = selectedReport ? getReportInputTypes(selectedReport) : [];
    const validationSummary = selectedReport?.validation_summary || {};
    const individualScores = validationSummary.individual_scores || selectedReport?.confidence?.individual_scores || {};
    const reportStatus = selectedReport ? getReportItemStatus(selectedReport) : 'open';
    const statusOptions = ['open', 'claimed', 'returned', 'closed'];

    return (
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 h-[calc(100vh-160px)]">
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
                    ) : listReports.length === 0 ? (
                        <div className="p-4 text-center text-slate-400">No reports found</div>
                    ) : (
                        listReports.map((report) => {
                            const reportConfidence = getReportConfidence(report);
                            const riskClass = reportConfidence >= 0.8 ? 'bg-accent-emerald' : reportConfidence >= 0.5 ? 'bg-accent-amber' : 'bg-accent-rose';
                            const reportTimestamp = getReportTimestamp(report);
                            const reportIntent = getReportIntent(report);
                            const reportCategory = getReportCategory(report);
                            const reportStatus = getReportItemStatus(report);
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
                                            <span className="uppercase">{reportIntent}</span>
                                            {reportCategory && <span className="text-slate-400">• {reportCategory}</span>}
                                        </div>
                                        <span className="font-mono">
                                            {reportTimestamp ? new Date(reportTimestamp).toLocaleString() : 'Unknown'}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-[10px] text-slate-500 uppercase tracking-widest">
                                        Status: <span className="text-slate-300">{reportStatus}</span>
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
                                    <span className="text-[10px] uppercase tracking-widest text-primary bg-primary/10 border border-primary/20 px-2 py-1 rounded">Submission Summary</span>
                                </div>
                                <p className="text-[11px] text-slate-500 font-mono">
                                    Submitted {selectedTimestamp ? new Date(selectedTimestamp).toLocaleString() : 'Unknown'}
                                </p>
                            </div>
                            <div className="text-right">
                                <div className="text-3xl font-bold text-primary">{Math.round(confidence * 100)}%</div>
                                <div className="text-[11px] text-slate-400 uppercase tracking-widest">Confidence</div>
                            </div>
                        </div>
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Reported Details</div>
                                <div className="space-y-3 text-sm text-slate-300">
                                    <div className="flex justify-between"><span className="text-slate-500">Intent</span><span className="uppercase">{selectedIntent}</span></div>
                                    <div className="flex justify-between"><span className="text-slate-500">Status</span><span className="uppercase">{reportStatus}</span></div>
                                    {selectedCategory && (
                                        <div className="flex justify-between"><span className="text-slate-500">Category</span><span>{selectedCategory}</span></div>
                                    )}
                                    {selectedReport.description && (
                                        <div className="flex justify-between"><span className="text-slate-500">Description</span><span className="text-right max-w-[60%]">{selectedReport.description}</span></div>
                                    )}
                                    {selectedReport.location && (
                                        <div className="flex justify-between"><span className="text-slate-500">Location</span><span className="text-right max-w-[60%]">{selectedReport.location}</span></div>
                                    )}
                                    {selectedReport.time_of_incident && (
                                        <div className="flex justify-between"><span className="text-slate-500">Time</span><span>{selectedReport.time_of_incident}</span></div>
                                    )}
                                    {selectedReport.color && (
                                        <div className="flex justify-between"><span className="text-slate-500">Color</span><span>{selectedReport.color}</span></div>
                                    )}
                                </div>
                                {selectedReport.image_url && (
                                    <div className="mt-4">
                                        <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Attached Image</div>
                                        <img
                                            src={selectedReport.image_url}
                                            alt="Reported item"
                                            className="w-full h-48 object-cover rounded-lg border border-white/10"
                                        />
                                    </div>
                                )}
                            </div>

                            <div className="bg-slate-900/40 border border-white/10 rounded-xl p-5">
                                <div className="text-[11px] uppercase tracking-widest text-slate-400 mb-4">Validation Summary</div>
                                <div className="space-y-3 text-sm text-slate-300">
                                    <div className="flex justify-between"><span className="text-slate-500">Confidence</span><span>{Math.round(confidence * 100)}%</span></div>
                                    <div className="flex justify-between"><span className="text-slate-500">Routing</span><span className="uppercase">{selectedReport.routing || validationSummary.routing || selectedReport.confidence?.routing || 'manual'}</span></div>
                                    <div className="flex justify-between"><span className="text-slate-500">Action</span><span className="uppercase">{selectedReport.action || validationSummary.action || selectedReport.confidence?.action || 'review'}</span></div>
                                    {selectedInputTypes.length > 0 && (
                                        <div className="flex justify-between"><span className="text-slate-500">Inputs</span><span className="uppercase">{selectedInputTypes.join(', ')}</span></div>
                                    )}
                                </div>

                                <div className="mt-4">
                                    <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Update Status</div>
                                    <div className="flex flex-wrap gap-2">
                                        {statusOptions.map((status) => {
                                            const isActive = status === reportStatus;
                                            return (
                                                <button
                                                    key={status}
                                                    onClick={() => {
                                                        if (!selectedReport?.id || isActive || updateStatusMutation.isPending) return;
                                                        updateStatusMutation.mutate({ reportId: selectedReport.id, itemStatus: status });
                                                    }}
                                                    className={`px-3 py-1 rounded-full text-[10px] uppercase tracking-widest border ${isActive
                                                        ? 'bg-primary/20 border-primary text-primary'
                                                        : 'border-white/10 text-slate-300 hover:border-primary/40'}
                                                    `}
                                                    disabled={updateStatusMutation.isPending}
                                                >
                                                    {status}
                                                </button>
                                            );
                                        })}
                                    </div>
                                    {updateStatusMutation.isError && (
                                        <div className="text-[10px] text-alert-red mt-2">Failed to update status.</div>
                                    )}
                                </div>

                                {Object.keys(individualScores).length > 0 && (
                                    <div className="mt-4">
                                        <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Individual Scores</div>
                                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                                            {Object.entries(individualScores).map(([key, value]) => (
                                                <div key={key} className="flex justify-between bg-slate-900/60 border border-white/5 rounded px-2 py-1">
                                                    <span className="text-slate-400 uppercase">{key}</span>
                                                    <span className="text-slate-200">{Math.round(normalizeScore(Number(value)) * 100)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {validationSummary && Object.keys(validationSummary).length > 0 && (
                                    <div className="mt-4">
                                        <div className="text-[10px] uppercase tracking-widest text-slate-500 mb-2">Raw Validation Summary</div>
                                        <pre className="text-[10px] text-slate-400 bg-slate-950/60 border border-white/10 rounded-lg p-3 overflow-x-auto">
                                            {JSON.stringify(validationSummary, null, 2)}
                                        </pre>
                                    </div>
                                )}
                            </div>
                        </div>
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
    );
}

export default Monitor;
