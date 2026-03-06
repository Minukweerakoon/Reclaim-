// @ts-nocheck
import { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Upload, Bell, History, ShieldAlert, Filter } from 'lucide-react';
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

const FRAME_WINDOW = 50;

/** Group alerts by 50-frame window and type for display */
function groupAlertsByWindow(alerts: any[]) {
  const map = new Map<string, { type: string; severity: string; frameStart: number; frameEnd: number; cameraId?: string; alerts: any[] }>();
  for (const a of alerts) {
    const frame = Number(a.frame ?? 0);
    const bucket = Math.floor(frame / FRAME_WINDOW) * FRAME_WINDOW;
    const type = a.type ?? a.alert_type ?? 'Alert';
    const key = `${bucket}_${type}`;
    if (!map.has(key)) {
      map.set(key, {
        type,
        severity: a.severity ?? 'MEDIUM',
        frameStart: bucket,
        frameEnd: bucket + FRAME_WINDOW - 1,
        cameraId: a.cameraId ?? a.camera_id,
        alerts: []
      });
    }
    map.get(key).alerts.push(a);
  }
  const list = Array.from(map.values());
  list.sort((a, b) => {
    const ta = a.alerts[0]?.timestamp != null ? new Date(typeof a.alerts[0].timestamp === 'number' ? a.alerts[0].timestamp * 1000 : a.alerts[0].timestamp).getTime() : 0;
    const tb = b.alerts[0]?.timestamp != null ? new Date(typeof b.alerts[0].timestamp === 'number' ? b.alerts[0].timestamp * 1000 : b.alerts[0].timestamp).getTime() : 0;
    return tb - ta;
  });
  return list;
}

type NotificationItem = {
  id: string;
  type: string;
  severity: string;
  message: string;
  timestamp: number;
  read: boolean;
  cameraId?: string;
  frameImages?: string[];
  frameStart?: number;
  frameEnd?: number;
  count?: number;
};

