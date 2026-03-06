/**
 * Admin user check for Reclaim/Voshan admin dashboard.
 * Only the user with this email can access the admin dashboard.
 */

const ADMIN_EMAIL = 'voshan1996@gmail.com';

function getAdminEmail(): string {
  return (import.meta.env.VITE_ADMIN_EMAIL as string) || ADMIN_EMAIL;
}

/**
 * Returns true if the given user is the allowed admin (by email).
 */
export function isAdminUser(user: { email?: string } | null): boolean {
  if (!user?.email) return false;
  const adminEmail = getAdminEmail().trim().toLowerCase();
  return user.email.trim().toLowerCase() === adminEmail;
}

export { getAdminEmail };
