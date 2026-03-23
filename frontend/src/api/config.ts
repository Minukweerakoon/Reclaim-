// In production, default to same-origin so Vercel rewrites can proxy backend calls.
const DEFAULT_API_ORIGIN = import.meta.env.DEV ? 'http://127.0.0.1:8000' : '';

export const apiOrigin = (import.meta.env.VITE_API_BASE_URL as string) || DEFAULT_API_ORIGIN;
export const apiBaseUrl = `${apiOrigin}/api`;