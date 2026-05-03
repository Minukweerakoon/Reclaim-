import { describe, expect, it } from 'vitest';
import {
  parseGroupedAlertPayload,
  parseNewAlertPayload,
  sanitizeFrameImageFilename,
} from './voshanSocket';

describe('sanitizeFrameImageFilename', () => {
  it('accepts safe basenames', () => {
    expect(sanitizeFrameImageFilename('alert_1.jpg')).toBe('alert_1.jpg');
  });

  it('rejects path traversal and slashes', () => {
    expect(sanitizeFrameImageFilename('../etc/passwd')).toBeNull();
    expect(sanitizeFrameImageFilename('a/b.png')).toBeNull();
    expect(sanitizeFrameImageFilename('..\\x')).toBeNull();
  });

  it('allows spaces and punctuation like ML frame filenames with raw camera_id', () => {
    expect(sanitizeFrameImageFilename('frame_store #1_1730000000000_f0_n0_BAG_UNATTENDED.jpg')).toBe(
      'frame_store #1_1730000000000_f0_n0_BAG_UNATTENDED.jpg',
    );
  });

  it('rejects non-strings', () => {
    expect(sanitizeFrameImageFilename(null)).toBeNull();
    expect(sanitizeFrameImageFilename(123)).toBeNull();
  });
});

describe('parseNewAlertPayload', () => {
  it('accepts a minimal valid object', () => {
    const r = parseNewAlertPayload({ type: 'BAG_UNATTENDED', severity: 'HIGH' });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.value.type).toBe('BAG_UNATTENDED');
      expect(r.value.severity).toBe('HIGH');
      expect(r.value.cameraId).toBeUndefined();
    }
  });

  it('treats null and non-objects like empty payloads (same as optional chaining)', () => {
    const n = parseNewAlertPayload(null);
    expect(n.success).toBe(true);
    if (n.success) {
      expect(n.value.type).toBe('Alert');
      expect(n.value.severity).toBe('MEDIUM');
    }
    const s = parseNewAlertPayload('ignored');
    expect(s.success).toBe(true);
    if (s.success) expect(s.value.type).toBe('Alert');
    const arr = parseNewAlertPayload([1, 2]);
    expect(arr.success).toBe(true);
  });

  it('drops cameraId with path separators; coerces unknown severity', () => {
    const r = parseNewAlertPayload({
      type: 'RUNNING',
      severity: 'CRITICAL',
      cameraId: 'zone/a',
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.value.cameraId).toBeUndefined();
      expect(r.value.severity).toBe('MEDIUM');
    }
  });

  it('preserves cameraId with dots and spaces (labels match previous UI)', () => {
    const r = parseNewAlertPayload({ type: 'X', cameraId: '  Front door  ' });
    expect(r.success).toBe(true);
    if (r.success) expect(r.value.cameraId).toBe('Front door');
  });

  it('stringifies numeric cameraId like template strings did', () => {
    const r = parseNewAlertPayload({ cameraId: 12 });
    expect(r.success).toBe(true);
    if (r.success) expect(r.value.cameraId).toBe('12');
  });

  it('sanitizes frame_image', () => {
    const r = parseNewAlertPayload({
      type: 'X',
      frame_image: 'ok.png',
    });
    expect(r.success).toBe(true);
    if (r.success) expect(r.value.frame_image).toBe('ok.png');
  });

  it('omits unsafe frame_image', () => {
    const r = parseNewAlertPayload({
      type: 'X',
      frame_image: '../../../x',
    });
    expect(r.success).toBe(true);
    if (r.success) expect(r.value.frame_image).toBeUndefined();
  });
});

describe('parseGroupedAlertPayload', () => {
  it('filters frameImages to safe names only', () => {
    const r = parseGroupedAlertPayload({
      type: 'LOITER',
      count: 2,
      frameStart: 0,
      frameEnd: 49,
      frameImages: ['a.png', '../../../evil', 'b.jpg'],
    });
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.value.frameImages).toEqual(['a.png', 'b.jpg']);
    }
  });

  it('treats undefined like empty payload (defaults)', () => {
    const r = parseGroupedAlertPayload(undefined);
    expect(r.success).toBe(true);
    if (r.success) {
      expect(r.value.type).toBe('Alert');
      expect(r.value.frameImages).toEqual([]);
    }
  });

  it('normalizes itemType from item_type', () => {
    const r = parseGroupedAlertPayload({
      type: 'T',
      item_type: 'hand_bag',
    });
    expect(r.success).toBe(true);
    if (r.success) expect(r.value.itemType).toBe('hand_bag');
  });
});
