"""
Benchmark Dataset Generator for Multimodal Validation System
Creates a reproducible, annotated test set for research evaluation.

Features:
- Diverse coverage of item types, quality levels, and modality combinations
- Intentional discrepancy cases (color, brand, location mismatches)
- Ground truth labels for validation decisions
- JSON schema for reproducibility

Dataset Structure:
- 200+ test cases across 10 item categories
- 3 quality levels (high, medium, low)
- 5 discrepancy types (color, brand, object, location, condition)
- Mixed modality combinations (image+text, image+text+voice, text-only)
"""

import json
import random
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """A single annotated test case."""
    id: str
    item_type: str
    item_category: str
    description: str
    location: str
    time_period: str
    
    # Quality annotations
    image_quality: str  # high, medium, low, none
    text_quality: str   # high, medium, low
    voice_quality: str  # high, medium, low, none
    
    # Ground truth
    expected_valid: bool
    expected_confidence: float
    
    # Discrepancy annotations
    has_discrepancy: bool = False
    discrepancy_type: Optional[str] = None  # color, brand, object, location, condition
    discrepancy_details: Optional[str] = None
    
    # Additional metadata
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


# Item categories with realistic lost & found scenarios
ITEM_CATEGORIES = {
    "electronics": {
        "items": ["iPhone", "Samsung Galaxy", "MacBook", "laptop", "tablet", "AirPods", "headphones", "smartwatch", "camera"],
        "brands": ["Apple", "Samsung", "Dell", "HP", "Sony", "Bose", "Lenovo", "Google"],
        "colors": ["black", "silver", "white", "gold", "rose gold", "blue", "space gray"],
    },
    "bags": {
        "items": ["backpack", "purse", "handbag", "messenger bag", "laptop bag", "gym bag", "duffel bag", "tote bag"],
        "brands": ["Nike", "Adidas", "Herschel", "JanSport", "Coach", "Michael Kors", "Under Armour"],
        "colors": ["black", "navy", "brown", "red", "pink", "gray", "blue", "green"],
    },
    "accessories": {
        "items": ["wallet", "keys", "sunglasses", "glasses", "watch", "umbrella", "charger", "power bank"],
        "brands": ["Ray-Ban", "Oakley", "Fossil", "Generic"],
        "colors": ["black", "brown", "silver", "gold", "tortoise"],
    },
    "clothing": {
        "items": ["jacket", "coat", "hoodie", "sweater", "hat", "cap", "scarf", "gloves"],
        "brands": ["North Face", "Patagonia", "Columbia", "Nike", "Adidas", "Uniqlo"],
        "colors": ["black", "navy", "red", "gray", "blue", "green", "white", "brown"],
    },
    "documents": {
        "items": ["passport", "ID card", "driver's license", "credit card", "student ID", "employee badge"],
        "brands": [],
        "colors": [],
    },
    "jewelry": {
        "items": ["ring", "necklace", "bracelet", "earrings", "watch"],
        "brands": ["Pandora", "Tiffany", "Swarovski", "Generic"],
        "colors": ["gold", "silver", "rose gold", "diamond", "pearl"],
    },
}

LOCATIONS = [
    "library", "cafeteria", "classroom", "lecture hall", "lab", "gym", 
    "parking lot", "auditorium", "office", "hallway", "restroom", 
    "entrance", "exit", "bus stop", "hostel", "student center", "bookstore"
]

TIME_PERIODS = ["morning", "afternoon", "evening", "night", "noon"]

IMPLAUSIBLE_COMBINATIONS = [
    ("laptop", "pool", None),          # Electronics don't belong at pool
    ("phone", "server room", None),    # Restricted area
    ("wallet", "gym", "midnight"),     # Gym closed at midnight
    ("ring", "parking lot", "morning"), # Valuables in open areas
    ("passport", "cafeteria", None),   # Sensitive document in casual area
]


