// @ts-nocheck
import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Upload, Bell, History, ShieldAlert } from 'lucide-react';
import { io } from 'socket.io-client';
import { voshanDetectionApi, getVoshanWsUrl } from '../api/voshanDetectionApi';

/** Build URL for alert frame image (ML service saves to alert_frames/; Node serves at /api/voshan/detection/alert-frames/) */
function getAlertFrameUrl(alert: { frame_url?: string; frame_image?: string; frameImage?: string }): string | null {
  if (alert.frame_url) return alert.frame_url;
  const fn = alert.frame_image || alert.frameImage;
  if (!fn) return null;
  const base = voshanDetectionApi.baseUrl;
  return `${base}/voshan/detection/alert-frames/${fn}`;
}

export function AdminDashboard({ user, onSignOut }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [toasts, setToasts] = useState<{ id: number; type: string; severity: string; message: string }[]>([]);
  const [health, setHealth] = useState<{ healthy?: boolean } | null>(null);
  const socketRef = useRef(null);
  const toastIdRef = useRef(0);

  const addToast = (type: string, severity: string, message: string) => {
    const id = ++toastIdRef.current;
    setToasts((t) => [...t.slice(-4), { id, type, severity, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 5000);
  };

  const loadAlerts = async () => {
    setAlertsLoading(true);
    try {
      const res = await voshanDetectionApi.getAlerts({ page: pagination.page, limit: pagination.limit });
      if (res.success && res.data?.alerts) {
        setAlerts(res.data.alerts);
        setPagination((p) => ({ ...p, total: res.data.pagination?.total ?? res.data.alerts.length }));
      }
    } catch (e) {
      addToast('error', 'HIGH', 'Failed to load alerts');
    } finally {
      setAlertsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [pagination.page, pagination.limit]);

  useEffect(() => {
    voshanDetectionApi.health().then(setHealth).catch(() => setHealth({ healthy: false }));
  }, []);

  useEffect(() => {
    const wsUrl = getVoshanWsUrl();
    const socket = io(wsUrl, { path: '/api/voshan/socket.io', transports: ['websocket', 'polling'] });
    socketRef.current = socket;
    socket.on('alert', (data) => {
      const type = data?.type || 'Alert';
      const severity = data?.severity || 'MEDIUM';
      addToast(type, severity, `New alert: ${type} (${severity})`);
      loadAlerts();
    });
    socket.on('connect_error', () => {});
    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  const [cameraId, setCameraId] = useState('');
  const [saveOutput, setSaveOutput] = useState(true);

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = e.currentTarget;
    const fileInput = form.querySelector('input[type="file"]') as HTMLInputElement;
    const file = fileInput?.files?.[0];
    if (!file) {
      setUploadError('Please select a video file');
      return;
    }
    setUploadError(null);
    setUploadResult(null);
    setUploading(true);
    setProgress(0);
    try {
      const result = await voshanDetectionApi.processVideo(
        file,
        { cameraId: cameraId || undefined, saveOutput },
        (p) => setProgress(p)
      );
      if (result.success && result.data) {
        setUploadResult(result.data);
        addToast('success', 'LOW', `Video processed: ${result.data.totalAlerts ?? 0} alerts`);
        loadAlerts();
      } else {
        setUploadError(result.message || result.error || 'Upload failed');
      }
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const displayName = user?.user_metadata?.full_name || user?.email || 'Admin';

  return (
    <div className="min-h-screen bg-[#08080f] text-white">
      <header className="sticky top-0 z-40 border-b border-white/10 bg-[#08080f]/90 backdrop-blur flex items-center justify-between px-4 md:px-8 h-16">
        <div className="flex items-center gap-4">
          <Link to="/reclaim" className="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-amber-400" />
            <h1 className="text-lg font-semibold">Suspicious Behavior – Admin</h1>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-400 hidden sm:block">{displayName}</span>
          <button
            onClick={onSignOut}
            className="px-3 py-1.5 text-sm rounded-lg bg-white/10 hover:bg-white/20"
          >
            Sign out
          </button>
        </div>
      </header>

      {/* Toasts */}
      <div className="fixed top-20 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`px-4 py-3 rounded-lg border shadow-lg ${
              t.severity === 'HIGH' ? 'bg-red-500/20 border-red-500/50' : 'bg-amber-500/20 border-amber-500/50'
            }`}
          >
            <p className="font-medium">{t.type}</p>
            <p className="text-sm text-slate-300">{t.message}</p>
          </div>
        ))}
      </div>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* ML health */}
        {health && (
          <div className="flex items-center gap-2 text-sm">
            <span className={health.healthy ? 'text-green-400' : 'text-red-400'}>
              {health.healthy ? '● ML service connected' : '○ ML service unavailable'}
            </span>
          </div>
        )}

        {/* Video upload */}
        <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold mb-4">
            <Upload className="w-5 h-5" /> Upload video
          </h2>
          <form onSubmit={handleUpload} className="space-y-4">
            <div>
              <input type="file" accept="video/*" className="text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-indigo-600 file:text-white" />
            </div>
            <div className="flex flex-wrap gap-4 items-center">
              <label className="flex items-center gap-2">
                <span className="text-slate-400 text-sm">Camera ID</span>
                <input
                  type="text"
                  value={cameraId}
                  onChange={(e) => setCameraId(e.target.value)}
                  placeholder="Optional"
                  className="bg-white/5 border border-white/10 rounded px-3 py-1.5 text-sm w-32"
                />
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={saveOutput} onChange={(e) => setSaveOutput(e.target.checked)} />
                <span className="text-sm text-slate-400">Save output video</span>
              </label>
            </div>
            {uploading && (
              <div className="h-2 bg-white/10 rounded overflow-hidden">
                <div className="h-full bg-indigo-500 transition-all" style={{ width: `${progress}%` }} />
              </div>
            )}
            {uploadError && <p className="text-sm text-red-400">{uploadError}</p>}
            {uploadResult && (
              <p className="text-sm text-green-400">
                Done: {uploadResult.totalFrames ?? 0} frames, {uploadResult.totalAlerts ?? 0} alerts
              </p>
            )}
            <button type="submit" disabled={uploading} className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium">
              {uploading ? 'Processing…' : 'Upload & process'}
            </button>
          </form>
        </section>

        {/* Alert history */}
        <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="flex items-center gap-2 text-lg font-semibold">
              <History className="w-5 h-5" /> Alert history
            </h2>
            <button onClick={loadAlerts} disabled={alertsLoading} className="text-sm text-slate-400 hover:text-white disabled:opacity-50">
              Refresh
            </button>
          </div>
          {alertsLoading ? (
            <p className="text-slate-400 text-sm">Loading…</p>
          ) : alerts.length === 0 ? (
            <p className="text-slate-400 text-sm">No alerts yet. Upload a video to detect suspicious behavior.</p>
          ) : (
            <ul className="space-y-4">
              {alerts.map((a) => {
                const frameUrl = getAlertFrameUrl(a);
                return (
                <li key={a.id ?? a.alertId ?? a.alert_id ?? Math.random()} className="rounded-xl border border-white/10 bg-white/5 p-4 flex gap-4">
                  {frameUrl && (
                    <img src={frameUrl} alt="" className="w-32 h-24 object-cover rounded-lg flex-shrink-0 bg-black/20" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="font-medium">{a.type ?? a.alert_type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        a.severity === 'HIGH' ? 'bg-red-500/20 text-red-300' :
                        a.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-500/20 text-slate-300'
                      }`}>
                        {a.severity ?? 'N/A'}
                      </span>
                      {a.cameraId && <span className="text-xs text-slate-400">{a.cameraId}</span>}
                    </div>
                    <p className="text-xs text-slate-400">
                      {a.timestamp ? new Date(typeof a.timestamp === 'number' ? a.timestamp * 1000 : a.timestamp).toLocaleString() : '—'}
                    </p>
                    {a.details && Object.keys(a.details).length > 0 && (
                      <pre className="mt-2 text-xs text-slate-500 overflow-auto max-h-20">{JSON.stringify(a.details, null, 0)}</pre>
                    )}
                  </div>
                </li>
              );
              })}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}
