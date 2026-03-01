r"""
Debug script: run detection on a video and print per-frame stats.
Use this to see if the model detects any person/bag in your video.

Usage (from backend/voshan/ml-service):
  python debug_detect_video.py "C:\path\to\your\video.mp4"

Optional: add --confidence 0.1 to lower threshold, --save-frames to save first 5 annotated frames.
"""

import os
import sys
import argparse
import yaml
import cv2
import numpy as np

# Add parent so we can import services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="Debug detection on a video")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--confidence", type=float, default=None, help="Confidence threshold (default: from config, or 0.15)")
    parser.add_argument("--max-frames", type=int, default=100, help="Max frames to sample (default 100, 0 = all)")
    parser.add_argument("--sample-every", type=int, default=1, help="Run detection every N frames (default 1)")
    parser.add_argument("--save-frames", action="store_true", help="Save first 5 annotated frames to debug_output/")
    args = parser.parse_args()

    video_path = os.path.abspath(args.video_path)
    if not os.path.exists(video_path):
        print(f"ERROR: Video not found: {video_path}")
        sys.exit(1)

    # Load config
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    conf = args.confidence if args.confidence is not None else config.get("model", {}).get("confidence", 0.25)
    if args.confidence is None and conf > 0.2:
        conf = 0.15
    print(f"Using confidence threshold: {conf}")

    from services.detector import YOLODetector

    model_path = os.path.join(os.path.dirname(__file__), config["model"]["path"])
    if not os.path.exists(model_path):
        print(f"ERROR: Model not found: {model_path}")
        sys.exit(1)

    detector = YOLODetector(
        model_path=model_path,
        image_size=config["model"]["image_size"],
        confidence=conf,
        device=config["model"]["device"],
    )
    print(f"Model classes: {detector.model.names}")
    print()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        sys.exit(1)

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Video: {total_frames} frames, {fps} fps, {w}x{h}")
    print()

    save_dir = None
    if args.save_frames:
        save_dir = os.path.join(os.path.dirname(__file__), "debug_output")
        os.makedirs(save_dir, exist_ok=True)
        print(f"Saving annotated frames to: {save_dir}")
        print()

    frame_idx = 0
    saved_count = 0
    total_dets = 0
    by_class = {}
    max_frames = args.max_frames if args.max_frames > 0 else total_frames

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % args.sample_every != 0:
            frame_idx += 1
            continue

        detections = detector.detect(frame)
        n = len(detections)
        total_dets += n

        for d in detections:
            cls = d.get("class_name", "?")
            by_class[cls] = by_class.get(cls, 0) + 1

        if n > 0 and saved_count < 5 and save_dir:
            out = frame.copy()
            for d in detections:
                bbox = d["bbox"]
                x1, y1, x2, y2 = map(int, bbox)
                cls = d.get("class_name", "?")
                c = d.get("confidence", 0)
                cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(out, f"{cls} {c:.2f}", (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            path = os.path.join(save_dir, f"frame_{frame_idx:05d}.jpg")
            cv2.imwrite(path, out)
            print(f"  Saved {path} ({n} detections)")
            saved_count += 1

        if frame_idx % 100 == 0 or (args.max_frames <= 200 and frame_idx % 20 == 0):
            print(f"  Frame {frame_idx}: {n} detections (cumulative: {total_dets})")

        frame_idx += 1

    cap.release()

    print()
    print("--- Summary ---")
    print(f"Frames sampled: {frame_idx}")
    print(f"Total detections: {total_dets}")
    print(f"By class: {by_class}")
    if total_dets == 0:
        print()
        print("No detections. Try:")
        print("  1. Lower confidence: python debug_detect_video.py \"<video>\" --confidence 0.1")
        print("  2. Lower model confidence in config.yaml (e.g. confidence: 0.15) and restart ML service")
        print("  3. If your video has people/bags but model was trained on different data, the model may not generalize.")
        print("  4. Enable COCO extension in config.yaml (coco_extension.enabled: true) to add COCO person/backpack/handbag.")
    else:
        print()
        print("Detections found. If the app still shows 0, restart the ML service so it uses the same config.")

if __name__ == "__main__":
    main()
