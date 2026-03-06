/**
 * Supabase client for backend (service_role key).
 * Use for alerts table (sus_alerts). Bypasses RLS.
 */

let client = null;

function getSupabase() {
  return client;
}

async function initSupabase() {
  const url = process.env.SUPABASE_URL?.trim();
  const key = process.env.SUPABASE_SERVICE_ROLE_KEY?.trim();
  if (!url || !key) {
    return null;
  }
  try {
    const { createClient } = require('@supabase/supabase-js');
    client = createClient(url, key);
    // Quick check: list one row to verify connection
    const { error } = await client.from('sus_alerts').select('id').limit(1);
    if (error) {
      console.warn('⚠️  Supabase table sus_alerts may not exist or RLS blocked:', error.message);
    }
    console.log('✅ Supabase connected');
    return client;
  } catch (err) {
    console.error('❌ Supabase init error:', err.message);
    client = null;
    return null;
  }
}

module.exports = { getSupabase, initSupabase };
