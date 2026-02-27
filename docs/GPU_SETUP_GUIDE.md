# GPU Setup Guide for RTX 4050

## ⚠️ CUDA Not Detected

Your code check shows: **CUDA Available: False**

This means PyTorch can't see your GPU. Here's how to fix it:

---

## ✅ Solution: Install CUDA-Enabled PyTorch

### Step 1: Check Your NVIDIA Driver
```bash
nvidia-smi
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 545.xx       Driver Version: 545.xx       CUDA Version: 12.3   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        TCC/WDDM  | Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ... WDDM  | 00000000:01:00.0  On |                  N/A |
```

**If this works → Your GPU driver is fine, proceed to Step 2**  
**If this fails → Install/update NVIDIA drivers from:** [nvidia.com/drivers](https://www.nvidia.com/drivers)

---

### Step 2: Install CUDA-Enabled PyTorch

Your current PyTorch is CPU-only. Reinstall with CUDA support:

```bash
# Uninstall current PyTorch
pip uninstall torch torchvision torchaudio

# Install CUDA 12.1 version (recommended for RTX 4050)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Or for CUDA 11.8 (if you have older drivers):**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

### Step 3: Verify GPU is Now Detected

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Not found')"
```

**Expected output:**
```
CUDA: True
GPU: NVIDIA GeForce RTX 4050 Laptop GPU
```

---

## 🚀 After CUDA is Working

### Your Training Will Be:
- **2-3x faster** with mixed precision (AMP)
- **10-20x faster** than CPU overall
- **4-6 hours** total training time (vs 24-36 hours on CPU)

### GPU Optimizations Already Added:
✅ Automatic GPU detection  
✅ Mixed precision training (AMP)  
✅ CuDNN benchmarking  
✅ GPU memory monitoring  

### Run Training:
```bash
python train_vit_classifier.py
```

**You should see:**
```
Using device: cuda
✓ GPU detected: NVIDIA GeForce RTX 4050 Laptop GPU
  GPU Memory: 6.00 GB
  CUDA Version: 12.1
✓ GPU optimizations enabled
✓ Mixed precision training enabled (faster GPU training)
```

---

## ⚡ Quick Reference

| Component | Status | Action Needed |
|-----------|--------|---------------|
| GPU Hardware | RTX 4050 ✓ | None |
| NVIDIA Driver | ? | Run `nvidia-smi` to check |
| CUDA Toolkit | ? | Not needed (comes with PyTorch) |
| PyTorch CUDA | ❌ CPU-only | **Reinstall** (see Step 2) |

---

## 🎯 Summary

**Current situation:** Code is ready for GPU but PyTorch is CPU-only  
**Fix:** Reinstall PyTorch with CUDA support (Step 2)  
**Time:** 5-10 minutes to reinstall  
**Result:** GPU-accelerated training! 🚀
