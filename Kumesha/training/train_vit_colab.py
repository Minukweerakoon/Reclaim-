"""
Colab-Compatible Training Script for Vision Transformer
Works with Google Drive or uploaded Balanced_Dataset

SETUP INSTRUCTIONS FOR COLAB:
1. Upload this file to Colab
2. Upload your Balanced_Dataset folder to Colab OR mount Google Drive
3. Run the cells below
"""

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import json
from pathlib import Path
from tqdm import tqdm
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Category mapping
CATEGORIES = [
    'Card', 'Headphone', 'Key', 'Keyboard', 'Lapcharger',
    'Laptop', 'Mouse', 'Smartphone', 'Unknown', 'Wallets', 'backpack'
]

class LostFoundDatasetColab(Dataset):
    """Dataset for Colab - loads images directly from Balanced_Dataset folder."""
    
    def __init__(self, data_dir, split='train', transform=None, max_samples_per_category=None):
        """
        Args:
            data_dir: Path to Balanced_Dataset folder
            split: 'train', 'val', or 'test'
            transform: Image transformations
            max_samples_per_category: Limit samples for faster testing (None = all)
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.category_to_idx = {cat: idx for idx, cat in enumerate(CATEGORIES)}
        
        # Load images from folders
        self.samples = []
        
        for category in CATEGORIES:
            category_dir = self.data_dir / category
            
            if not category_dir.exists():
                print(f"⚠️  Warning: {category_dir} not found, skipping...")
                continue
            
            # Get all images
            image_files = list(category_dir.glob("*.jpg")) + \
                         list(category_dir.glob("*.jpeg")) + \
                         list(category_dir.glob("*.png"))
            
            # Create train/val/test split (70/15/15)
            n_images = len(image_files)
            n_train = int(n_images * 0.70)
            n_val = int(n_images * 0.15)
            
            if split == 'train':
                selected_images = image_files[:n_train]
            elif split == 'val':
                selected_images = image_files[n_train:n_train + n_val]
            else:  # test
                selected_images = image_files[n_train + n_val:]
            
            # Limit if max_samples set (for quick testing)
            if max_samples_per_category:
                selected_images = selected_images[:max_samples_per_category]
            
            # Add to dataset
            for img_path in selected_images:
                self.samples.append({
                    'path': str(img_path),
                    'category': category,
                    'label': self.category_to_idx[category]
                })
        
        print(f"{split.upper()} dataset: {len(self.samples)} images across {len(set(s['category'] for s in self.samples))} categories")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load image
        try:
            image = Image.open(sample['path']).convert('RGB')
        except Exception as e:
            print(f"Error loading {sample['path']}: {e}")
            # Return a blank image if load fails
            image = Image.new('RGB', (224, 224))
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        return image, sample['label'], sample['path']

def create_data_loaders_colab(data_dir, batch_size=32, quick_test=False):
    """
    Create data loaders for Colab.
    
    Args:
        data_dir: Path to Balanced_Dataset folder
        batch_size: Batch size
        quick_test: If True, use only 100 samples per category for fast testing
    """
    
    # Image processor for ViT
    processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
    
    # Training augmentation
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std)
    ])
    
    # Validation/Test (no augmentation)
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std)
    ])
    
    max_samples = 100 if quick_test else None
    
    # Create datasets
    train_dataset = LostFoundDatasetColab(data_dir, 'train', train_transform, max_samples)
    val_dataset = LostFoundDatasetColab(data_dir, 'val', eval_transform, max_samples)
    test_dataset = LostFoundDatasetColab(data_dir, 'test', eval_transform, max_samples)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    
    return train_loader, val_loader, test_loader

# COLAB SETUP CELL
def setup_colab():
    """
    Run this first in Colab to set up environment.
    Choose Option A (upload) or Option B (Google Drive)
    """
    
    print("="*80)
    print("GOOGLE COLAB SETUP")
    print("="*80)
    print()
    print("Choose how to access your images:")
    print()
    print("Option A: Upload Balanced_Dataset folder (SLOW - ~10GB)")
    print("Option B: Mount Google Drive (RECOMMENDED)")
    print()
    
    # Option B is recommended
    choice = input("Enter A or B: ").strip().upper()
    
    if choice == 'B':
        from google.colab import drive
        drive.mount('/content/drive')
        print("\n✓ Google Drive mounted!")
        print("Make sure Balanced_Dataset is in: /content/drive/MyDrive/Balanced_Dataset")
        data_dir = '/content/drive/MyDrive/Balanced_Dataset'
    else:
        print("\nUpload your Balanced_Dataset folder using the file browser on the left")
        data_dir = '/content/Balanced_Dataset'
    
    return data_dir

# Example usage in Colab:
"""
# Cell 1: Install dependencies
!pip install transformers torch torchvision scikit-learn seaborn

# Cell 2: Setup
data_dir = setup_colab()

# Cell 3: Quick test (100 samples per category)
train_loader, val_loader, test_loader = create_data_loaders_colab(
    data_dir, 
    batch_size=32,
    quick_test=True  # Set False for full training
)

# Cell 4: Load model
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = ViTForImageClassification.from_pretrained(
    'google/vit-base-patch16-224',
    num_labels=11,
    ignore_mismatched_sizes=True
)
model.to(device)

# Cell 5: Train (copy train_model function from main script)
# ... training code ...
"""

print("✅ Colab-compatible script ready!")
print("Copy this to Google Colab and run the example cells above")
