/**
 * Inbox for the public “missing item at a venue” contact form (mailto).
 * Override with `VITE_ADMIN_CONTACT_EMAIL` in the frontend environment if needed.
 */
const DEFAULT_ADMIN_CONTACT_EMAIL = 'reclaim703@gmail.com';

export function getAdminContactEmail(): string {
  const raw = (import.meta.env.VITE_ADMIN_CONTACT_EMAIL as string | undefined)?.trim();
  return raw || DEFAULT_ADMIN_CONTACT_EMAIL;
}
