// In production, default to same-origin so Vercel rewrites can proxy backend calls.
const DEFAULT_API_ORIGIN = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';

const rawApiOrigin = ((import.meta.env.VITE_API_BASE_URL as string) || '').trim();
const normalizedApiOrigin = rawApiOrigin.replace(/\/$/, '');
const isHttpsPage = typeof window !== 'undefined' && window.location.protocol === 'https:';
const isMixedContentTarget = isHttpsPage && normalizedApiOrigin.startsWith('http://');

if (isMixedContentTarget) {
	console.warn('[API] Ignoring insecure VITE_API_BASE_URL on HTTPS page:', normalizedApiOrigin);
}

export const apiOrigin = isMixedContentTarget
	? DEFAULT_API_ORIGIN
	: (normalizedApiOrigin || DEFAULT_API_ORIGIN);
export const apiBaseUrl = `${apiOrigin}/api`;