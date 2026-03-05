# Enhanced YOLO to Lost & Found Category Mapping
# Maps YOLO's 80 COCO classes to Lost & Found categories

YOLO_TO_LOSTFOUND_MAPPING = {
    # Electronics - Direct Mapping
    "cell phone": "phone",
    "laptop": "laptop",
    "mouse": "mouse",
    "keyboard": "keyboard",
    "remote": "remote",
    "tv": "electronics",
    # YOLO COCO does not have a 'camera' class, but we map common misdetections
    # (e.g. camera body detected as 'cell phone' or 'book') to electronics
    "camera": "camera",          # May appear in custom/fine-tuned models
    "digital camera": "camera",
    "glasses": "glasses",
    "sunglasses": "glasses",
    "watch": "watch",
    "earphones": "electronics",
    "headphones": "electronics",
    
    # Personal Items - Bags & Accessories
    "handbag": "wallet",  # Closest match for wallet
    "backpack": "backpack",
    "suitcase": "luggage",
    "umbrella": "umbrella",
    "tie": "clothing",
    "jacket": "clothing",
    "coat": "clothing",
    
    # Small Personal Items
    "book": "book",
    "bottle": "bottle",
    "cup": "cup",
    "fork": "utensils",
    "knife": "utensils",
    "spoon": "utensils",
    
    # Wearables
    "person": None,  # Skip - not an item
    "bicycle": "bicycle",
    "car": None,  # Too large for lost & found
    "motorcycle": None,  # Too large
    "airplane": None,  # Not applicable
    "bus": None,  # Not applicable
    "train": None,  # Not applicable
    "truck": None,  # Not applicable
    "boat": None,  # Not applicable
    
    # Sports Equipment
    "sports ball": "ball",
    "baseball bat": "sports_equipment",
    "baseball glove": "sports_equipment",
    "skateboard": "skateboard",
    "surfboard": "sports_equipment",
    "tennis racket": "sports_equipment",
    "frisbee": "sports_equipment",
    "skis": "sports_equipment",
    "snowboard": "sports_equipment",
    "kite": "toy",
    
    # Common Items
    "clock": "clock",
    "vase": "decorative",
    "scissors": "scissors",
    "teddy bear": "toy",
    "hair drier": "electronics",
    "toothbrush": "personal_care",
    
    # Items that need ViT fallback (unmapped)
    # These will return None and trigger ViT detection
    "bench": None,
    "bird": None,
    "cat": None,
    "dog": None,
    "horse": None,
    "sheep": None,
    "cow": None,
    "elephant": None,
    "bear": None,
    "zebra": None,
    "giraffe": None,
    "traffic light": None,
    "fire hydrant": None,
    "stop sign": None,
    "parking meter": None,
    "dining table": None,
    "toilet": None,
    "couch": None,
    "potted plant": None,
    "bed": None,
    "chair": None,
    "refrigerator": None,
    "oven": None,
    "toaster": None,
    "sink": None,
    "microwave": None,
    "wine glass": "glass",
    "bowl": "bowl",
    "banana": None,
    "apple": None,
    "sandwich": None,
    "orange": None,
    "broccoli": None,
    "carrot": None,
    "hot dog": None,
    "pizza": None,
    "donut": None,
    "cake": None,
}

# ViT-specific categories (when YOLO fails)
VIT_EXCLUSIVE_CATEGORIES = [
    "key",  # Too small for YOLO
    "keychain",
    "card",  # ID cards, credit cards
    "headphone",  # Small earbuds/AirPods
    "laptop_charger",  # Specific item
    "wallet",  # If YOLO detects handbag with low confidence
]

def get_lostfound_category(yolo_class: str, vit_available: bool = True) -> tuple:
    """
    Map YOLO detection to Lost & Found category.
    
    Returns:
        tuple: (category: str | None, should_use_vit: bool)
    """
    if yolo_class in YOLO_TO_LOSTFOUND_MAPPING:
        category = YOLO_TO_LOSTFOUND_MAPPING[yolo_class]
        
        # If mapping is None, suggest ViT fallback
        if category is None and vit_available:
            return (None, True)
        
        return (category, False)
    
    # Unknown YOLO class - try ViT if available
    return (yolo_class, vit_available)
