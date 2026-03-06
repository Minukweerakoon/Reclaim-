/**
 * Database connection: Supabase only (alerts in sus_alerts table).
 * Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Voshan/.env.
 */

const { initSupabase } = require('./supabase');

const connectDB = async () => {
  if (!process.env.SUPABASE_URL?.trim() || !process.env.SUPABASE_SERVICE_ROLE_KEY?.trim()) {
    console.warn('⚠️  Supabase not configured: set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in Voshan/.env');
    console.warn('   Server will start but alert storage will fail until configured.');
    return;
  }
  await initSupabase();
};

module.exports = connectDB;
