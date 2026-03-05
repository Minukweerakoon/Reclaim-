/**
 * Voshan detection API client for admin dashboard.
 * Base URL: VITE_VOSHAN_API_URL or /api (same-origin proxy to Node backend on 5000).
 */

const BASE = (import.meta.env.VITE_VOSHAN_API_URL as string) || '/api';

export const voshanDetectionApi = {
  baseUrl: BASE,

  async health() {
    const res = await fetch(`${BASE}/voshan/detection/health`);
    return res.json();
  },

  async processVideo(file: File, options: { cameraId?: string; saveOutput?: boolean } = {}, onProgress?: (p: number) => void) {
    const form = new FormData();
    form.append('video', file);
    if (options.cameraId) form.append('cameraId', options.cameraId);
    form.append('saveOutput', String(options.saveOutput ?? true));

    const xhr = new XMLHttpRequest();
    return new Promise<{ success: boolean; data?: any; message?: string; error?: string }>((resolve, reject) => {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
      });
      xhr.addEventListener('load', () => {
        try {
          const data = JSON.parse(xhr.responseText || '{}');
          resolve(data);
        } catch {
          resolve({ success: false, error: 'Invalid response' });
        }
      });
      xhr.addEventListener('error', () => reject(new Error('Network error')));
      xhr.open('POST', `${BASE}/voshan/detection/process-video`);
      xhr.send(form);
    });
  },

  async getAlerts(params: { page?: number; limit?: number; type?: string; severity?: string; cameraId?: string } = {}) {
    const sp = new URLSearchParams();
    if (params.page != null) sp.set('page', String(params.page));
    if (params.limit != null) sp.set('limit', String(params.limit));
    if (params.type) sp.set('type', params.type);
    if (params.severity) sp.set('severity', params.severity);
    if (params.cameraId) sp.set('cameraId', params.cameraId);
    const res = await fetch(`${BASE}/voshan/detection/alerts?${sp}`);
    return res.json();
  },
};

/** WebSocket URL for Voshan alerts (Socket.IO). */
export function getVoshanWsUrl(): string {
  const base = import.meta.env.VITE_VOSHAN_API_URL as string;
  if (base && base.startsWith('http')) {
    const u = new URL(base);
    return `${u.protocol === 'https:' ? 'wss:' : 'ws:'}//${u.host}`;
  }
  return `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}`;
}
