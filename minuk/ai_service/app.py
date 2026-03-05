import os
import io
from typing import Optional, Literal
from datetime import datetime
import time

import numpy as np
import requests
from PIL import Image

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms

import pandas as pd

import faiss
import open_clip

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from supabase import create_client  # type: ignore[import-untyped]
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

print("SUPABASE_URL:", os.getenv("SUPABASE_URL"))
print("SUPABASE_SERVICE_ROLE_KEY:", "Loaded" if os.getenv("SUPABASE_SERVICE_ROLE_KEY") else "Missing")

# =========================================================
# CONFIG
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Supabase credentials not set")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(title="UACR AI Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    rebuild_faiss()

# =========================================================
# MODEL LOADING
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODEL_PATH = os.path.join(ASSETS_DIR, "mobilenetv3_mc_dropout.pt")

common_tf = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# =========================================================
# LOAD CLASS ORDER FROM TRAINING METADATA (CRITICAL)
# =========================================================

META_CSV = os.path.join(ASSETS_DIR, "metadata.csv")

if not os.path.exists(META_CSV):
    raise RuntimeError("metadata.csv not found in assets folder")

df = pd.read_csv(META_CSV)

if "category" not in df.columns:
    raise RuntimeError("metadata.csv must contain a 'category' column")

classes = sorted(df["category"].unique().tolist())
NUM_CLASSES = len(classes)

idx_to_cat = {i: c for i, c in enumerate(classes)}

class MobileNetV3LargeMCDropout(nn.Module):
    def __init__(self, num_classes, p_drop=0.3):
        super().__init__()
        base = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        )
        in_feats = int(base.classifier[3].in_features)  # type: ignore[arg-type]
        base.classifier[3] = nn.Sequential(
            nn.Dropout(p_drop),
            nn.Linear(in_feats, num_classes)
        )
        self.model = base

    def forward(self, x):
        return self.model(x)

clf = MobileNetV3LargeMCDropout(NUM_CLASSES).to(DEVICE)
clf.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
clf.eval()

# Backbone for embeddings
class Backbone(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        base = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        )
        in_feats = int(base.classifier[3].in_features)  # type: ignore[arg-type]
        base.classifier[3] = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(in_feats, num_classes)
        )
        self.base = base

    def forward(self, x):
        x = self.base.features(x)
        x = self.base.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.base.classifier[0](x)
        x = self.base.classifier[1](x)
        return x

backbone = Backbone(NUM_CLASSES).to(DEVICE)
backbone.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE), strict=False)
backbone.eval()

# CLIP
clip_model_loaded, _, clip_val_preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="laion2b_s34b_b79k"
)
clip_model = clip_model_loaded.to(DEVICE).eval()
clip_preprocess = clip_val_preprocess

# =========================================================
# FAISS (built from unified 'items' table where item_type='found')
# =========================================================

db_index: Optional[faiss.Index] = None
db_ids = []
db_urls = []
db_cats = []

def rebuild_faiss():
    global db_index, db_ids, db_urls, db_cats

    rows = supabase.table("items") \
        .select("id, metric_vec, final_category, image_url") \
        .eq("status", "pending") \
        .eq("item_type", "found") \
        .execute().data

    if not rows:
        db_index = None
        return

    vecs = []
    db_ids = []
    db_urls = []
    db_cats = []

    for r in rows:
        if not r["metric_vec"]:
            continue
        vecs.append(np.array(r["metric_vec"], dtype=np.float32))
        db_ids.append(r["id"])
        db_urls.append(r["image_url"])
        db_cats.append(r.get("final_category"))

    if not vecs:
        db_index = None
        return

    emb = np.stack(vecs).astype("float32")
    faiss.normalize_L2(emb)
    idx = faiss.IndexFlatIP(emb.shape[1])
    idx.add(emb)  # type: ignore[call-arg]
    db_index = idx

# =========================================================
# UTILITIES
# =========================================================

def download_image(url: str) -> Image.Image:
    headers = {"User-Agent": "Mozilla/5.0"}
    last_error: Optional[Exception] = None

    # Transient network errors to Supabase/CDN do happen; retry before failing.
    for attempt in range(1, 4):
        try:
            r = requests.get(url, timeout=20, headers=headers)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception as e:
            last_error = e
            if attempt < 3:
                time.sleep(0.5 * attempt)

    raise HTTPException(
        status_code=400,
        detail=f"Failed to download image after retries: {last_error}"
    )

@torch.no_grad()
def mc_predict(x, T=20):
    probs = []
    for _ in range(T):
        logits = clf(x)
        probs.append(F.softmax(logits, dim=-1))
    p = torch.stack(probs, 0).mean(0)
    ent = -(p * (p + 1e-12).log()).sum(dim=1)
    return p[0].cpu().numpy(), float(ent[0].cpu())

