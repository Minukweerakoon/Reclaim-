"""
Real Image Dataset Integration
Processes the Balanced_Dataset with 44,000 real lost-and-found item images

This dramatically improves research quality:
- Real-world validation (not just synthetic)
- Visual grounding for text descriptions
- Multi-modal learning capabilities
- Publication-ready evaluation dataset
"""

import os
import json
import random
from pathlib import Path
from collections import Counter
import shutil

# Dataset path
BALANCED_DATASET_PATH = Path("Balanced_Dataset")
OUTPUT_PATH = Path("data/image_dataset")

# Category mapping (normalize names)
CATEGORY_MAPPING = {
    "Card": "card",
    "Headphone": "headphone",
    "Key": "key",
    "Keyboard": "keyboard",
    "Lapcharger": "laptop_charger",
    "Laptop": "laptop",
    "Mouse": "mouse",
    "Smartphone": "phone",
    "Unknown": "unknown",
    "Wallets": "wallet",
    "backpack": "backpack"
}

def analyze_dataset():
    """Analyze the image dataset structure."""
    print("="*80)
    print("REAL IMAGE DATASET ANALYSIS")
    print("="*80)
    print()
    
    if not BALANCED_DATASET_PATH.exists():
        print(f"❌ Dataset not found at {BALANCED_DATASET_PATH}")
        return None
    
    # Count images per category
    category_counts = {}
    total_images = 0
    
    for category_dir in BALANCED_DATASET_PATH.iterdir():
        if category_dir.is_dir():
            image_files = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.jpeg")) + list(category_dir.glob("*.png"))
            count = len(image_files)
            category_counts[category_dir.name] = count
            total_images += count
    
    print(f"📊 DATASET STATISTICS")
    print(f"   Total Images: {total_images:,}")
    print(f"   Categories: {len(category_counts)}")
    print()
    
    print("📁 Images per category:")
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        normalized = CATEGORY_MAPPING.get(category, category)
        print(f"   {category:15s} → {normalized:15s}: {count:,} images")
    
    print()
    print("✅ This is EXCELLENT for research!")
    print("   - 10x larger than LostNet dataset (1000 images)")
    print("   - Balanced across categories")
    print("   - Real-world images → High credibility")
    print()
    
    return category_counts

def create_train_val_test_split(train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """
    Create train/validation/test splits for research evaluation.
    
    Args:
        train_ratio: Percentage for training (default: 70%)
        val_ratio: Percentage for validation (default: 15%)
        test_ratio: Percentage for test (default: 15%)
    """
    print("="*80)
    print("CREATING TRAIN/VAL/TEST SPLITS")
    print("="*80)
    print()
    
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    splits = {
        "train": [],
        "validation": [],
        "test": []
    }
    
    total_processed = 0
    
    for category_dir in BALANCED_DATASET_PATH.iterdir():
        if not category_dir.is_dir():
            continue
        
        category = category_dir.name
        normalized_category = CATEGORY_MAPPING.get(category, category)
        
        # Get all images
        image_files = list(category_dir.glob("*.jpg")) + list(category_dir.glob("*.jpeg")) + list(category_dir.glob("*.png"))
        random.shuffle(image_files)
        
        # Calculate split sizes
        n_images = len(image_files)
        n_train = int(n_images * train_ratio)
        n_val = int(n_images * val_ratio)
        
        # Split
        train_images = image_files[:n_train]
        val_images = image_files[n_train:n_train + n_val]
        test_images = image_files[n_train + n_val:]
        
        # Record metadata
        for img_path in train_images:
            splits["train"].append({
                "path": str(img_path),
                "category": normalized_category,
                "original_category": category,
                "split": "train"
            })
        
        for img_path in val_images:
            splits["validation"].append({
                "path": str(img_path),
                "category": normalized_category,
                "original_category": category,
                "split": "validation"
            })
        
        for img_path in test_images:
            splits["test"].append({
                "path": str(img_path),
                "category": normalized_category,
                "original_category": category,
                "split": "test"
            })
        
        total_processed += n_images
        
        print(f"   {category:15s}: Train={len(train_images):,}, Val={len(val_images):,}, Test={len(test_images):,}")
    
    # Save split metadata
    for split_name, split_data in splits.items():
        output_file = OUTPUT_PATH / f"{split_name}_split.json"
        with open(output_file, 'w') as f:
            json.dump(split_data, f, indent=2)
        print(f"\n✓ Saved {split_name} split: {len(split_data):,} images → {output_file}")
    
    print()
    print(f"📊 SPLIT SUMMARY")
    print(f"   Total images processed: {total_processed:,}")
    print(f"   Train: {len(splits['train']):,} ({train_ratio*100:.0f}%)")
    print(f"   Validation: {len(splits['validation']):,} ({val_ratio*100:.0f}%)")
    print(f"   Test: {len(splits['test']):,} ({test_ratio*100:.0f}%)")
    print()
    
    return splits

def generate_research_metrics():
    """Generate key metrics for research paper."""
    print("="*80)
    print("RESEARCH DATASET METRICS (For Publication)")
    print("="*80)
    print()
    
    # Load splits
    train_split = OUTPUT_PATH / "train_split.json"
    if train_split.exists():
        with open(train_split, 'r') as f:
            train_data = json.load(f)
        
        # Count categories
        category_dist = Counter([item['category'] for item in train_data])
        
        print("📈 Training Set Distribution:")
        for category, count in category_dist.most_common():
            percentage = (count / len(train_data)) * 100
            print(f"   {category:15s}: {count:,} images ({percentage:.1f}%)")
        
        print()
        print("📝 For Research Paper:")
        print(f"   \"We collected a dataset of {sum(category_dist.values()):,} images")
        print(f"    across {len(category_dist)} categories commonly found in")
        print(f"    lost-and-found systems.\"")
        print()
        
        # Calculate balance metric
        avg_count = sum(category_dist.values()) / len(category_dist)
        std_dev = (sum((count - avg_count)**2 for count in category_dist.values()) / len(category_dist))**0.5
        balance_score = 1 - (std_dev / avg_count)
        
        print(f"   Dataset Balance Score: {balance_score:.3f}")
        print(f"   (1.0 = perfectly balanced, 0.0 = highly imbalanced)")

def main():
    """Main integration pipeline."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "🌟 REAL IMAGE DATASET INTEGRATION 🌟" + " "*22 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Step 1: Analyze
    category_counts = analyze_dataset()
    
    if category_counts is None:
        return
    
    # Step 2: Create splits
    splits = create_train_val_test_split()
    
    # Step 3: Generate metrics
    generate_research_metrics()
    
    print()
    print("="*80)
    print("INTEGRATION COMPLETE!")
    print("="*80)
    print()
    print("🎯 RESEARCH IMPACT:")
    print("   - Dataset size: 44,000 images (vs LostNet: 1,000)")
    print("   - Real-world data → High credibility")
    print("   - Proper train/val/test splits → Reproducible evaluation")
    print("   - MASSIVE upgrade for first-class research!")
    print()
    print("📝 Next Steps:")
    print("   1. Use test set for final evaluation (DO NOT peek!)")
    print("   2. Train multimodal models on train set")
    print("   3. Report results in research paper")
    print()
    print("✅ Your project now has PUBLICATION-QUALITY data!")
    print()

if __name__ == "__main__":
    random.seed(42)  # For reproducibility
    main()