export function AdminDashboard({ user, onSignOut }) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });
  const [alertsLoading, setAlertsLoading] = useState(true);
  const [toasts, setToasts] = useState<{ id: number; type: string; severity: string; message: string }[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [notificationPanelOpen, setNotificationPanelOpen] = useState(false);
  const [health, setHealth] = useState<{ healthy?: boolean } | null>(null);
  const socketRef = useRef(null);
  const toastIdRef = useRef(0);
  const notificationPanelRef = useRef<HTMLDivElement>(null);
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'history' | 'filter'>('upload');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');
  const [filterCameraId, setFilterCameraId] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filteredAlerts, setFilteredAlerts] = useState<any[]>([]);
  const [filteredLoading, setFilteredLoading] = useState(false);

  const addNotification = (type: string, severity: string, message: string, cameraId?: string, frameImages?: string[], frameStart?: number, frameEnd?: number, count?: number) => {
    const id = `n-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
    setNotifications((prev) => [
      { id, type, severity, message, timestamp: Date.now(), read: false, cameraId, frameImages, frameStart, frameEnd, count },
      ...prev.slice(0, 49),
    ]);
  };

  const markAllNotificationsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const clearNotifications = () => {
    setNotifications([]);
    setNotificationPanelOpen(false);
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notificationPanelRef.current && !notificationPanelRef.current.contains(event.target as Node)) {
        setNotificationPanelOpen(false);
      }
    }
    function handleEscape(e: KeyboardEvent) {
      if (e.key === 'Escape') setLightboxImage(null);
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

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

  const loadFilteredAlerts = async () => {
    setFilteredLoading(true);
    try {
      const params = { page: 1, limit: 100 };
      if (filterType) params.type = filterType;
      if (filterSeverity) params.severity = filterSeverity;
      if (filterCameraId) params.cameraId = filterCameraId;
      if (filterStartDate) params.startDate = new Date(filterStartDate + 'T00:00:00').toISOString();
      if (filterEndDate) params.endDate = new Date(filterEndDate + 'T23:59:59.999').toISOString();
      const res = await voshanDetectionApi.getAlerts(params);
      if (res.success && res.data?.alerts) {
        setFilteredAlerts(res.data.alerts);
      } else {
        setFilteredAlerts([]);
      }
    } catch (e) {
      addToast('error', 'HIGH', 'Failed to load filtered alerts');
      setFilteredAlerts([]);
    } finally {
      setFilteredLoading(false);
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

    socket.on('connect', () => {
      socket.emit('subscribe-alerts');
    });

    socket.on('new-alert', (data) => {
      const type = data?.type || 'Alert';
      const severity = data?.severity || 'MEDIUM';
      const cameraId = data?.cameraId ?? data?.camera_id;
      const msg = cameraId ? `New alert: ${type} (${severity}) — Camera ${cameraId}` : `New alert: ${type} (${severity})`;
      addToast(type, severity, msg);
      addNotification(type, severity, msg, cameraId);
      loadAlerts();
    });

    socket.on('grouped-alert', (data) => {
      const type = data?.type || 'Alert';
      const severity = data?.severity || 'MEDIUM';
      const cameraId = data?.cameraId ?? data?.camera_id;
      const count = data?.count ?? 0;
      const frameStart = data?.frameStart ?? 0;
      const frameEnd = data?.frameEnd ?? 0;
      const frameImages = Array.isArray(data?.frameImages) ? data.frameImages : [];
      const msg = count > 0
        ? (cameraId ? `${count}× ${type} (frames ${frameStart}–${frameEnd}) — Camera ${cameraId}` : `${count}× ${type} (frames ${frameStart}–${frameEnd})`)
        : (cameraId ? `Alert: ${type} — Camera ${cameraId}` : `Alert: ${type}`);
      addToast(type, severity, msg);
      addNotification(type, severity, msg, cameraId, frameImages, frameStart, frameEnd, count);
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
          <div className="relative" ref={notificationPanelRef}>
            <button
              type="button"
              onClick={() => setNotificationPanelOpen((o) => !o)}
              className="relative p-2 rounded-lg text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              aria-label="Notifications"
            >
              <Bell className="w-5 h-5" />
              {notifications.some((n) => !n.read) && (
                <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-amber-500 text-[10px] font-bold text-black">
                  {notifications.filter((n) => !n.read).length > 99 ? '99+' : notifications.filter((n) => !n.read).length}
                </span>
              )}
            </button>
            {notificationPanelOpen && (
              <div className="absolute right-0 top-full mt-1 w-80 max-h-[70vh] overflow-hidden rounded-xl border border-white/10 bg-[#0f0f18] shadow-xl z-50 flex flex-col">
                <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
                  <span className="font-medium text-sm">Notifications</span>
                  <div className="flex gap-1">
                    {notifications.some((n) => !n.read) && (
                      <button
                        type="button"
                        onClick={markAllNotificationsRead}
                        className="text-xs text-amber-400 hover:text-amber-300"
                      >
                        Mark read
                      </button>
                    )}
                    {notifications.length > 0 && (
                      <>
                        <span className="text-white/30">·</span>
                        <button type="button" onClick={clearNotifications} className="text-xs text-slate-400 hover:text-white">
                          Clear
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <ul className="overflow-y-auto flex-1">
                  {notifications.length === 0 ? (
                    <li className="px-4 py-6 text-center text-sm text-slate-500">No notifications yet</li>
                  ) : (
                    notifications.map((n) => (
                      <li
                        key={n.id}
                        className={`px-4 py-3 border-b border-white/5 last:border-0 ${n.read ? 'opacity-70' : 'bg-amber-500/5'}`}
                      >
                        <p className="font-medium text-sm">{n.type}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{n.message}</p>
                        {n.frameImages && n.frameImages.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {n.frameImages.slice(0, 6).map((fn, i) => {
                              const src = `${voshanDetectionApi.baseUrl}/voshan/detection/alert-frames/${fn}`;
                              return (
                                <button key={i} type="button" onClick={() => setLightboxImage(src)} className="rounded overflow-hidden focus:ring-2 ring-amber-400">
                                  <img src={src} alt="" className="w-12 h-9 object-cover bg-black/20" />
                                </button>
                              );
                            })}
                            {n.frameImages.length > 6 && (
                              <span className="text-[10px] text-slate-500 self-center">+{n.frameImages.length - 6}</span>
                            )}
                          </div>
                        )}
                        <p className="text-[10px] text-slate-500 mt-1">
                          {new Date(n.timestamp).toLocaleTimeString()}
                          {n.cameraId ? ` · ${n.cameraId}` : ''}
                        </p>
                        <span
                          className={`inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded ${
                            n.severity === 'HIGH' ? 'bg-red-500/20 text-red-300' : 'bg-amber-500/20 text-amber-300'
                          }`}
                        >
                          {n.severity}
                        </span>
                      </li>
                    ))
                  )}
                </ul>
              </div>
            )}
          </div>
          <span className="text-sm text-slate-400 hidden sm:block">{displayName}</span>
          <button
            onClick={onSignOut}
            className="px-3 py-1.5 text-sm rounded-lg bg-white/10 hover:bg-white/20"
          >
            Sign out
          </button>
        </div>
      </header>

      {lightboxImage && (
        <div
          className="fixed inset-0 z-[100] bg-black/80 flex items-center justify-center p-4"
          onClick={() => setLightboxImage(null)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Escape' && setLightboxImage(null)}
          aria-label="Close"
        >
          <img
            src={lightboxImage}
            alt="Alert frame"
            className="max-w-full max-h-[90vh] object-contain rounded"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

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
        {health && (
          <div className="flex items-center gap-2 text-sm">
            <span className={health.healthy ? 'text-green-400' : 'text-red-400'}>
              {health.healthy ? '● ML service connected' : '○ ML service unavailable'}
            </span>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 p-1 rounded-xl bg-white/5 border border-white/10 w-fit">
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === 'upload' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            <Upload className="w-4 h-4 inline-block mr-2 align-middle" /> Upload
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('history')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === 'history' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            <History className="w-4 h-4 inline-block mr-2 align-middle" /> Alert history
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('filter')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${activeTab === 'filter' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
          >
            <Filter className="w-4 h-4 inline-block mr-2 align-middle" /> Filter
          </button>
        </div>

        {activeTab === 'upload' && (
          <>
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
          </>
        )}

        {activeTab === 'history' && (
          <>
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
            (() => {
              const groups = groupAlertsByWindow(alerts);
              return (
            <ul className="space-y-4">
              {groups.map((grp, idx) => {
                const frameUrls = grp.alerts.map((a) => getAlertFrameUrl(a)).filter(Boolean) as string[];
                const firstTs = grp.alerts[0]?.timestamp;
                const tsStr = firstTs != null
                  ? new Date(typeof firstTs === 'number' ? firstTs * 1000 : firstTs).toLocaleString()
                  : '—';
                return (
                  <li key={`${grp.frameStart}-${grp.type}-${idx}`} className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="font-medium">{grp.count}× {grp.type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        grp.severity === 'HIGH' ? 'bg-red-500/20 text-red-300' :
                        grp.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-500/20 text-slate-300'
                      }`}>
                        {grp.severity}
                      </span>
                      <span className="text-xs text-slate-400">Frames {grp.frameStart}–{grp.frameEnd}</span>
                      {grp.cameraId && <span className="text-xs text-slate-400">{grp.cameraId}</span>}
                    </div>
                    <p className="text-xs text-slate-400 mb-2">{tsStr}</p>
                    {frameUrls.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {frameUrls.map((src, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setLightboxImage(src)}
                            className="rounded-lg overflow-hidden focus:ring-2 ring-amber-400 flex-shrink-0"
                          >
                            <img src={src} alt="" className="w-32 h-24 object-cover bg-black/20 hover:opacity-90 transition-opacity" />
                          </button>
                        ))}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
              );
            })()
          )}
            </section>
          </>
        )}

        {activeTab === 'filter' && (
          <>
            <section className="rounded-2xl border border-white/10 bg-white/5 p-6">
          <h2 className="flex items-center gap-2 text-lg font-semibold mb-4">
            <Filter className="w-5 h-5" /> Filter suspicious behavior
          </h2>
          <div className="flex flex-wrap gap-4 items-end mb-6">
            <label className="flex flex-col gap-1">
              <span className="text-slate-400 text-xs">From date</span>
              <input
                type="date"
                value={filterStartDate}
                onChange={(e) => setFilterStartDate(e.target.value)}
                className="bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-slate-400 text-xs">To date</span>
              <input
                type="date"
                value={filterEndDate}
                onChange={(e) => setFilterEndDate(e.target.value)}
                className="bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-slate-400 text-xs">Camera</span>
              <input
                type="text"
                value={filterCameraId}
                onChange={(e) => setFilterCameraId(e.target.value)}
                placeholder="Any"
                className="bg-white/5 border border-white/10 rounded px-3 py-2 text-sm w-28"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-slate-400 text-xs">Category</span>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="bg-[#1a1a2e] text-white border border-white/10 rounded px-3 py-2 text-sm [color-scheme:dark]"
              >
                <option value="">All</option>
                <option value="RUNNING">RUNNING</option>
                <option value="LOITERING">LOITERING</option>
                <option value="LOITER_NEAR_UNATTENDED">LOITER_NEAR_UNATTENDED</option>
                <option value="BAG_UNATTENDED">BAG_UNATTENDED</option>
                <option value="OWNER_RETURNED">OWNER_RETURNED</option>
              </select>
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-slate-400 text-xs">Severity</span>
              <select
                value={filterSeverity}
                onChange={(e) => setFilterSeverity(e.target.value)}
                className="bg-[#1a1a2e] text-white border border-white/10 rounded px-3 py-2 text-sm [color-scheme:dark]"
              >
                <option value="">All</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
              </select>
            </label>
            <button
              type="button"
              onClick={loadFilteredAlerts}
              disabled={filteredLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-sm font-medium"
            >
              {filteredLoading ? 'Searching…' : 'Search'}
            </button>
          </div>
          {filteredLoading ? (
            <p className="text-slate-400 text-sm">Loading…</p>
          ) : filteredAlerts.length === 0 ? (
            <p className="text-slate-400 text-sm">No results. Set filters and click Search, or no alerts match.</p>
          ) : (
            <ul className="space-y-4">
              {groupAlertsByWindow(filteredAlerts).map((grp, idx) => {
                const frameUrls = grp.alerts.map((a) => getAlertFrameUrl(a)).filter(Boolean) as string[];
                const firstTs = grp.alerts[0]?.timestamp;
                const tsStr = firstTs != null
                  ? new Date(typeof firstTs === 'number' ? firstTs * 1000 : firstTs).toLocaleString()
                  : '—';
                return (
                  <li key={`f-${grp.frameStart}-${grp.type}-${idx}`} className="rounded-xl border border-white/10 bg-white/5 p-4">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <span className="font-medium">{grp.count}× {grp.type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        grp.severity === 'HIGH' ? 'bg-red-500/20 text-red-300' :
                        grp.severity === 'MEDIUM' ? 'bg-amber-500/20 text-amber-300' : 'bg-slate-500/20 text-slate-300'
                      }`}>
                        {grp.severity}
                      </span>
                      <span className="text-xs text-slate-400">Frames {grp.frameStart}–{grp.frameEnd}</span>
                      {grp.cameraId && <span className="text-xs text-slate-400">{grp.cameraId}</span>}
                    </div>
                    <p className="text-xs text-slate-400 mb-2">{tsStr}</p>
                    {frameUrls.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {frameUrls.map((src, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setLightboxImage(src)}
                            className="rounded-lg overflow-hidden focus:ring-2 ring-amber-400 flex-shrink-0"
                          >
                            <img src={src} alt="" className="w-32 h-24 object-cover bg-black/20 hover:opacity-90 transition-opacity" />
                          </button>
                        ))}
                      </div>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
