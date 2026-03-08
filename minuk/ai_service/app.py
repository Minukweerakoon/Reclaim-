import os
import io
import logging
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    rebuild_faiss_for_type("found")
    rebuild_faiss_for_type("lost")

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
# FAISS (bidirectional matching: found ↔ lost)
# =========================================================

# Found items index (for lost queries)
found_index: Optional[faiss.Index] = None
found_ids = []
found_urls = []
found_cats = []
found_model_cats = []
found_meta = []

# Lost items index (for found queries)
lost_index: Optional[faiss.Index] = None
lost_ids = []
lost_urls = []
lost_cats = []
lost_model_cats = []
lost_meta = []

def rebuild_faiss_for_type(item_type: str):
    """Rebuild FAISS index for specific item type (found or lost)"""
    # Declare ALL global variables at function start
    global found_index, found_ids, found_urls, found_cats, found_model_cats, found_meta
    global lost_index, lost_ids, lost_urls, lost_cats, lost_model_cats, lost_meta
    
    if item_type == "found":
        index_var = "found_index"
        ids_list, urls_list, cats_list, model_cats_list, meta_list = found_ids, found_urls, found_cats, found_model_cats, found_meta
    else:  # lost
        index_var = "lost_index"
        ids_list, urls_list, cats_list, model_cats_list, meta_list = lost_ids, lost_urls, lost_cats, lost_model_cats, lost_meta

    rows = supabase.table("items") \
        .select("id, metric_vec, final_category, model_category, image_url, location, time_of_incident, user_email, user_id, user_category, validation_summary") \
        .eq("status", "pending") \
        .eq("item_type", item_type) \
        .execute().data
    
    logger.info(f"[FAISS] Building {item_type} index from {len(rows)} database items")

    if not rows:
        if item_type == "found":
            found_index = None
        else:
            lost_index = None
        ids_list.clear()
        urls_list.clear()
        cats_list.clear()
        model_cats_list.clear()
        meta_list.clear()
        return

    vecs = []
    ids_list.clear()
    urls_list.clear()
    cats_list.clear()
    model_cats_list.clear()
    meta_list.clear()

    for r in rows:
        if not r["metric_vec"]:
            continue
        vecs.append(np.array(r["metric_vec"], dtype=np.float32))
        ids_list.append(r["id"])
        urls_list.append(r["image_url"])
        cats_list.append(r.get("final_category"))
        model_cats_list.append(r.get("model_category"))
        meta_list.append({
            "location": r.get("location"),
            "reported_time": r.get("time_of_incident"),
            "user_email": r.get("user_email"),
            "user_id": r.get("user_id"),
            "user_category": r.get("user_category"),
            "phone_number": (r.get("validation_summary") or {}).get("contact_phone"),
        })

    if not vecs:
        if item_type == "found":
            found_index = None
        else:
            lost_index = None
        return

    emb = np.stack(vecs).astype("float32")
    faiss.normalize_L2(emb)
    idx = faiss.IndexFlatIP(emb.shape[1])
    idx.add(emb)  # type: ignore[call-arg]
    
    if item_type == "found":
        found_index = idx
        logger.info(f"[FAISS] ✓ Found index rebuilt: {len(found_ids)} items")
    else:
        lost_index = idx
        logger.info(f"[FAISS] ✓ Lost index rebuilt: {len(lost_ids)} items")

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


