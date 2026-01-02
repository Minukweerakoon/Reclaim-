import os, io
import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

import faiss
import open_clip

from fastapi import FastAPI, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import requests

# Optional: helps avoid OpenMP crash on macOS (safe for dev; remove if you want)
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")


# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(__file__)
ASSETS = os.path.join(BASE_DIR, "assets")

MODEL_PT  = os.path.join(ASSETS, "mobilenetv3_mc_dropout.pt")
EMB_NPY   = os.path.join(ASSETS, "embeddings_mobilenetv3.npy")
IDS_NPY   = os.path.join(ASSETS, "ids_mobilenetv3.npy")
FAISS_IDX = os.path.join(ASSETS, "faiss_mobilenetv3.index")
META_CSV  = os.path.join(ASSETS, "metadata.csv")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI(title="UACR AI Service (Minuk)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Load metadata
# -----------------------------
df = pd.read_csv(META_CSV)
df["id"] = df["id"].astype(int)

classes = sorted(df["category"].unique().tolist())
num_classes = len(classes)
idx_to_cat = {i: c for i, c in enumerate(classes)}
id_to_cat = dict(zip(df["id"].values, df["category"].values))
id_to_path = dict(zip(df["id"].values, df["path"].values))


# -----------------------------
# Load embeddings + ids + faiss index
# -----------------------------
embeddings = np.load(EMB_NPY).astype("float32")
ids = np.load(IDS_NPY).astype(int)
index = faiss.read_index(FAISS_IDX)


# -----------------------------
# Transforms (must match training)
# -----------------------------
common_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
])


# -----------------------------
# MobileNetV3 MC-Dropout classifier
# -----------------------------
class MobileNetV3LargeMCDropout(nn.Module):
    def __init__(self, num_classes, p_drop=0.3):
        super().__init__()
        base = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        )
        in_feats = base.classifier[3].in_features
        base.classifier[3] = nn.Sequential(nn.Dropout(p_drop), nn.Linear(in_feats, num_classes))
        self.model = base

    def forward(self, x):
        return self.model(x)

clf = MobileNetV3LargeMCDropout(num_classes=num_classes, p_drop=0.3).to(DEVICE)
state = torch.load(MODEL_PT, map_location=DEVICE)
clf.load_state_dict(state)
clf.eval()


# -----------------------------
# MobileNetV3 Backbone for embeddings
# -----------------------------
class MobileNetV3Backbone(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        base = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        )
        in_feats = base.classifier[3].in_features
        base.classifier[3] = nn.Sequential(nn.Dropout(0.3), nn.Linear(in_feats, num_classes))
        self.base = base

    def forward(self, x):
        x = self.base.features(x)
        x = self.base.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.base.classifier[0](x)
        x = self.base.classifier[1](x)
        return x

backbone = MobileNetV3Backbone(num_classes=num_classes).to(DEVICE)
backbone.load_state_dict(state, strict=False)
backbone.eval()


# -----------------------------
# CLIP (OpenCLIP)
# -----------------------------
clip_model, _, clip_preprocess = open_clip.create_model_and_transforms(
    model_name="ViT-B-32",
    pretrained="laion2b_s34b_b79k"
)
clip_model = clip_model.to(DEVICE).eval()


# -----------------------------
# Helpers
# -----------------------------
def enable_dropout(m: nn.Module):
    for layer in m.modules():
        if isinstance(layer, nn.Dropout):
            layer.train()

@torch.no_grad()
def mc_predict(x: torch.Tensor, T: int = 20):
    enable_dropout(clf)
    probs = []
    for _ in range(T):
        logits = clf(x)
        probs.append(F.softmax(logits, dim=-1))
    p = torch.stack(probs, 0).mean(0)  # [1,C]
    ent = -(p * (p + 1e-12).log()).sum(dim=1)  # [1]
    return p[0].cpu().numpy(), float(ent[0].cpu().numpy())

def alpha_from_entropy(entropy: float, ent_lo=0.2, ent_hi=1.5):
    return float(np.clip((entropy - ent_lo) / (ent_hi - ent_lo), 0, 1))

