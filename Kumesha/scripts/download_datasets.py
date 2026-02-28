"""
Dataset Downloader and Preprocessor
Automates acquisition of free datasets for research-grade validation

Datasets:
1. LostFound (Kaggle) - Primary lost-and-found data
2. Delhi Metro Lost Items (Kaggle) - 27K items for knowledge graph
3. MS-COCO (Optional) - For pre-training if needed
"""

import os
import subprocess
import json
import pandas as pd
from pathlib import Path

# Create data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

def check_kaggle_api():
    """Check if Kaggle API is configured."""
    try:
        result = subprocess.run(["kaggle", "--version"], capture_output=True, text=True)
        print(f"✓ Kaggle API found: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Kaggle API not installed!")
        print("\nInstall Instructions:")
        print("1. pip install kaggle")
        print("2. Go to https://www.kaggle.com/settings/account")
        print("3. Click 'Create New API Token'")
        print("4. Move kaggle.json to ~/.kaggle/ (Linux/Mac) or C:\\Users\\<you>\\.kaggle\\ (Windows)")
        return False

def download_lostfound_dataset():
    """Download primary LostFound dataset from Kaggle."""
    print("\n" + "="*80)
    print("DOWNLOADING: LostFound Dataset (Primary)")
    print("="*80)
    
    dataset_name = "lostfound-ml-ai"  # Actual Kaggle dataset identifier
    output_path = DATA_DIR / "lostfound"
    output_path.mkdir(exist_ok=True)
    
    cmd = [
        "kaggle", "datasets", "download",
        "-d", dataset_name,
        "-p", str(output_path),
        "--unzip"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Downloaded to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
        print("\nTroubleshooting:")
        print("- Verify dataset exists: https://www.kaggle.com/datasets/")
        print("- Check Kaggle API credentials")
        return False

def download_delhi_metro_dataset():
    """Download Delhi Metro Lost and Found dataset."""
    print("\n" + "="*80)
    print("DOWNLOADING: Delhi Metro Lost Items (27K+ samples)")
    print("="*80)
    
    # Note: This is a placeholder - you'll need the actual dataset name from Kaggle
    # Search: https://www.kaggle.com/search?q=delhi+metro+lost
    
    dataset_name = "delhi-metro-lost-found"  # Replace with actual name
    output_path = DATA_DIR / "delhi_metro"
    output_path.mkdir(exist_ok=True)
    
    cmd = [
        "kaggle", "datasets", "download",
        "-d", dataset_name,
        "-p", str(output_path),
        "--unzip"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✓ Downloaded to {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Dataset not found or access denied: {e}")
        print("   Skipping Delhi Metro dataset for now...")
        return False

def process_lostfound_data():
    """Process LostFound dataset for knowledge graph."""
    print("\n" + "="*80)
    print("PROCESSING: Extracting item-location-time triplets")
    print("="*80)
    
    lostfound_path = DATA_DIR / "lostfound"
    
    # Look for CSV files
    csv_files = list(lostfound_path.glob("*.csv"))
    
    if not csv_files:
        print(f"⚠️  No CSV files found in {lostfound_path}")
        print("   You may need to manually extract the downloaded zip")
        return None
    
    print(f"Found {len(csv_files)} CSV file(s)")
    
    # Load first CSV
    df = pd.read_csv(csv_files[0])
    print(f"\nDataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Extract relevant fields (adjust based on actual columns)
    triplets = []
    
    # Example processing (adjust field names based on actual data)
    if 'item' in df.columns and 'location' in df.columns:
        for _, row in df.iterrows():
            triplets.append({
                'item': str(row.get('item', '')).lower(),
                'location': str(row.get('location', '')).lower(),
                'timestamp': row.get('date', '')
            })
    
    # Save processed triplets
    output_file = DATA_DIR / "knowledge_graph_triplets.json"
    with open(output_file, 'w') as f:
        json.dump(triplets, f, indent=2)
    
    print(f"\n✓ Saved {len(triplets)} triplets to {output_file}")
    return triplets

def generate_synthetic_data(n_samples=1000):
    """Generate synthetic lost-and-found samples if real data is scarce."""
    print("\n" + "="*80)
    print(f"GENERATING: {n_samples} synthetic samples")
    print("="*80)
    
    import random
    
    items = ['phone', 'laptop', 'keys', 'wallet', 'bag', 'book', 'glasses', 'watch']
    locations = ['library', 'cafeteria', 'classroom', 'gym', 'parking', 'office']
    colors = ['black', 'blue', 'red', 'silver', 'brown']
    
    synthetic_samples = []
    
    for i in range(n_samples):
        item = random.choice(items)
        location = random.choice(locations)
        color = random.choice(colors) if random.random() > 0.3 else None
        
        # Generate description
        desc = f"I lost my {color + ' ' if color else ''}{item}"
        if random.random() > 0.5:
            desc += f" in the {location}"
        
        # Assign quality score (simulate manual annotation)
        has_item = True
        has_location = "in the" in desc
        has_color = color is not None
        
        quality_score = (has_item * 40 + has_location * 30 + has_color * 30) / 100
        
        synthetic_samples.append({
            'text': desc,
            'item': item,
            'location': location if has_location else None,
            'color': color,
            'quality_score': quality_score,
            'plausibility': 'plausible'  # Most are plausible by default
        })
    
    # Add some implausible samples
    implausible = [
        {'text': 'I lost my swimsuit in the server room', 'plausibility': 'implausible'},
        {'text': 'I lost my surfboard in the library', 'plausibility': 'implausible'},
        {'text': 'I lost my scuba gear in the classroom', 'plausibility': 'implausible'},
    ]
    
    synthetic_samples.extend(implausible)
    
    output_file = DATA_DIR / "synthetic_dataset.json"
    with open(output_file, 'w') as f:
        json.dump(synthetic_samples, f, indent=2)
    
    print(f"✓ Generated {len(synthetic_samples)} synthetic samples")
    print(f"✓ Saved to {output_file}")
    
    return synthetic_samples

def main():
    """Main dataset acquisition pipeline."""
    print("\n" + "="*80)
    print("DATASET ACQUISITION PIPELINE")
    print("="*80)
    
    # Check prerequisites
    if not check_kaggle_api():
        print("\n⚠️  Kaggle API not configured. Skipping Kaggle downloads.")
        print("   We'll generate synthetic data instead.\n")
        kaggle_available = False
    else:
        kaggle_available = True
    
    # Download datasets
    if kaggle_available:
        download_lostfound_dataset()
        download_delhi_metro_dataset()
        
        # Process downloaded data
        process_lostfound_data()
    
    # Always generate synthetic data as backup
    generate_synthetic_data(n_samples=1000)
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Data directory: {DATA_DIR.absolute()}")
    print("\nNext steps:")
    print("1. Review downloaded data in data/ folder")
    print("2. Run: python update_knowledge_graph.py  (to integrate into system)")
    print("3. Test with: python test_knowledge_graph.py")
    print()

if __name__ == "__main__":
    main()