def _norm_cat(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    v = str(value).strip().lower()
    return v or None

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
    # Declare all global variables at function start
    global found_index, found_ids, found_urls, found_cats, found_model_cats, found_meta
    global lost_index, lost_ids, lost_urls, lost_cats, lost_model_cats, lost_meta

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

    # ============================================
    # BIDIRECTIONAL MATCHING
    # ============================================
    # 1. Index current item in its type's index (found → found_index, lost → lost_index)
    # 2. Retrieve from opposite type's index (found → search lost_index, lost → search found_index)
    
    logger.info(f"[INDEX] ===== BIDIRECTIONAL MATCH START =====")
    logger.info(f"[INDEX] Received item_type='{payload.item_type}', item_id={payload.item_id}")
    
    # Use direct global references instead of local variables to avoid stale references
    is_found_item = (payload.item_type == "found")
    logger.info(f"[INDEX] is_found_item={is_found_item}")
    logger.info(f"[INDEX] Current database state: found_ids={len(found_ids)} items, lost_ids={len(lost_ids)} items")
    
    # Determine which lists to work with using direct global access
    my_index_ref = found_index if is_found_item else lost_index
    my_ids_ref = found_ids if is_found_item else lost_ids
    
    logger.info(f"[INDEX] Will ADD to: {'found_index' if is_found_item else 'lost_index'} (current size: {len(my_ids_ref)})")
    logger.info(f"[INDEX] Will SEARCH in: {'lost_index' if is_found_item else 'found_index'} (current size: {len(lost_ids if is_found_item else found_ids)})")

    # Index current item - use globals directly
    if my_index_ref is None:
        rebuild_faiss_for_type(payload.item_type)
        my_index_ref = found_index if is_found_item else lost_index
    else:
        # Check for duplicates
        if payload.item_id in my_ids_ref:
            rebuild_faiss_for_type(payload.item_type)
            my_index_ref = found_index if is_found_item else lost_index
        else:
            vec = z.reshape(1, -1).astype("float32")
            faiss.normalize_L2(vec)
            my_index_ref.add(vec)  # type: ignore[call-arg]

            # Append to appropriate global lists directly
            if is_found_item:
                found_ids.append(payload.item_id)
                found_urls.append(payload.image_url)
                found_cats.append(final_category)
                found_model_cats.append(pred_cat)
            else:
                lost_ids.append(payload.item_id)
                lost_urls.append(payload.image_url)
                lost_cats.append(final_category)
                lost_model_cats.append(pred_cat)
            
            item_meta = {
                "location": None,
                "reported_time": None,
                "user_email": None,
                "user_id": None,
                "user_category": payload.user_category,
                "phone_number": None,
            }
            try:
                meta_row = (
                    supabase.table("items")
                    .select("location, time_of_incident, user_email, user_id, user_category, validation_summary")
                    .eq("id", payload.item_id)
                    .limit(1)
                    .execute()
                )
                if meta_row.data and len(meta_row.data) > 0:
                    row = meta_row.data[0]
                    item_meta = {
                        "location": row.get("location"),
                        "reported_time": row.get("time_of_incident"),
                        "user_email": row.get("user_email"),
                        "user_id": row.get("user_id"),
                        "user_category": row.get("user_category"),
                        "phone_number": (row.get("validation_summary") or {}).get("contact_phone"),
                    }
            except Exception:
                pass
            
            # Append metadata to appropriate list
            if is_found_item:
                found_meta.append(item_meta)
            else:
                lost_meta.append(item_meta)

    # Search opposite index - use globals directly
    search_index_ref = lost_index if is_found_item else found_index
    search_ids_ref = lost_ids if is_found_item else found_ids
    search_urls_ref = lost_urls if is_found_item else found_urls
    search_cats_ref = lost_cats if is_found_item else found_cats
    search_model_cats_ref = lost_model_cats if is_found_item else found_model_cats
    search_meta_ref = lost_meta if is_found_item else found_meta
    
    # Rebuild opposite index if needed
    if search_index_ref is None:
        opposite_type = "lost" if is_found_item else "found"
        rebuild_faiss_for_type(opposite_type)
        # Re-read globals after rebuild
        search_index_ref = lost_index if is_found_item else found_index
        search_ids_ref = lost_ids if is_found_item else found_ids
        search_urls_ref = lost_urls if is_found_item else found_urls
        search_cats_ref = lost_cats if is_found_item else found_cats
        search_model_cats_ref = lost_model_cats if is_found_item else found_model_cats
        search_meta_ref = lost_meta if is_found_item else found_meta
    
    opposite_type = "lost" if is_found_item else "found"
    logger.info(f"[SEARCH] ===== SEARCH START =====")
    logger.info(f"[SEARCH] Item type='{payload.item_type}' will search '{opposite_type}' index")
    logger.info(f"[SEARCH] search_ids_ref has {len(search_ids_ref)} items")
    logger.info(f"[SEARCH] search_ids_ref IDs: {search_ids_ref[:3]}...")
    logger.info(f"[SEARCH] Global found_ids: {len(found_ids)} items, Global lost_ids: {len(lost_ids)} items")
    logger.info(f"[SEARCH] Verifying: search_ids_ref is {'lost_ids' if search_ids_ref is lost_ids else 'found_ids' if search_ids_ref is found_ids else 'UNKNOWN'}")

    # If no items to search, return indexed status only
    if search_index_ref is None or len(search_ids_ref) == 0:
        return {
            "status": "indexed",
            "final_category": final_category,
            "predicted_category": pred_cat,
            "entropy": entropy,
            "alpha": alpha,
            "results": [],
        }

    # Perform retrieval using the opposite index
    faiss.normalize_L2(z)
    D, I = search_index_ref.search(z, payload.k)  # type: ignore[call-arg]
    sims = D[0]
    idxs = I[0]

    # Filter out invalid FAISS indices (-1)
    valid = [(sim, idx) for sim, idx in zip(sims, idxs) if idx >= 0]

    if not valid:
        return {
            "status": "indexed",
            "final_category": final_category,
            "predicted_category": pred_cat,
            "entropy": entropy,
            "alpha": alpha,
            "results": [],
        }

    sims = np.array([v[0] for v in valid], dtype=np.float32)
    idxs = np.array([v[1] for v in valid], dtype=np.int32)

    # Convert cosine similarity (-1 to 1) into 0-1 range
    metric_scores = (sims + 1.0) / 2.0

    candidate_urls = [search_urls_ref[i] for i in idxs]
    clip_sims = clip_sim(query_img, candidate_urls)

    # CLIP scores are already normalized cosine similarities (0-1 range)
    # Do NOT use minmax normalization as it makes the best match always 100%
    clip_scores = clip_sims

    final_scores = (1 - alpha) * metric_scores + alpha * clip_scores

    order = np.argsort(final_scores)[::-1]

    # Smart category logic using all category signals.
    # Query side has: model(pred_cat), final(final_category), user(payload.user_category)
    query_model = _norm_cat(pred_cat)
    query_final = _norm_cat(final_category)
    query_user = _norm_cat(payload.user_category)
    query_categories = {c for c in [query_model, query_final, query_user] if c}

    results = []
    seen_ids = set()
    rank = 1
    for j in order:
        i = idxs[j]
        item_id = search_ids_ref[i]
        if item_id in seen_ids:
            continue
        seen_ids.add(item_id)

        meta = search_meta_ref[i] if i < len(search_meta_ref) else {}

        cand_model = _norm_cat(search_model_cats_ref[i])
        cand_final = _norm_cat(search_cats_ref[i])
        cand_user = _norm_cat(meta.get("user_category"))
        candidate_categories = {c for c in [cand_model, cand_final, cand_user] if c}

        # Candidate must share at least one category signal with query.
        # This avoids unrelated categories (e.g. smartphone in laptop query).
        overlap = query_categories.intersection(candidate_categories)
        if not overlap:
            continue

        # Use raw similarity score without any category boost
        # This shows the actual CLIP + metric similarity percentage
        adjusted_score = float(final_scores[j])

        results.append({
            "rank": rank,
            "id": item_id,
            "category": search_model_cats_ref[i] or search_cats_ref[i],
            "model_category": search_model_cats_ref[i],
            "final_category": search_cats_ref[i],
            "image_url": search_urls_ref[i],
            "score": adjusted_score,
            "location": meta.get("location"),
            "reported_time": meta.get("reported_time"),
            "user_email": meta.get("user_email"),
            "user_id": meta.get("user_id"),
            "user_category": meta.get("user_category"),
            "phone_number": meta.get("phone_number"),
            "category_overlap": sorted(list(overlap)),
        })
        logger.info(f"[SEARCH] Match #{rank}: ID={item_id}, score={adjusted_score:.2%}, location={meta.get('location')}")
        rank += 1

    # Keep highest adjusted-score matches first after category filtering.
    results.sort(key=lambda r: r.get("score", 0.0), reverse=True)
    for idx, row in enumerate(results, start=1):
        row["rank"] = idx

    logger.info(f"[SEARCH] ===== RETURNING {len(results)} RESULTS =====")
    if results:
        logger.info(f"[SEARCH] Top result: ID={results[0]['id']}, location={results[0].get('location')}")

    return {
        "status": "indexed",
        "predicted_category": pred_cat,
        "final_category": final_category,
        "entropy": entropy,
        "alpha": alpha,
        "results": results,
    }