def minmax_norm(x):
    x = np.array(x, dtype=np.float32)
    if x.size == 0 or (x.max() - x.min()) < 1e-9:
        return np.zeros_like(x)
    return (x - x.min()) / (x.max() - x.min())

def pick_categories(p_row, entropy, ent_lo=0.2, ent_hi=1.5, min_k=1, max_k=5):
    alpha = alpha_from_entropy(entropy, ent_lo, ent_hi)
    target_cov = 0.70*(1-alpha) + 0.95*alpha

    order = np.argsort(p_row)[::-1]
    cov, chosen = 0.0, []
    for i, c in enumerate(order):
        if i >= max_k:
            break
        chosen.append(int(c))
        cov += float(p_row[c])
        if cov >= target_cov and (i+1) >= min_k:
            break
    return chosen, cov, target_cov

@torch.no_grad()
def clip_embed(pil_img: Image.Image):
    x = clip_preprocess(pil_img).unsqueeze(0).to(DEVICE)
    feat = clip_model.encode_image(x)
    return F.normalize(feat, dim=-1)

@torch.no_grad()
def clip_sims(query_pil: Image.Image, cand_paths):
    q = clip_embed(query_pil)
    sims = []
    for p in cand_paths:
        img = Image.open(p).convert("RGB")
        c = clip_embed(img)
        sims.append((q @ c.T).item())
    return np.array(sims, dtype=np.float32)

def faiss_search_filtered(query_vec, allowed_cats, k=10, overshoot=400):
    D, I = index.search(query_vec.astype("float32"), overshoot)
    D, I = D[0], I[0]
    allowed = set(allowed_cats)
    out = []
    for sim, pos in zip(D, I):
        img_id = int(ids[pos])
        if id_to_cat.get(img_id) in allowed:
            out.append((img_id, float(sim)))
        if len(out) >= k:
            break
    return out


def top_probs_list(p: np.ndarray, topk: int = 5):
    top_idx = np.argsort(p)[::-1][:topk]
    return [
        {"category": idx_to_cat[int(i)], "prob": float(p[int(i)])}
        for i in top_idx
    ]


def faiss_search_global(query_vec, k=10, overshoot=2000):
    D, I = index.search(query_vec.astype("float32"), overshoot)
    D, I = D[0], I[0]
    out = []
    for sim, pos in zip(D, I):
        img_id = int(ids[pos])
        out.append((img_id, float(sim)))
        if len(out) >= k:
            break
    return out


