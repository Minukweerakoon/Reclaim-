"""
Uncertainty-Aware Category-Refined (UACR) retrieval logic.
"""
import io
from datetime import datetime
from typing import Tuple, Union
import numpy as np
import requests
from PIL import Image

from .config import (
    ENTROPY_LOW, ENTROPY_HIGH, ALPHA_THRESHOLD,
    MIN_CATEGORIES, MAX_CATEGORIES,
    COVERAGE_LOW, COVERAGE_HIGH,
    GLOBAL_OVERSHOOT, FILTERED_OVERSHOOT
)


def alpha_from_entropy(entropy: float, ent_lo: float = ENTROPY_LOW, ent_hi: float = ENTROPY_HIGH) -> float:
    """Convert entropy to alpha (uncertainty measure) in [0, 1]."""
    return float(np.clip((entropy - ent_lo) / (ent_hi - ent_lo), 0, 1))


def minmax_norm(x):
    """Min-max normalization."""
    x = np.array(x, dtype=np.float32)
    if x.size == 0 or (x.max() - x.min()) < 1e-9:
        return np.zeros_like(x)
    return (x - x.min()) / (x.max() - x.min())


def pick_categories(
    p_row: np.ndarray,
    entropy: float,
    ent_lo: float = ENTROPY_LOW,
    ent_hi: float = ENTROPY_HIGH,
    min_k: int = MIN_CATEGORIES,
    max_k: int = MAX_CATEGORIES
) -> Tuple[list, float, float]:
    """Select categories based on uncertainty and probability distribution.
    
    Returns:
        chosen_idx: List of selected category indices
        cov: Actual coverage achieved
        target_cov: Target coverage based on uncertainty
    """
    alpha = alpha_from_entropy(entropy, ent_lo, ent_hi)
    target_cov = COVERAGE_LOW * (1 - alpha) + COVERAGE_HIGH * alpha

    order = np.argsort(p_row)[::-1]
    cov, chosen = 0.0, []
    for i, c in enumerate(order):
        if i >= max_k:
            break
        chosen.append(int(c))
        cov += float(p_row[c])
        if cov >= target_cov and (i + 1) >= min_k:
            break
    return chosen, cov, target_cov


def adaptive_retrieval(
    query_vec: np.ndarray,
    chosen_cats: list[str],
    alpha: float,
    k: int,
    search_global_fn,
    search_filtered_fn
) -> Tuple[list, str]:
    """Perform adaptive retrieval based on uncertainty.
    
    Args:
        query_vec: Query embedding vector
        chosen_cats: List of selected category names
        alpha: Uncertainty measure [0, 1]
        k: Number of results to retrieve
        search_global_fn: Function for global search
        search_filtered_fn: Function for filtered search
    
    Returns:
        hits: List of (doc_id, similarity) tuples
        retrieval_mode: "global" or "filtered"
    """
    if alpha >= ALPHA_THRESHOLD:
        hits = search_global_fn(
            query_vec,
            k=k,
            overshoot=max(GLOBAL_OVERSHOOT, k * 400)
        )
        retrieval_mode = "global"
    else:
        hits = search_filtered_fn(
            query_vec,
            chosen_cats,
            k=k,
            overshoot=max(FILTERED_OVERSHOOT, k * 50)
        )
        retrieval_mode = "filtered"
    
    return hits, retrieval_mode


def rank_results(hits: list, docs: list, k: int) -> list:
    """Rank and format retrieval results.
    
    Args:
        hits: List of (doc_id, similarity) tuples
        docs: List of MongoDB documents
        k: Number of results to return
    
    Returns:
        List of ranked results with metadata
    """
    metric = np.array([sim for _, sim in hits], dtype=np.float32)
    metric_n = minmax_norm(metric)

    order = np.argsort(metric_n)[::-1]
    results = []

    for rank, j in enumerate(order[:k], start=1):
        d = docs[int(j)]
        results.append({
            "rank": rank,
            "id": str(d.get("_id")),
            "category": d.get("category"),
            "image_url": d.get("image_url"),
            "score": float(metric_n[int(j)]),
        })

    return results


def process_item_logic(
    status: str,
    image_url: str,
    k: int,
    mc_T: int,
    models_manager,
    storage_module
) -> Union[dict, tuple[str, dict]]:
    """
    Core logic for processing lost and found items.
    
    Args:
        status: "lost" or "found"
        image_url: URL of the item image
        k: Number of results to return (for lost items)
        mc_T: Number of MC dropout iterations
        models_manager: ModelManager instance
        storage_module: Storage module with FAISS operations
    
    Returns:
        For found items: dict with indexed response
        For lost items: dict with retrieval response
        On error: tuple of (error_type, error_dict)
    """
    from .models import common_tf
    
    # 1) Download and validate image
    try:
        r = requests.get(image_url, timeout=25)
        r.raise_for_status()
        query_img = Image.open(io.BytesIO(r.content)).convert("RGB")
    except Exception as e:
        return ("download_error", {
            "error": f"Failed to download/open image_url: {e}"
        })
    
    # Prepare input tensor
    x = common_tf(query_img).unsqueeze(0).to(
        models_manager.clf.model.classifier[3][1].weight.device
    )
    
    # 2) MC dropout classification
    p, entropy = models_manager.mc_predict(x, T=mc_T)
    pred_idx = int(p.argmax())
    pred_cat = models_manager.idx_to_cat[pred_idx]
    
    # 3) Compute entropy
    # (already computed in step 2)
    
    # 4) Compute alpha (uncertainty measure)
    alpha = alpha_from_entropy(entropy)
    
    # 5) Generate embedding
    z = models_manager.metric_embed(query_img)
    
    # 6) Handle FOUND items - index for future retrieval
    if status == "found":
        doc = {
            "type": "found",
            "category": pred_cat,
            "created_at": datetime.utcnow(),
            "metric_vec": z[0].tolist(),
            "entropy": float(entropy),
            "alpha": float(alpha),
            "source": "production",
            "image_url": image_url,
        }
        
        doc_id = storage_module.insert_item(doc)
        storage_module.add_vector(z[0], doc_id, pred_cat, "found")
        
        return {
            "status": "indexed",
            "id": doc_id,
            "category": pred_cat,
            "entropy": float(entropy),
            "alpha": float(alpha),
        }
    
    # 7) Handle LOST items - search for matches
    db_idx = storage_module.get_db_index()
    if db_idx.is_empty():
        return ("no_items", {
            "error": "No found items indexed yet.",
            "results": []
        })
    
    # Category selection based on uncertainty
    chosen_idx, cov, target_cov = pick_categories(p, entropy)
    chosen_cats = [models_manager.idx_to_cat[i] for i in chosen_idx]
    
    # Adaptive retrieval
    hits, retrieval_mode = adaptive_retrieval(
        query_vec=z,
        chosen_cats=chosen_cats,
        alpha=alpha,
        k=k,
        search_global_fn=storage_module.search_global,
        search_filtered_fn=storage_module.search_filtered
    )
    
    if len(hits) == 0:
        return {
            "predicted_category": pred_cat,
            "entropy": float(entropy),
            "alpha": float(alpha),
            "retrieval_mode": retrieval_mode,
            "results": []
        }
    
    # Fetch documents and rank results
    docs = storage_module.get_docs_for_ids([doc_id for doc_id, _ in hits])
    results = rank_results(hits, docs, k=k)
    
    return {
        "predicted_category": pred_cat,
        "entropy": float(entropy),
        "alpha": float(alpha),
        "retrieval_mode": retrieval_mode,
        "results": results,
    }