class BenchmarkGenerator:
    """
    Generates a comprehensive benchmark dataset for evaluation.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the generator with a random seed for reproducibility.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        random.seed(seed)
        self.test_cases: List[TestCase] = []
    
    def _generate_id(self, item: str, idx: int) -> str:
        """Generate a unique test case ID."""
        hash_input = f"{item}_{idx}_{self.seed}"
        return f"tc_{hashlib.md5(hash_input.encode()).hexdigest()[:8]}"
    
    def _generate_description(self, item: str, color: Optional[str], brand: Optional[str], location: str, time: str) -> str:
        """Generate a realistic text description."""
        templates = [
            "I lost my {color} {brand} {item} at the {location} this {time}.",
            "Found a {color} {item} near the {location} {time}.",
            "Lost {brand} {item} ({color}) in the {location} area.",
            "My {item} was left at {location} around {time}. It's {color}.",
            "Looking for my {color} {brand} {item}, last seen at {location}.",
        ]
        
        template = random.choice(templates)
        
        # Handle missing fields
        if not color:
            template = template.replace("{color} ", "").replace("({color})", "").replace("It's {color}.", "")
        if not brand:
            template = template.replace("{brand} ", "")
        
        return template.format(
            color=color or "",
            brand=brand or "",
            item=item,
            location=location,
            time=time
        ).strip()
    
    def generate_positive_cases(self, count: int = 120) -> List[TestCase]:
        """Generate cases that should be validated as correct."""
        cases = []
        
        for i in range(count):
            category = random.choice(list(ITEM_CATEGORIES.keys()))
            cat_data = ITEM_CATEGORIES[category]
            
            item = random.choice(cat_data["items"])
            brand = random.choice(cat_data["brands"]) if cat_data["brands"] else None
            color = random.choice(cat_data["colors"]) if cat_data["colors"] else None
            location = random.choice(LOCATIONS)
            time_period = random.choice(TIME_PERIODS)
            
            # Vary quality levels
            quality_weights = [0.4, 0.4, 0.2]  # high, medium, low
            image_quality = random.choices(["high", "medium", "low"], weights=quality_weights)[0]
            text_quality = random.choices(["high", "medium", "low"], weights=[0.3, 0.5, 0.2])[0]
            
            # Some cases have voice input
            has_voice = random.random() < 0.3
            voice_quality = random.choice(["high", "medium", "low"]) if has_voice else "none"
            
            # Higher quality = higher expected confidence
            quality_scores = {"high": 0.9, "medium": 0.75, "low": 0.6}
            base_confidence = quality_scores[image_quality]
            if text_quality == "low":
                base_confidence -= 0.1
            if has_voice:
                base_confidence += 0.05
            
            case = TestCase(
                id=self._generate_id(item, i),
                item_type=item,
                item_category=category,
                description=self._generate_description(item, color, brand, location, time_period),
                location=location,
                time_period=time_period,
                image_quality=image_quality,
                text_quality=text_quality,
                voice_quality=voice_quality,
                expected_valid=True,
                expected_confidence=round(min(1.0, max(0.5, base_confidence + random.uniform(-0.1, 0.1))), 2),
                tags=[category, image_quality],
            )
            cases.append(case)
        
        return cases
    
    def generate_discrepancy_cases(self, count: int = 50) -> List[TestCase]:
        """Generate cases with intentional discrepancies."""
        cases = []
        discrepancy_types = ["color", "brand", "object", "location", "condition"]
        
        for i in range(count):
            disc_type = random.choice(discrepancy_types)
            category = random.choice(list(ITEM_CATEGORIES.keys()))
            cat_data = ITEM_CATEGORIES[category]
            
            item = random.choice(cat_data["items"])
            location = random.choice(LOCATIONS)
            time_period = random.choice(TIME_PERIODS)
            
            # Generate discrepancy
            if disc_type == "color" and cat_data["colors"]:
                true_color = random.choice(cat_data["colors"])
                wrong_color = random.choice([c for c in cat_data["colors"] if c != true_color] or [true_color])
                description = f"Lost my {wrong_color} {item} at the {location}."
                details = f"Image shows {true_color}, text says {wrong_color}"
            
            elif disc_type == "brand" and cat_data["brands"]:
                true_brand = random.choice(cat_data["brands"])
                wrong_brand = random.choice([b for b in cat_data["brands"] if b != true_brand] or [true_brand])
                description = f"Found a {wrong_brand} {item} at {location}."
                details = f"Image shows {true_brand} logo, text says {wrong_brand}"
            
            elif disc_type == "object":
                # Different object type
                other_items = [it for it in cat_data["items"] if it != item]
                wrong_item = random.choice(other_items) if other_items else item
                description = f"Lost my {wrong_item} at {location}."
                details = f"Image shows {item}, text describes {wrong_item}"
            
            elif disc_type == "location":
                wrong_location = random.choice([loc for loc in LOCATIONS if loc != location])
                description = f"Found a {item} at the {wrong_location}."
                details = f"Metadata says {location}, text says {wrong_location}"
            
            else:  # condition
                description = f"Lost my brand new {item} at {location}."
                details = "Image shows worn/damaged item, text says 'brand new'"
            
            case = TestCase(
                id=self._generate_id(f"disc_{item}", i),
                item_type=item,
                item_category=category,
                description=description,
                location=location,
                time_period=time_period,
                image_quality="high",  # Good quality to make discrepancy clear
                text_quality="high",
                voice_quality="none",
                expected_valid=False,
                expected_confidence=round(random.uniform(0.3, 0.55), 2),
                has_discrepancy=True,
                discrepancy_type=disc_type,
                discrepancy_details=details,
                tags=["discrepancy", disc_type],
            )
            cases.append(case)
        
        return cases
    
    def generate_implausible_cases(self, count: int = 20) -> List[TestCase]:
        """Generate cases with implausible spatial-temporal combinations."""
        cases = []
        
        for i in range(count):
            if i < len(IMPLAUSIBLE_COMBINATIONS):
                item, location, time = IMPLAUSIBLE_COMBINATIONS[i]
            else:
                # Generate more implausible combinations
                item = random.choice(["laptop", "phone", "passport", "wallet"])
                location = random.choice(["pool", "server room", "restricted area"])
                time = random.choice(["midnight", "3am", None])
            
            time_period = time or random.choice(TIME_PERIODS)
            
            case = TestCase(
                id=self._generate_id(f"implaus_{item}", i),
                item_type=item,
                item_category="electronics" if item in ["laptop", "phone"] else "accessories",
                description=f"Lost my {item} at the {location} around {time_period}.",
                location=location,
                time_period=time_period,
                image_quality="medium",
                text_quality="high",
                voice_quality="none",
                expected_valid=False,
                expected_confidence=round(random.uniform(0.35, 0.5), 2),
                has_discrepancy=False,
                discrepancy_type=None,
                discrepancy_details=None,
                tags=["implausible", "spatial_temporal"],
                notes=f"Implausible: {item} at {location}",
            )
            cases.append(case)
        
        return cases
    
    def generate_low_quality_cases(self, count: int = 30) -> List[TestCase]:
        """Generate cases with very low quality inputs."""
        cases = []
        
        for i in range(count):
            category = random.choice(list(ITEM_CATEGORIES.keys()))
            cat_data = ITEM_CATEGORIES[category]
            item = random.choice(cat_data["items"])
            location = random.choice(LOCATIONS)
            
            # Low quality descriptions
            low_quality_descriptions = [
                f"lost {item}",
                f"found something at {location}",
                "lost my stuff",
                f"anyone seen a {item}?",
                "help",
            ]
            
            case = TestCase(
                id=self._generate_id(f"lowq_{item}", i),
                item_type=item,
                item_category=category,
                description=random.choice(low_quality_descriptions),
                location=location,
                time_period=random.choice(TIME_PERIODS),
                image_quality="low",
                text_quality="low",
                voice_quality="none",
                expected_valid=False,  # Rejected due to quality
                expected_confidence=round(random.uniform(0.2, 0.45), 2),
                tags=["low_quality", "incomplete"],
            )
            cases.append(case)
        
        return cases
    
    def generate_full_benchmark(self, 
                                positive_count: int = 120,
                                discrepancy_count: int = 50,
                                implausible_count: int = 20,
                                low_quality_count: int = 30) -> List[TestCase]:
        """
        Generate the complete benchmark dataset.
        
        Default: ~220 test cases with balanced distribution.
        """
        logger.info("Generating benchmark dataset...")
        
        self.test_cases = []
        
        # Generate all case types
        self.test_cases.extend(self.generate_positive_cases(positive_count))
        logger.info(f"  Generated {positive_count} positive cases")
        
        self.test_cases.extend(self.generate_discrepancy_cases(discrepancy_count))
        logger.info(f"  Generated {discrepancy_count} discrepancy cases")
        
        self.test_cases.extend(self.generate_implausible_cases(implausible_count))
        logger.info(f"  Generated {implausible_count} implausible cases")
        
        self.test_cases.extend(self.generate_low_quality_cases(low_quality_count))
        logger.info(f"  Generated {low_quality_count} low quality cases")
        
        # Shuffle to mix case types
        random.shuffle(self.test_cases)
        
        logger.info(f"Total benchmark size: {len(self.test_cases)} cases")
        return self.test_cases
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the generated benchmark."""
        if not self.test_cases:
            return {}
        
        stats = {
            "total_cases": len(self.test_cases),
            "expected_valid": sum(1 for tc in self.test_cases if tc.expected_valid),
            "expected_invalid": sum(1 for tc in self.test_cases if not tc.expected_valid),
            "validation_rate": sum(1 for tc in self.test_cases if tc.expected_valid) / len(self.test_cases),
            "by_category": {},
            "by_quality": {"high": 0, "medium": 0, "low": 0},
            "discrepancy_types": {},
            "avg_expected_confidence": sum(tc.expected_confidence for tc in self.test_cases) / len(self.test_cases),
        }
        
        for tc in self.test_cases:
            # By category
            stats["by_category"][tc.item_category] = stats["by_category"].get(tc.item_category, 0) + 1
            
            # By quality
            if tc.image_quality in stats["by_quality"]:
                stats["by_quality"][tc.image_quality] += 1
            
            # Discrepancy types
            if tc.has_discrepancy and tc.discrepancy_type:
                stats["discrepancy_types"][tc.discrepancy_type] = stats["discrepancy_types"].get(tc.discrepancy_type, 0) + 1
        
        return stats
    
    def save(self, output_path: str = "data/ground_truth.json"):
        """Save benchmark to JSON file."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        output = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0.0",
                "seed": self.seed,
                "description": "Multimodal Validation System Benchmark Dataset",
            },
            "statistics": self.get_statistics(),
            "test_cases": [asdict(tc) for tc in self.test_cases],
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Benchmark saved to: {output_path}")
        return output_path
    
    def generate_splits(self, train_ratio: float = 0.6, val_ratio: float = 0.2) -> Dict[str, List[TestCase]]:
        """
        Split benchmark into train/validation/test sets.
        
        Args:
            train_ratio: Fraction for training (calibration)
            val_ratio: Fraction for validation
        
        Returns:
            Dictionary with 'train', 'val', 'test' keys
        """
        if not self.test_cases:
            self.generate_full_benchmark()
        
        n = len(self.test_cases)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))
        
        # Shuffle with seed
        shuffled = self.test_cases.copy()
        random.Random(self.seed).shuffle(shuffled)
        
        return {
            "train": shuffled[:train_end],
            "val": shuffled[train_end:val_end],
            "test": shuffled[val_end:],
        }


def main():
    """Generate and save benchmark dataset."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate benchmark dataset')
    parser.add_argument('--output', default='data/ground_truth.json', help='Output path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--positive', type=int, default=120, help='Number of positive cases')
    parser.add_argument('--discrepancy', type=int, default=50, help='Number of discrepancy cases')
    parser.add_argument('--implausible', type=int, default=20, help='Number of implausible cases')
    parser.add_argument('--low-quality', type=int, default=30, help='Number of low quality cases')
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("BENCHMARK DATASET GENERATOR")
    print(f"{'='*60}")
    
    generator = BenchmarkGenerator(seed=args.seed)
    generator.generate_full_benchmark(
        positive_count=args.positive,
        discrepancy_count=args.discrepancy,
        implausible_count=args.implausible,
        low_quality_count=args.low_quality,
    )
    
    # Print statistics
    stats = generator.get_statistics()
    print(f"\nDataset Statistics:")
    print(f"  Total cases: {stats['total_cases']}")
    print(f"  Expected valid: {stats['expected_valid']} ({stats['validation_rate']:.1%})")
    print(f"  Expected invalid: {stats['expected_invalid']}")
    print(f"  Avg confidence: {stats['avg_expected_confidence']:.2f}")
    
    print(f"\nBy Category:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"  {cat}: {count}")
    
    print(f"\nBy Quality (image):")
    for qual, count in stats['by_quality'].items():
        print(f"  {qual}: {count}")
    
    if stats['discrepancy_types']:
        print(f"\nDiscrepancy Types:")
        for disc_type, count in stats['discrepancy_types'].items():
            print(f"  {disc_type}: {count}")
    
    # Save
    generator.save(args.output)
    
    # Generate splits
    splits = generator.generate_splits()
    print(f"\nData Splits:")
    for split_name, cases in splits.items():
        print(f"  {split_name}: {len(cases)} cases")
    
    print(f"\n✅ Benchmark generated: {args.output}")


if __name__ == "__main__":
    main()
