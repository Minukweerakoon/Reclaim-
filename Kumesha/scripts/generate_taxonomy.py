# Script to generate extended taxonomy priors for spatial_temporal_validator.py
# Run this to generate code to paste into the validator

# Extended items (40 new items to add)
NEW_ITEMS = {
    # More Electronics
    "camera": {"library": 0.60, "cafeteria": 0.40, "classroom": 0.70, "lab": 0.80, "gym": 0.30, "parking": 0.25, "auditorium": 0.85, "office": 0.75, "hallway": 0.35, "restroom": 0.15, "entrance": 0.30, "bus stop": 0.35, "hostel": 0.70, "pool": 0.40, "server room": 0.50},
    "charger": {"library": 0.90, "cafeteria": 0.85, "classroom": 0.90, "lab": 0.85, "gym": 0.50, "parking": 0.30, "auditorium": 0.75, "office": 0.90, "hallway": 0.50, "restroom": 0.40, "entrance": 0.35, "bus stop": 0.40, "hostel": 0.95, "pool": 0.15, "server room": 0.80},
    "powerbank": {"library": 0.85, "cafeteria": 0.80, "classroom": 0.85, "lab": 0.75, "gym": 0.60, "parking": 0.40, "auditorium": 0.70, "office": 0.80, "hallway": 0.55, "restroom": 0.45, "entrance": 0.40, "bus stop": 0.50, "hostel": 0.85, "pool": 0.20, "server room": 0.60},
    "earbuds": {"library": 0.85, "cafeteria": 0.75, "classroom": 0.80, "lab": 0.70, "gym": 0.90, "parking": 0.45, "auditorium": 0.80, "office": 0.70, "hallway": 0.65, "restroom": 0.55, "entrance": 0.50, "bus stop": 0.70, "hostel": 0.85, "pool": 0.50, "server room": 0.35},
    "calculator": {"library": 0.90, "cafeteria": 0.60, "classroom": 0.95, "lab": 0.90, "gym": 0.10, "parking": 0.15, "auditorium": 0.65, "office": 0.85, "hallway": 0.40, "restroom": 0.20, "entrance": 0.25, "bus stop": 0.25, "hostel": 0.75, "pool": 0.05, "server room": 0.45},
    
    # Documents
    "notebook": {"library": 0.95, "cafeteria": 0.70, "classroom": 0.95, "lab": 0.85, "gym": 0.15, "parking": 0.20, "auditorium": 0.80, "office": 0.90, "hallway": 0.50, "restroom": 0.25, "entrance": 0.30, "bus stop": 0.35, "hostel": 0.85, "pool": 0.05, "server room": 0.40},
    "textbook": {"library": 0.95, "cafeteria": 0.65, "classroom": 0.95, "lab": 0.80, "gym": 0.10, "parking": 0.15, "auditorium": 0.75, "office": 0.85, "hallway": 0.45, "restroom": 0.20, "entrance": 0.25, "bus stop": 0.30, "hostel": 0.90, "pool": 0.03, "server room": 0.35},
    "folder": {"library": 0.90, "cafeteria": 0.60, "classroom": 0.90, "lab": 0.85, "gym": 0.10, "parking": 0.20, "auditorium": 0.70, "office": 0.95, "hallway": 0.50, "restroom": 0.25, "entrance": 0.30, "bus stop": 0.25, "hostel": 0.70, "pool": 0.05, "server room": 0.55},
    "idcard": {"library": 0.70, "cafeteria": 0.80, "classroom": 0.75, "lab": 0.70, "gym": 0.85, "parking": 0.75, "auditorium": 0.75, "office": 0.90, "hallway": 0.80, "restroom": 0.85, "entrance": 0.90, "bus stop": 0.70, "hostel": 0.90, "pool": 0.80, "server room": 0.65},
   
    # More Clothing/Accessories
    "shoes": {"library": 0.30, "cafeteria": 0.40, "classroom": 0.35, "lab": 0.25, "gym": 0.95, "parking": 0.50, "auditorium": 0.45, "office": 0.30, "hallway": 0.60, "restroom": 0.70, "entrance": 0.65, "bus stop": 0.55, "hostel": 0.85, "pool": 0.90, "server room": 0.10},
    "hat": {"library": 0.45, "cafeteria": 0.60, "classroom": 0.50, "lab": 0.35, "gym": 0.65, "parking": 0.60, "auditorium": 0.70, "office": 0.45, "hallway": 0.70, "restroom": 0.50, "entrance": 0.75, "bus stop": 0.80, "hostel": 0.70, "pool": 0.85, "server room": 0.15},
    "scarf": {"library": 0.65, "cafeteria": 0.70, "classroom": 0.70, "lab": 0.55, "gym": 0.60, "parking": 0.50, "auditorium": 0.75, "office": 0.65, "hallway": 0.75, "restroom": 0.55, "entrance": 0.80, "bus stop": 0.85, "hostel": 0.75, "pool": 0.20, "server room": 0.20},
    "purse": {"library": 0.80, "cafeteria": 0.90, "classroom": 0.80, "lab": 0.65, "gym": 0.85, "parking": 0.75, "auditorium": 0.85, "office": 0.80, "hallway": 0.75, "restroom": 0.90, "entrance": 0.70, "bus stop": 0.80, "hostel": 0.85, "pool": 0.70, "server room": 0.25},
    "luggage": {"library": 0.20, "cafeteria": 0.40, "classroom": 0.25, "lab": 0.15, "gym": 0.40, "parking": 0.85, "auditorium": 0.50, "office": 0.35, "hallway": 0.70, "restroom": 0.35, "entrance": 0.90, "bus stop": 0.95, "hostel": 0.90, "pool": 0.30, "server room": 0.20},
    
    # Sports/Activities
    "waterbottle": {"library": 0.70, "cafeteria": 0.85, "classroom": 0.75, "lab": 0.60, "gym": 0.95, "parking": 0.50, "auditorium": 0.70, "office": 0.75, "hallway": 0.65, "restroom": 0.55, "entrance": 0.55, "bus stop": 0.60, "hostel": 0.85, "pool": 0.90, "server room": 0.40},
    "gymbag": {"library": 0.30, "cafeteria": 0.50, "classroom": 0.35, "lab": 0.20, "gym": 0.95, "parking": 0.65, "auditorium": 0.40, "office": 0.30, "hallway": 0.60, "restroom": 0.75, "entrance": 0.70, "bus stop": 0.70, "hostel": 0.90, "pool": 0.85, "server room": 0.10},
    
    # Instruments
    "flute": {"auditorium": 0.95, "classroom": 0.85, "hostel": 0.80, "library": 0.15, "cafeteria": 0.25, "lab": 0.10, "gym": 0.10, "parking": 0.35, "office": 0.20, "hallway": 0.35, "restroom": 0.05, "entrance": 0.35, "bus stop": 0.45, "pool": 0.03, "server room": 0.02},
    "violin": {"auditorium": 0.95, "classroom": 0.90, "hostel": 0.80, "library": 0.15, "cafeteria": 0.20, "lab": 0.08, "gym": 0.10, "parking": 0.40, "office": 0.15, "hallway": 0.35, "restroom": 0.05, "entrance": 0.40, "bus stop": 0.50, "pool": 0.02, "server room": 0.01},
    
    # Personal Care
    "makeupbag": {"library": 0.35, "cafeteria": 0.60, "classroom": 0.40, "lab": 0.25, "gym": 0.75, "parking": 0.45, "auditorium": 0.50, "office": 0.55, "hallway": 0.50, "restroom": 0.90, "entrance": 0.40, "bus stop": 0.45, "hostel": 0.90, "pool": 0.85, "server room": 0.10},
    "lunchbox": {"library": 0.60, "cafeteria": 0.95, "classroom": 0.70, "lab": 0.55, "gym": 0.50, "parking": 0.40, "auditorium": 0.55, "office": 0.80, "hallway": 0.60, "restroom": 0.30, "entrance": 0.45, "bus stop": 0.60, "hostel": 0.85, "pool": 0.25, "server room": 0.35},
}

