"""
Automated Project Reorganization Script
Cleans up root directory by moving files to organized folders
"""

import os
import shutil
from pathlib import Path

# Base directory
BASE_DIR = Path(".")

# Create new directories
DIRS_TO_CREATE = {
    "training": "Training scripts and model fine-tuning",
    "scripts": "Utility and helper scripts",
    "demos": "Demo and example scripts",
    "docs": "Documentation and guides",
    "logs": "Log files and outputs"
}

# File movements
MOVES = {
    "training": [
        "train_vit_classifier.py",
        "train_vit_colab.py",
        "update_knowledge_graph.py",
        "integrate_real_images.py"
    ],
    "scripts": [
        "download_datasets.py",
        "download_models.py",
        "check_env.py",
        "list_gemini_models.py"
    ],
    "demos": [
        "text_demo.py",
        "audio_demo.py",
        "clip_demo.py",
        "multimodal_demo.py",
        "demo.py"
    ],
    "tests": [  # Consolidate with existing tests/
        "test_full_api.py",
        "test_api_response.py",
        "test_llm_direct.py",
        "verify_gemini.py",
        "test_active_learning.py",
        "test_knowledge_graph.py",
        "test_llm_intelligence.py",
        "test_scenarios.py",
        "test_new_features.py",
        "reproduce_brand_issue.py",
        "reproduce_plausibility.py"
    ],
    "docs": [
        "GPU_SETUP_GUIDE.md",
        "VIT_TRAINING_GUIDE.md",
        "API_README.md"
    ],
    "logs": [
        "test_results.log",
        "test_output.txt",
        "server.out.log",
        "server.err.log",
        "uvicorn.out"
    ]
}

# Files to delete
FILES_TO_DELETE = [
    "gemini_models.txt",
    "yolov8n.pt",  # Duplicate (exists in models/)
    "# Comprehensive Agentic AI Builder.txt"  # Unknown
]

def create_directories():
    """Create new organization directories."""
    print("\n" + "="*80)
    print("STEP 1: Creating Directories")
    print("="*80)
    
    for dir_name, description in DIRS_TO_CREATE.items():
        dir_path = BASE_DIR / dir_name
        if not dir_path.exists():
            dir_path.mkdir(exist_ok=True)
            print(f"✓ Created {dir_name}/ - {description}")
        else:
            print(f"  {dir_name}/ already exists")

def move_files():
    """Move files to their new locations."""
    print("\n" + "="*80)
    print("STEP 2: Moving Files")
    print("="*80)
    
    moved_count = 0
    skipped_count = 0
    
    for dest_dir, files in MOVES.items():
        print(f"\nMoving to {dest_dir}/:")
        dest_path = BASE_DIR / dest_dir
        
        for filename in files:
            src = BASE_DIR / filename
            dst = dest_path / filename
            
            if src.exists():
                try:
                    shutil.move(str(src), str(dst))
                    print(f"  ✓ {filename}")
                    moved_count += 1
                except Exception as e:
                    print(f"  ✗ {filename} - Error: {e}")
                    skipped_count += 1
            else:
                print(f"  ⊘ {filename} - Not found")
                skipped_count += 1
    
    print(f"\nMoved: {moved_count}, Skipped: {skipped_count}")

def delete_files():
    """Delete redundant files."""
    print("\n" + "="*80)
    print("STEP 3: Deleting Redundant Files")
    print("="*80)
    
    deleted_count = 0
    
    for filename in FILES_TO_DELETE:
        file_path = BASE_DIR / filename
        if file_path.exists():
            try:
                if file_path.is_file():
                    file_path.unlink()
                    print(f"  ✓ Deleted {filename}")
                    deleted_count += 1
            except Exception as e:
                print(f"  ✗ {filename} - Error: {e}")
        else:
            print(f"  ⊘ {filename} - Not found")
    
    print(f"\nDeleted: {deleted_count} files")

def generate_summary():
    """Generate summary of current structure."""
    print("\n" + "="*80)
    print("STEP 4: New Project Structure")
    print("="*80)
    
    # Count files in each directory
    for dir_name in ["training", "scripts", "demos", "tests", "docs", "logs"]:
        dir_path = BASE_DIR / dir_name
        if dir_path.exists():
            file_count = len(list(dir_path.glob("*.py"))) + len(list(dir_path.glob("*.md")))
            print(f"  📂 {dir_name}/  ({file_count} files)")
    
    # Root files
    root_files = [f for f in BASE_DIR.glob("*") if f.is_file() and not f.name.startswith(".")]
    print(f"\n  📄 Root directory: {len(root_files)} files (cleaned!)")

def main():
    """Run the reorganization."""
    print("\n" + "="*80)
    print("PROJECT REORGANIZATION SCRIPT")
    print("="*80)
    print("\nThis will:")
    print("  • Create organized folders (training/, scripts/, demos/, docs/, logs/)")
    print("  • Move files to appropriate locations")
    print("  • Delete redundant files")
    print()
    
    response = input("Proceed with reorganization? (yes/no): ").strip().lower()
    
    if response != "yes":
        print("\n❌ Reorganization cancelled.")
        return
    
    print("\n🚀 Starting reorganization...")
    
    # Execute steps
    create_directories()
    move_files()
    delete_files()
    generate_summary()
    
    print("\n" + "="*80)
    print("✅ REORGANIZATION COMPLETE!")
    print("="*80)
    print("\nYour project is now clean and organized!")
    print("\nNext steps:")
    print("  1. Review the new structure")
    print("  2. Update any hardcoded paths in your code")
    print("  3. Test that everything still works")
    print()

if __name__ == "__main__":
    main()
