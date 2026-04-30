/**
 * Admin user check for Reclaim/Voshan admin dashboard.
 * Checks Supabase user metadata/app metadata for admin authorization.
 */

/**
 * Returns true when the logged-in user is marked as admin in Supabase.
 */
export function isAdminUser(user: { email?: string; user_metadata?: Record<string, any>; app_metadata?: Record<string, any> } | null): boolean {
  if (!user) return false;
  
  // Prefer Supabase metadata checks from the currently logged-in user.
  // Support both boolean `admin` and string `role` formats.
  const userMetadata = user.user_metadata || {};
  const appMetadata = user.app_metadata || {};
  const adminValue = userMetadata.admin ?? appMetadata.admin;
  const roleValue = userMetadata.role ?? appMetadata.role;

  if (adminValue === true || adminValue === 'true') {
    return true;
  }

  if (typeof roleValue === 'string' && roleValue.trim().toLowerCase() === 'admin') {
    return true;
  }

  return false;
}
