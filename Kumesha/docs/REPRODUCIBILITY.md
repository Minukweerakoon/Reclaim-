# Reproducibility Guide

This document captures the minimum steps and expectations to reproduce the
core research results for this project.

## 1) Environment

- Python 3.10+
- CPU or CUDA-capable GPU
- Dependencies from `requirements.txt`

Optional but recommended:
- CUDA-enabled PyTorch for training and CLIP/Whisper acceleration

## 2) Dataset Expectations

The training pipeline expects a directory structure like:

```
Balanced_Dataset/
  card/
  headphone/
  key/
  keyboard/
  laptop_charger/
  laptop/
  mouse/
  phone/
  unknown/
  wallet/
  backpack/
```

The included training script uses a deterministic split (70/15/15) based on
sorted filenames. This keeps the split stable across machines.

## 3) Deterministic Training

`training/train_vit_classifier.py` sets global seeds and deterministic
CUDA flags. The key controls are:

- `set_seed(seed=42)` for Python, NumPy, and PyTorch
- `torch.backends.cudnn.deterministic = True`
- `torch.backends.cudnn.benchmark = False`

To reproduce results, keep the same seed, GPU type, and dependency versions.

## 4) Training Command

```bash
python training/train_vit_classifier.py
```

Artifacts:
- `models/best_vit_lostfound.pth`
- `results/confusion_matrix.png`

## 5) Evaluation

Evaluation runs automatically at the end of training and reports:
- per-class precision/recall
- confusion matrix
- overall test accuracy

## 6) Model and API Validation

Suggested minimal checks:

```bash
pytest tests/ -v
RUN_CLIP_INTEGRATION_TESTS=1 pytest tests/test_xai.py -v
```

## 7) Experiment Logging

For publication-ready experiments:
- record git commit hash
- capture `pip freeze`
- log GPU/CPU model and RAM
- store training metrics and seed in experiment notes