# Generate TIME_PRIORS for new items (using common patterns)
TIME_PATTERNS = {
    "electronics": {"early_morning": 0.35, "morning": 0.80, "noon": 0.80, "afternoon": 0.90, "evening": 0.80, "night": 0.55, "late_night": 0.25},
    "documents": {"early_morning": 0.30, "morning": 0.90, "noon": 0.85, "afternoon": 0.90, "evening": 0.70, "night": 0.45, "late_night": 0.20},
    "clothing": {"early_morning": 0.50, "morning": 0.75, "noon": 0.70, "afternoon": 0.80, "evening": 0.85, "night": 0.60, "late_night": 0.35},
    "sports": {"early_morning": 0.55, "morning": 0.75, "noon": 0.70, "afternoon": 0.85, "evening": 0.95, "night": 0.50, "late_night": 0.20},
    "instruments": {"early_morning": 0.20, "morning": 0.60, "noon": 0.70, "afternoon": 0.85, "evening": 0.95, "night": 0.70, "late_night": 0.30},
    "personal": {"early_morning": 0.45, "morning": 0.75, "noon": 0.80, "afternoon": 0.85, "evening": 0.80, "night": 0.60, "late_night": 0.35},
}

# Category mapping for new items
ITEM_CATEGORIES = {
    "camera": "electronics", "charger": "electronics", "powerbank": "electronics", "earbuds": "electronics", "calculator": "electronics",
    "notebook": "documents", "textbook": "documents", "folder": "documents", "idcard": "documents",
    "shoes": "clothing", "hat": "clothing", "scarf": "clothing", "purse": "clothing", "luggage": "clothing",
    "waterbottle": "sports", "gymbag": "sports",
    "flute": "instruments", "violin": "instruments",
    "makeupbag": "personal", "lunchbox": "personal",
}

# Generate output
print("# ADD TO LOCATION_PRIORS:")
for item, priors in NEW_ITEMS.items():
    print(f'        "{item}": {priors},')

print("\n# ADD TO TIME_PRIORS:")
for item, category in ITEM_CATEGORIES.items():
    print(f'        "{item}": {TIME_PATTERNS[category]},')

print("\n# ADD TO ITEM_CATEGORY_MAP:")
print('        # Extended Electronics')
print('        "phone charger": "charger", "power bank": "powerbank", "portable charger": "powerbank",')
print('        "airpods": "earbuds", "earphones": "earbuds", "calc": "calculator",')
print('        # Documents')
print('        "notes": "notebook", "journal": "notebook", "book": "textbook", "id": "idcard", "card": "idcard",')
print('        # Accessories')  
print('        "sneakers": "shoes", "boots": "shoes", "cap": "hat", "beanie": "hat", "handbag": "purse", "suitcase": "luggage",')
print('        # Sports')
print('        "bottle": "waterbottle", "water bottle": "waterbottle", "gym bag": "gymbag", "sports bag": "gymbag",')
print('        # Instruments')
print('        "fluit": "flute", "fiddle": "violin",')
print('        # Personal')
print('        "makeup": "makeupbag", "cosmetics": "makeupbag", "lunch": "lunchbox", "lunchcontainer": "lunchbox",')

print("\n✅ Generated extended taxonomy - Copy and paste into spatial_temporal_validator.py")
