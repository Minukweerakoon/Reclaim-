/**
 * Alert persistence using Supabase (sus_alerts table).
 * Returns alerts in the same shape as the API (camelCase + _id) so the frontend is unchanged.
 */

const { getSupabase } = require('../../config/supabase');

const TABLE = 'sus_alerts';

/** Map DB row (snake_case) to API shape (camelCase + _id) */
function toAlert(row) {
  if (!row) return null;
  const a = {
    _id: row.id,
    id: row.id,
    alertId: row.alert_id,
    type: row.type,
    severity: row.severity,
    timestamp: row.timestamp,
    frame: row.frame,
    cameraId: row.camera_id ?? null,
    details: row.details ?? {},
    snapshot: row.snapshot ?? null,
    frameImage: row.frame_image ?? null,
    frame_image: row.frame_image ?? null,
    videoInfo: row.video_info ?? null,
    acknowledged: row.acknowledged ?? false,
    acknowledgedAt: row.acknowledged_at ?? null,
    acknowledgedBy: row.acknowledged_by ?? null,
    createdAt: row.created_at ?? null,
    updatedAt: row.updated_at ?? null
  };
  return a;
}

/** Map payload to DB columns (snake_case) */
function toRow(alert, extra = {}) {
  const ts = alert.timestamp instanceof Date ? alert.timestamp : new Date((alert.timestamp || 0) * 1000);
  return {
    alert_id: alert.alert_id ?? alert.alertId,
    type: alert.type,
    severity: alert.severity,
    timestamp: ts.toISOString(),
    frame: alert.frame ?? 0,
    camera_id: alert.cameraId ?? alert.camera_id ?? null,
    details: alert.details ?? {},
    snapshot: alert.snapshot ?? null,
    frame_image: alert.frame_image ?? alert.frameImage ?? null,
    video_info: alert.video_info ?? alert.videoInfo ?? null,
    acknowledged: alert.acknowledged ?? false,
    acknowledged_at: alert.acknowledgedAt ?? alert.acknowledged_at ?? null,
    acknowledged_by: alert.acknowledgedBy ?? alert.acknowledged_by ?? null,
    ...extra
  };
}

async function insert(alert) {
  const supabase = getSupabase();
  if (!supabase) throw new Error('Supabase not configured');
  const row = toRow(alert);
  const { data, error } = await supabase.from(TABLE).insert(row).select('*').single();
  if (error) throw error;
  return toAlert(data);
}

async function findMany({ type, severity, cameraId, startDate, endDate, page = 1, limit = 50 } = {}) {
  const supabase = getSupabase();
  if (!supabase) throw new Error('Supabase not configured');
  let q = supabase.from(TABLE).select('*', { count: 'exact' }).order('timestamp', { ascending: false });
  if (type) q = q.eq('type', type);
  if (severity) q = q.eq('severity', severity);
  if (cameraId) q = q.eq('camera_id', cameraId);
  if (startDate) q = q.gte('timestamp', new Date(startDate).toISOString());
  if (endDate) q = q.lte('timestamp', new Date(endDate).toISOString());
  const skip = (parseInt(page) - 1) * parseInt(limit);
  q = q.range(skip, skip + parseInt(limit) - 1);
  const { data, error, count } = await q;
  if (error) throw error;
  return { alerts: (data || []).map(toAlert), total: count ?? 0 };
}

async function findByCamera(cameraId, { type, severity, page = 1, limit = 50 } = {}) {
  return findMany({ cameraId, type, severity, page, limit });
}

async function findById(id) {
  const supabase = getSupabase();
  if (!supabase) throw new Error('Supabase not configured');
  const { data, error } = await supabase.from(TABLE).select('*').eq('id', id).single();
  if (error) {
    if (error.code === 'PGRST116') return null; // not found
    throw error;
  }
  return toAlert(data);
}

async function deleteById(id) {
  const supabase = getSupabase();
  if (!supabase) throw new Error('Supabase not configured');
  const { data, error } = await supabase.from(TABLE).delete().eq('id', id).select('id').single();
  if (error) throw error;
  return data != null;
}

module.exports = { insert, findMany, findByCamera, findById, deleteById, toAlert };
