/**
 * Upload alert clip (and optionally frame image) to Supabase Storage and return public URL.
 * Used so clips are stored in Supabase instead of only on disk.
 */

const fs = require('fs');
const path = require('path');
const { getSupabase } = require('../../config/supabase');

const BUCKET_CLIPS = 'alert-clips';
const BUCKET_FRAMES = 'alert-frames';

/**
 * Ensure the Storage bucket exists (create if not). Call once at startup or first use.
 * Bucket is created as public so getPublicUrl works for alert clips.
 */
async function ensureBucket(bucketName, options = { public: true }) {
  const supabase = getSupabase();
  if (!supabase) return false;
  const { error } = await supabase.storage.getBucket(bucketName);
  if (error) {
    const notFound = error.message && (error.message.includes('not found') || error.message.includes('Bucket'));
    if (notFound) {
      const { error: createErr } = await supabase.storage.createBucket(bucketName, options);
      if (createErr) {
        console.warn(`[Supabase Storage] Could not create bucket ${bucketName}:`, createErr.message);
        return false;
      }
      console.log(`[Supabase Storage] Created bucket: ${bucketName}`);
    } else {
      console.warn(`[Supabase Storage] getBucket ${bucketName}:`, error.message);
      return false;
    }
  }
  return true;
}

/**
 * Upload a file from local path to Supabase Storage and return the public URL.
 * @param {string} localFilePath - Full path to the file on disk
 * @param {string} storagePath - Path inside the bucket (e.g. 'abc_f123_n0_RUNNING.mp4')
 * @param {string} bucket - Bucket name (default: alert-clips)
 * @returns {Promise<string|null>} Public URL or null on failure
 */
async function uploadFileAndGetPublicUrl(localFilePath, storagePath, bucket = BUCKET_CLIPS) {
  const supabase = getSupabase();
  if (!supabase) return null;
  if (!localFilePath || !fs.existsSync(localFilePath)) return null;
  try {
    const fileBuffer = fs.readFileSync(localFilePath);
    const { data, error } = await supabase.storage
      .from(bucket)
      .upload(storagePath, fileBuffer, {
        contentType: bucket === BUCKET_CLIPS ? 'video/mp4' : 'image/jpeg',
        upsert: true,
      });
    if (error) {
      console.warn(`[Supabase Storage] upload failed for ${storagePath}:`, error.message);
      return null;
    }
    const { data: urlData } = supabase.storage.from(bucket).getPublicUrl(data.path);
    return urlData?.publicUrl || null;
  } catch (err) {
    console.warn('[Supabase Storage] upload error:', err.message);
    return null;
  }
}

/**
 * Upload alert clip from local disk to Supabase Storage.
 * @param {string} clipFilename - Filename only (e.g. video_xxx_f66_n0_RUNNING.mp4)
 * @param {string} alertClipsDir - Full path to directory where the file lives
 * @returns {Promise<string|null>} Public URL or null (keep using filename for static serve on failure)
 */
async function uploadAlertClip(clipFilename, alertClipsDir) {
  if (!clipFilename || typeof clipFilename !== 'string') return null;
  const safeName = path.basename(clipFilename);
  if (!safeName) return null;
  const localPath = path.join(alertClipsDir, safeName);
  const url = await uploadFileAndGetPublicUrl(localPath, safeName, BUCKET_CLIPS);
  return url;
}

module.exports = { ensureBucket, uploadFileAndGetPublicUrl, uploadAlertClip, BUCKET_CLIPS, BUCKET_FRAMES };