def run_uacr(query_img: Image.Image, k: int = 10, mc_T: int = 20, debug: bool = False):
    x = common_tf(query_img).unsqueeze(0).to(DEVICE)

    # 1) category + uncertainty
    p, entropy = mc_predict(x, T=mc_T)
    pred_idx = int(np.argmax(p))
    pred_cat = idx_to_cat[pred_idx]

    chosen_idx, cov, target_cov = pick_categories(p, entropy)
    chosen_cats = [idx_to_cat[i] for i in chosen_idx]

    # Helpful debugging/UX: show top-k category probabilities
    top_probs = top_probs_list(p, topk=5) if debug else None

    # 2) metric embedding
    with torch.no_grad():
        z = backbone(x)
        z = F.normalize(z, dim=1)
    z = z.cpu().numpy().astype("float32")

    # 3) Adaptive retrieval: if uncertain, widen search so CLIP has a chance to rescue
    alpha = alpha_from_entropy(entropy)

    if alpha >= 0.35:
        hits = faiss_search_global(z, k=k, overshoot=max(2000, k * 400))
        retrieval_mode = "global"
    else:
        hits = faiss_search_filtered(z, chosen_cats, k=k, overshoot=max(400, k * 50))
        retrieval_mode = "filtered"

    if len(hits) == 0:
        return {
            "predicted_category": pred_cat,
            "final_category": pred_cat,
            "final_id": None, 
            "entropy": entropy,
            "alpha": alpha,
            "chosen_categories": chosen_cats,
            "coverage": cov,
            "target_coverage": target_cov,
            "top_probs": top_probs,
            "clip_used": False,
            "retrieval_mode": retrieval_mode,
            "results": [],
        }

    cand_ids = [img_id for img_id, _ in hits]
    cand_paths = [id_to_path.get(img_id, "") for img_id in cand_ids]
    metric = np.array([sim for _, sim in hits], dtype=np.float32)

    # Filter to only candidates that exist locally (needed for CLIP reranking)
    keep = [i for i, pth in enumerate(cand_paths) if pth and os.path.exists(pth)]

    # Normalize metric scores for fusion
    metric_n_full = minmax_norm(metric)

    # If nothing exists locally, we can still return metric-only results (no CLIP)
    if len(keep) == 0:
        order = np.argsort(metric_n_full)[::-1]
        results = []
        for rank, idx in enumerate(order[:k], start=1):
            img_id = int(cand_ids[idx])
            results.append({
                "rank": rank,
                "id": img_id,
                "category": id_to_cat.get(img_id, "Unknown"),
                "final_score": float(metric_n_full[idx]),
                "metric_sim": float(metric[idx]),
                "clip_sim": 0.0,
            })
        final_category = results[0]["category"] if results else pred_cat
        final_id = results[0]["id"] if results else None

        return {
            "predicted_category": pred_cat,
            "final_category": final_category,
            "final_id": final_id,
            "entropy": entropy,
            "alpha": alpha,
            "chosen_categories": chosen_cats,
            "coverage": cov,
            "target_coverage": target_cov,
            "top_probs": top_probs,
            "clip_used": False,
            "retrieval_mode": retrieval_mode,
            "results": results,
        }

    # Build the local-only candidate lists
    cand_ids_ok = [cand_ids[i] for i in keep]
    cand_paths_ok = [cand_paths[i] for i in keep]
    metric_ok = metric[keep]

    metric_n = minmax_norm(metric_ok)

    # 4) CLIP + fusion (safe fallback)
    clip = np.zeros(len(cand_paths_ok), dtype=np.float32)  # always defined
    clip_used = False

    try:
        clip = clip_sims(query_img, cand_paths_ok)
        clip_n = minmax_norm(clip)

        # Use entropy-driven alpha: low entropy -> metric dominates; high entropy -> CLIP dominates
        final = (1 - alpha) * metric_n + alpha * clip_n
        clip_used = True
    except Exception as e:
        final = metric_n
        clip_used = False
        print("⚠️ CLIP skipped:", e)

    order = np.argsort(final)[::-1]
    results = []
    for rank, idx in enumerate(order[:k], start=1):
        img_id = int(cand_ids_ok[idx])
        results.append({
            "rank": rank,
            "id": img_id,
            "category": id_to_cat.get(img_id, "Unknown"),
            "final_score": float(final[idx]),
            "metric_sim": float(metric_ok[idx]),
            "clip_sim": float(clip[idx]),
        })
    final_category = results[0]["category"] if results else pred_cat
    final_id = results[0]["id"] if results else None

    return {
        "predicted_category": pred_cat,
        "final_category": final_category,
        "final_id": final_id,
        "entropy": entropy,
        "alpha": alpha,
        "chosen_categories": chosen_cats,
        "coverage": cov,
        "target_coverage": target_cov,
        "top_probs": top_probs,
        "clip_used": clip_used,
        "retrieval_mode": retrieval_mode,
        "results": results,
    }


# -----------------------------
# Request body for URL-based search 
# -----------------------------
class UrlSearchRequest(BaseModel):
    image_url: str
    k: int = 10
    mc_T: int = 20
    debug: bool = False


# -----------------------------
# Routes
# -----------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "num_classes": num_classes,
        "indexed": int(index.ntotal),
    }

@app.post("/search")
async def search(
    file: UploadFile = File(...),
    k: int = Query(10, ge=1, le=50),
    mc_T: int = Query(20, ge=5, le=50),
    debug: bool = Query(False)
):
    raw = await file.read()
    query_img = Image.open(io.BytesIO(raw)).convert("RGB")
    return run_uacr(query_img, k=k, mc_T=mc_T, debug=debug)

@app.post("/search-by-url")
async def search_by_url(payload: UrlSearchRequest):
    try:
        r = requests.get(payload.image_url, timeout=20)
        r.raise_for_status()
        query_img = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        return {"error": f"Failed to download/open image_url: {str(e)}"}

    return run_uacr(query_img, k=payload.k, mc_T=payload.mc_T, debug=payload.debug)
