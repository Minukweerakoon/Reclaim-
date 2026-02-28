"""
E2E test: Validate with real image + save to Supabase with image_url.
Verifies the full pipeline: validate → upload to Storage → save with image_url.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

import requests
import json

BASE = "http://localhost:8000"
HEADERS = {"X-API-Key": "test-api-key"}

# Real images from Balanced_Dataset
LAPTOP_IMG = r"c:\Users\16473\Desktop\multimodel-validation\Balanced_Dataset\Laptop\laptops_100_aug0.jpg"
WALLET_IMG = r"c:\Users\16473\Desktop\multimodel-validation\Balanced_Dataset\Wallets\wallets_100_aug0.jpg"


def validate_with_image(text, visual, image_path, label):
    """Run validation and return result including image_url."""
    print(f"\n{'='*60}")
    print(f"VALIDATING: {label}")
    print(f"{'='*60}")
    
    data = {"text": text, "visualText": visual, "language": "en"}
    with open(image_path, "rb") as f:
        files = {"image_file": (os.path.basename(image_path), f, "image/jpeg")}
        r = requests.post(f"{BASE}/validate/complete", data=data, files=files, headers=HEADERS, timeout=120)
    
    print(f"  Status: {r.status_code}")
    if r.status_code != 200:
        print(f"  ERROR: {r.text[:300]}")
        return None
    
    result = r.json()
    conf = result.get("confidence", {})
    print(f"  Confidence: {conf.get('overall_confidence')}")
    print(f"  Image URL:  {result.get('image_url', 'NONE')}")
    return result


def save_to_supabase(validation_result, intention, email):
    """Save validated report to Supabase with image_url."""
    from src.database.supabase_client import get_supabase_manager
    sb = get_supabase_manager()
    
    conf = validation_result.get("confidence", {})
    text_result = validation_result.get("text", {})
    entities = text_result.get("entities", {}) if text_result else {}
    
    item_data = {
        "item_type": ", ".join(entities.get("item_mentions", ["unknown"])),
        "description": text_result.get("text", ""),
        "color": ", ".join(entities.get("color_mentions", [])),
        "brand": ", ".join(entities.get("brand_mentions", [])),
        "location": ", ".join(entities.get("location_mentions", [])),
        "confidence_score": conf.get("overall_confidence", 0),
        "routing": conf.get("routing", "manual"),
        "action": conf.get("action", "review"),
        "image_url": validation_result.get("image_url"),  # ← from Storage
        "validation_summary": {
            "input_types": validation_result.get("input_types"),
            "confidence": conf,
        },
    }
    
    rid = sb.save_validated_item(
        intention=intention,
        user_id="e2e-image-test",
        user_email=email,
        item_data=item_data,
    )
    
    if rid:
        print(f"  SAVED: {rid[:10]}... (image_url included)")
    else:
        print("  SAVE FAILED!")
    return rid


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    EMAIL = "kumeshawijesundara2002@gmail.com"
    
    # Test 1: Lost Laptop with Image
    r1 = validate_with_image(
        "I lost my silver Dell laptop at the library second floor near the window. It has a blue protective case.",
        "Silver Dell laptop blue case",
        LAPTOP_IMG,
        "LOST LAPTOP"
    )
    if r1:
        save_to_supabase(r1, "lost", EMAIL)
    
    # Test 2: Found Wallet with Image
    r2 = validate_with_image(
        "I found a brown leather wallet near the Student Center cafeteria entrance. It has a zipper.",
        "Brown leather wallet",
        WALLET_IMG,
        "FOUND WALLET"
    )
    if r2:
        save_to_supabase(r2, "found", EMAIL)
    
    # Verify
    print(f"\n{'='*60}")
    print("VERIFICATION: Check image_url in recent records")
    print(f"{'='*60}")
    
    from src.database.supabase_client import get_supabase_manager
    sb = get_supabase_manager()
    
    for table, label in [("lost_items", "LOST"), ("found_items", "FOUND")]:
        items = sb._get_items(table, 5, "active")
        for item in items:
            img = item.get("image_url", "")
            has_img = "YES" if img else "NO"
            print(f"  [{label}] {item['id'][:10]}.. | {item.get('item_type',''):15s} | image={has_img}")
            if img:
                print(f"           URL: {img[:80]}...")
    
    print(f"\n{'='*60}")
    print("DONE! Check Supabase Table Editor → image_url column should have URLs!")
    print(f"{'='*60}")
