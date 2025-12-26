"""
Vision Transformer (ViT) Training Pipeline
Trains custom classifier on 44K lost-and-found images for robust detection

This addresses YOLOv8 limitations by creating a domain-specific classifier
optimized for your exact 11 categories.

Target: 98%+ accuracy (vs YOLOv8's variable performance)
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

# Category mapping
CATEGORIES = [
    'card', 'headphone', 'key', 'keyboard', 'laptop_charger',
    'laptop', 'mouse', 'phone', 'unknown', 'wallet', 'backpack'
]

class LostFoundDataset(Dataset):
    """Dataset for lost and found items - loads directly from Balanced_Dataset folder."""
    
    def __init__(self, data_dir, split='train', transform=None):
        """
        Args:
            data_dir: Path to Balanced_Dataset folder
            split: 'train', 'val', or 'test'
            transform: Image transformations
        """
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.category_to_idx = {cat: idx for idx, cat in enumerate(CATEGORIES)}
        
        # Load images from folders
        self.samples = []
        
        print(f"\nLoading {split} dataset from {data_dir}...")
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
            
            # Add to dataset
            for img_path in selected_images:
                self.samples.append({
                    'path': str(img_path),
                    'category': category,
                    'label': self.category_to_idx[category]
                })
            
            print(f"  {category:15s}: {len(selected_images):,} images")
        
        print(f"Total {split} samples: {len(self.samples):,}\n")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # Load image
        try:
            image = Image.open(sample['path']).convert('RGB')
        except Exception as e:
            print(f"Error loading {sample['path']}: {e}")
            # Return blank image if load fails
            image = Image.new('RGB', (224, 224))
        
        # Apply transforms
        if self.transform:
            image = self.transform(image)
        
        return image, sample['label'], sample['path']

def create_data_loaders(data_dir='Balanced_Dataset', batch_size=32):
    """Create train/val/test data loaders with augmentation."""
    
    # Image processor for ViT
    processor = ViTImageProcessor.from_pretrained('google/vit-base-patch16-224')
    
    # Training augmentation (important for generalization!)
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std)
    ])
    
    # Validation/Test (no augmentation)
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=processor.image_mean, std=processor.image_std)
    ])
    
    # Create datasets from Balanced_Dataset folder
    train_dataset = LostFoundDataset(data_dir, split='train', transform=train_transform)
    val_dataset = LostFoundDataset(data_dir, split='val', transform=eval_transform)
    test_dataset = LostFoundDataset(data_dir, split='test', transform=eval_transform)
    
    # Create dataloaders
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=4)
    
    print(f"Train samples: {len(train_dataset):,}")
    print(f"Validation samples: {len(val_dataset):,}")
    print(f"Test samples: {len(test_dataset):,}")
    
    return train_loader, val_loader, test_loader

def train_model(num_epochs=10, learning_rate=2e-5):
    """Train Vision Transformer on 44K images."""
    
    print("="*80)
    print("TRAINING VISION TRANSFORMER ON 44K LOST-AND-FOUND IMAGES")
    print("="*80)
    print()
    
    # Setup device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    if device.type == 'cuda':
        print(f"✓ GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"  GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"  CUDA Version: {torch.version.cuda}")
        
        # Enable GPU optimizations
        torch.backends.cudnn.benchmark = True
        print("✓ GPU optimizations enabled")
    else:
        print("⚠️  WARNING: No GPU detected! Training will be VERY SLOW.")
        print("   Make sure CUDA is installed and GPU drivers are up to date.")
    
    print()
    
    # Load pre-trained ViT
    print("Loading pre-trained Vision Transformer...")
    model = ViTForImageClassification.from_pretrained(
        'google/vit-base-patch16-224',
        num_labels=len(CATEGORIES),
        ignore_mismatched_sizes=True
    )
    model.to(device)
    
    # Use mixed precision for faster training on GPU
    use_amp = device.type == 'cuda'
    scaler = torch.cuda.amp.GradScaler() if use_amp else None
    if use_amp:
        print("✓ Mixed precision training enabled (faster GPU training)")
    
    # Create data loaders
    print("\nPreparing datasets...")
    train_loader, val_loader, test_loader = create_data_loaders(batch_size=32)
    
    # Optimizer and loss
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    criterion = nn.CrossEntropyLoss()
    
    # Learning rate scheduler
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=num_epochs)
    
    # Training loop
    best_val_acc = 0.0
    history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
    
    print(f"\nStarting training for {num_epochs} epochs...")
    print()
    
    for epoch in range(num_epochs):
        print(f"Epoch {epoch+1}/{num_epochs}")
        print("-" * 80)
        
        # Training phase
        model.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for images, labels, _ in tqdm(train_loader, desc="Training"):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass with mixed precision
            if use_amp:
                with torch.cuda.amp.autocast():
                    outputs = model(images).logits
                    loss = criterion(outputs, labels)
                
                # Backward pass with gradient scaling
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                # Regular training (CPU)
                outputs = model(images).logits
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
            
            # Statistics
            train_loss += loss.item()
            _, predicted = outputs.max(1)
            train_total += labels.size(0)
            train_correct += predicted.eq(labels).sum().item()
        
        train_loss /= len(train_loader)
        train_acc = 100. * train_correct / train_total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for images, labels, _ in tqdm(val_loader, desc="Validation"):
                images, labels = images.to(device), labels.to(device)
                
                outputs = model(images).logits
                loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                val_total += labels.size(0)
                val_correct += predicted.eq(labels).sum().item()
        
        val_loss /= len(val_loader)
        val_acc = 100. * val_correct / val_total
        
        # Update learning rate
        scheduler.step()
        
        # Save history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}%")
        print(f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'models/best_vit_lostfound.pth')
            print(f"✓ New best model saved! (Val Acc: {val_acc:.2f}%)")
        
        print()
    
    print("="*80)
    print(f"Training Complete! Best Validation Accuracy: {best_val_acc:.2f}%")
    print("="*80)
    
    return model, history

def evaluate_model(model, test_loader):
    """Evaluate model on test set."""
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    model.eval()
    
    all_preds = []
    all_labels = []
    
    print("\nEvaluating on test set...")
    
    with torch.no_grad():
        for images, labels, _ in tqdm(test_loader):
            images = images.to(device)
            outputs = model(images).logits
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(all_labels, all_preds, target_names=CATEGORIES))
    
    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=CATEGORIES, yticklabels=CATEGORIES)
    plt.title('Confusion Matrix - Vision Transformer on Lost & Found Items')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('results/confusion_matrix.png', dpi=300)
    print("✓ Confusion matrix saved to results/confusion_matrix.png")
    
    # Calculate accuracy
    accuracy = 100. * np.sum(np.array(all_preds) == np.array(all_labels)) / len(all_labels)
    print(f"\nTest Accuracy: {accuracy:.2f}%")
    
    return accuracy

if __name__ == "__main__":
    # Create directories
    Path("models").mkdir(exist_ok=True)
    Path("results").mkdir(exist_ok=True)
    
    # Train model
    model, history = train_model(num_epochs=10, learning_rate=2e-5)
    
    # Evaluate
    _, _, test_loader = create_data_loaders()
    test_accuracy = evaluate_model(model, test_loader)
    
    print("\n" + "="*80)
    print("TRAINING SUMMARY")
    print("="*80)
    print(f"Final Test Accuracy: {test_accuracy:.2f}%")
    print(f"Target (LostNet 2024): 96.8%")
    print(f"Your Result: {'✅ EXCEEDED!' if test_accuracy > 96.8 else '⏳ Keep training'}")
    print()
    print("Model saved to: models/best_vit_lostfound.pth")
    print("Ready to integrate into image validation pipeline!")