def alpha_from_entropy(ent, lo=0.2, hi=1.5):
    return float(np.clip((ent - lo) / (hi - lo), 0, 1))

@torch.no_grad()
def metric_embed(img):
    x = common_tf(img).unsqueeze(0).to(DEVICE)
    z = backbone(x)
    z = F.normalize(z, dim=1)
    return z.cpu().numpy().astype("float32")

@torch.no_grad()
def clip_sim(query_img, urls):
    q = clip_preprocess(query_img).unsqueeze(0).to(DEVICE)  # type: ignore[operator]
    q = clip_model.encode_image(q)  # type: ignore[operator]
    q = F.normalize(q, dim=-1)

    sims = []
    for u in urls:
        img = download_image(u)
        x = clip_preprocess(img).unsqueeze(0).to(DEVICE)  # type: ignore[operator]
        c = clip_model.encode_image(x)  # type: ignore[operator]
        c = F.normalize(c, dim=-1)
        sims.append((q @ c.T).item())

    return np.array(sims, dtype=np.float32)

def minmax(x):
    if len(x) == 0:
        return x
    if x.max() - x.min() < 1e-9:
        return np.zeros_like(x)
    return (x - x.min()) / (x.max() - x.min())

# =========================================================
# REQUEST MODEL
# =========================================================

class ProcessItemRequest(BaseModel):
    item_id: str
    item_type: Literal["lost", "found"]
    image_url: str
    user_category: Optional[str] = None
    k: int = 5
    mc_T: int = 20

# =========================================================
# ENDPOINT
# =========================================================

@app.post("/items/process")
async def process_item(payload: ProcessItemRequest):

    query_img = download_image(payload.image_url)

    x = common_tf(query_img).unsqueeze(0).to(DEVICE)  # type: ignore[attr-defined]
    p, entropy = mc_predict(x, payload.mc_T)

    pred_idx = int(np.argmax(p))
    pred_cat = idx_to_cat[pred_idx]
    alpha = alpha_from_entropy(entropy)
    z = metric_embed(query_img)

    table = "items"

    # Compute final_category using uncertainty logic
    UNCERTAINTY_THRESHOLD = 1.2  # tune if needed

    if payload.user_category and entropy > UNCERTAINTY_THRESHOLD:
        final_category = payload.user_category
    else:
        final_category = pred_cat

    supabase.table(table).update({
        "model_category": pred_cat,
        "final_category": final_category,
        "metric_vec": z[0].tolist(),
        "entropy": entropy,
        "alpha": alpha
    }).eq("id", payload.item_id).execute()

    # If found → rebuild index and return
    if payload.item_type == "found":
        global db_index, db_ids, db_urls, db_cats

        if db_index is None:
            rebuild_faiss()
        else:
            vec = z.reshape(1, -1).astype("float32")
            faiss.normalize_L2(vec)
            db_index.add(vec)  # type: ignore[call-arg]

            db_ids.append(payload.item_id)
            db_urls.append(payload.image_url)
            db_cats.append(final_category)

        return {
            "status": "indexed",
            "final_category": final_category,
            "predicted_category": pred_cat,
            "entropy": entropy,
            "alpha": alpha,
        }

    # LOST → retrieve from 'items' where item_type='found'
    if db_index is None:
        rebuild_faiss()

    if db_index is None:
        return {"results": []}

    faiss.normalize_L2(z)
    D, I = db_index.search(z, payload.k)  # type: ignore[call-arg]
    sims = D[0]
    idxs = I[0]

    # Filter out invalid FAISS indices (-1)
    valid = [(sim, idx) for sim, idx in zip(sims, idxs) if idx >= 0]

    if not valid:
        return {"results": []}

    sims = np.array([v[0] for v in valid], dtype=np.float32)
    idxs = np.array([v[1] for v in valid], dtype=np.int32)

    # Convert cosine similarity (-1 to 1) into 0-1 range
    metric_scores = (sims + 1.0) / 2.0

    candidate_urls = [db_urls[i] for i in idxs]
    clip_sims = clip_sim(query_img, candidate_urls)

    # Normalize CLIP scores safely
    clip_scores = minmax(clip_sims)

    final = (1 - alpha) * metric_scores + alpha * clip_scores

    order = np.argsort(final)[::-1]

    results = []
    for rank, j in enumerate(order, start=1):
        i = idxs[j]
        results.append({
            "rank": rank,
            "id": db_ids[i],
            "category": db_cats[i],
            "image_url": db_urls[i],
            "score": float(final[j]),
        })

    return {
        "predicted_category": pred_cat,
        "final_category": final_category,
        "entropy": entropy,
        "alpha": alpha,
        "results": results,
    }