import { z, type ZodError } from 'zod';

const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH'] as const;
export type VoshanSeverity = (typeof SEVERITIES)[number];

const MAX_CAMERA_ID_LEN = 128;
const MAX_FRAME_FILENAME_LEN = 255;

/** Reject path segments / traversal; allow any other single-segment filename the ML service emits. */
export function sanitizeFrameImageFilename(name: unknown): string | null {
  if (typeof name !== 'string') return null;
  const t = name.trim();
  if (t.length === 0 || t.length > MAX_FRAME_FILENAME_LEN) return null;
  if (t.includes('..') || t.includes('/') || t.includes('\\')) return null;
  if (/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(t)) return null;
  return t;
}

/** Match pre-validation UI: any reasonable label, but block path/control characters. */
function normalizeCameraId(v: unknown): string | undefined {
  if (v === null || v === undefined) return undefined;
  let s: string;
  if (typeof v === 'string') s = v.trim();
  else if (typeof v === 'number' && Number.isFinite(v)) s = String(v);
  else if (typeof v === 'boolean') s = v ? 'true' : 'false';
  else return undefined;
  if (s.length === 0 || s.length > MAX_CAMERA_ID_LEN) return undefined;
  if (/[\r\n\0\u2028\u2029]/.test(s)) return undefined;
  if (/[\\/]/.test(s)) return undefined;
  return s;
}

/** Treat null / primitives / arrays like optional-chaining did: use defaults, do not reject the event. */
function asPlainObject(data: unknown): Record<string, unknown> {
  if (data !== null && typeof data === 'object' && !Array.isArray(data)) {
    return data as Record<string, unknown>;
  }
  return {};
}

function coerceSeverity(v: unknown): VoshanSeverity {
  if (typeof v === 'string' && (SEVERITIES as readonly string[]).includes(v)) {
    return v as VoshanSeverity;
  }
  return 'MEDIUM';
}

function coerceAlertType(v: unknown): string {
  if (typeof v !== 'string' || !v.trim()) return 'Alert';
  const t = v.trim();
  return t.length > 96 ? t.slice(0, 96) : t;
}

function coerceNonNegInt(v: unknown, fallback: number): number {
  if (typeof v === 'number' && Number.isFinite(v) && v >= 0) return Math.min(Math.floor(v), 1_000_000_000);
  if (typeof v === 'string' && v.trim() !== '') {
    const n = Number(v);
    if (Number.isFinite(n) && n >= 0) return Math.min(Math.floor(n), 1_000_000_000);
  }
  return fallback;
}

const detailsSchema = z.record(z.string(), z.unknown()).optional();

/** Validates shape before normalization (unknown keys stripped). */
export const newAlertPayloadSchema = z
  .object({
    alertId: z.union([z.string(), z.number()]).optional(),
    type: z.unknown().optional(),
    severity: z.unknown().optional(),
    cameraId: z.unknown().optional(),
    camera_id: z.unknown().optional(),
    timestamp: z.unknown().optional(),
    frame: z.unknown().optional(),
    details: z.unknown().optional(),
    frame_image: z.unknown().optional(),
  })
  .strip();

export type ParsedNewAlertPayload = {
  alertId?: string;
  type: string;
  severity: VoshanSeverity;
  cameraId?: string;
  timestamp?: unknown;
  frame?: unknown;
  details?: Record<string, unknown>;
  frame_image?: string;
};

export function parseNewAlertPayload(data: unknown):
  | { success: true; value: ParsedNewAlertPayload }
  | { success: false; error: ZodError } {
  const base = newAlertPayloadSchema.safeParse(asPlainObject(data));
  if (!base.success) return { success: false, error: base.error };

  const o = base.data;
  const cameraId = normalizeCameraId(o.cameraId ?? o.camera_id);
  let details: Record<string, unknown> | undefined;
  const dParsed = detailsSchema.safeParse(o.details);
  if (dParsed.success && dParsed.data) details = dParsed.data;

  let frame_image: string | undefined;
  if (o.frame_image !== undefined && o.frame_image !== null) {
    const s = sanitizeFrameImageFilename(o.frame_image);
    if (s) frame_image = s;
  }

  let alertId: string | undefined;
  if (o.alertId !== undefined && o.alertId !== null) {
    alertId = typeof o.alertId === 'number' && Number.isFinite(o.alertId) ? String(o.alertId) : typeof o.alertId === 'string' ? o.alertId.trim().slice(0, 128) : undefined;
    if (alertId === '') alertId = undefined;
  }

  return {
    success: true,
    value: {
      alertId,
      type: coerceAlertType(o.type),
      severity: coerceSeverity(o.severity),
      cameraId,
      timestamp: o.timestamp,
      frame: o.frame,
      details,
      frame_image,
    },
  };
}

export const groupedAlertPayloadSchema = z
  .object({
    type: z.unknown().optional(),
    severity: z.unknown().optional(),
    cameraId: z.unknown().optional(),
    camera_id: z.unknown().optional(),
    count: z.unknown().optional(),
    frameStart: z.unknown().optional(),
    frameEnd: z.unknown().optional(),
    itemType: z.unknown().optional(),
    item_type: z.unknown().optional(),
    frameImages: z.unknown().optional(),
  })
  .strip();

function coerceItemType(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  if (typeof v !== 'string') return null;
  const t = v.trim();
  if (!t) return null;
  return t.length > 64 ? t.slice(0, 64) : t;
}

export type ParsedGroupedAlertPayload = {
  type: string;
  severity: VoshanSeverity;
  cameraId?: string;
  count: number;
  frameStart: number;
  frameEnd: number;
  itemType: string | null;
  frameImages: string[];
};

export function parseGroupedAlertPayload(data: unknown):
  | { success: true; value: ParsedGroupedAlertPayload }
  | { success: false; error: ZodError } {
  const base = groupedAlertPayloadSchema.safeParse(asPlainObject(data));
  if (!base.success) return { success: false, error: base.error };

  const o = base.data;
  const cameraId = normalizeCameraId(o.cameraId ?? o.camera_id);
  const rawImages = Array.isArray(o.frameImages) ? o.frameImages : [];
  const frameImages = rawImages.map(sanitizeFrameImageFilename).filter((x): x is string => x !== null);

  const itemType = coerceItemType(o.itemType ?? o.item_type);

  return {
    success: true,
    value: {
      type: coerceAlertType(o.type),
      severity: coerceSeverity(o.severity),
      cameraId,
      count: coerceNonNegInt(o.count, 0),
      frameStart: coerceNonNegInt(o.frameStart, 0),
      frameEnd: coerceNonNegInt(o.frameEnd, 0),
      itemType,
      frameImages,
    },
  };
}
