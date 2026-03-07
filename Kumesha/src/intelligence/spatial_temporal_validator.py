"""
Spatial-Temporal Context Validation Module (Novel Feature #1)
Research-Grade Bayesian Probabilistic Plausibility Assessment

This module implements a Bayesian probabilistic model to validate the plausibility
of lost/found item reports based on spatial (location) and temporal (time) context.

Mathematical Model:
    Plausibility = P(Location|Item) × P(Time|Item) × Context_Weight

Example:
    P(Laptop|Library, 2pm) = 0.90  ✅ Highly plausible
    P(Swimsuit|Server Room, 9am) = 0.001  ❌ Highly implausible

Research Contribution:
    First system to apply Bayesian plausibility scoring to Lost & Found validation.
"""

import logging
import math
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class SpatialTemporalValidator:
    """
    Bayesian Probabilistic Validator for Spatial-Temporal Context.
    
    Uses learned patterns and prior probability distributions to assess
    whether a reported item-location-time combination is plausible.
    """
    
    # ------------------------------------------------------------------ #
    # Prior Probability Matrices (Static Defaults)
    # ------------------------------------------------------------------ #
    
    # P(Location|Item) - Probability of finding item at location
    # Values are normalized probabilities (0.0 to 1.0)
    LOCATION_PRIORS: Dict[str, Dict[str, float]] = {
        # Electronics
        "phone": {
            "library": 0.85, "cafeteria": 0.80, "classroom": 0.85, "lab": 0.70,
            "gym": 0.60, "parking": 0.50, "auditorium": 0.75, "office": 0.80,
            "hallway": 0.65, "restroom": 0.55, "entrance": 0.50, "bus stop": 0.60,
            "hostel": 0.70, "pool": 0.20, "server room": 0.15
        },
        "laptop": {
            "library": 0.95, "cafeteria": 0.60, "classroom": 0.90, "lab": 0.95,
            "gym": 0.15, "parking": 0.20, "auditorium": 0.70, "office": 0.95,
            "hallway": 0.30, "restroom": 0.10, "entrance": 0.25, "bus stop": 0.20,
            "hostel": 0.80, "pool": 0.05, "server room": 0.85
        },
        "tablet": {
            "library": 0.90, "cafeteria": 0.65, "classroom": 0.85, "lab": 0.85,
            "gym": 0.20, "parking": 0.25, "auditorium": 0.75, "office": 0.90,
            "hallway": 0.35, "restroom": 0.15, "entrance": 0.30, "bus stop": 0.30,
            "hostel": 0.75, "pool": 0.10, "server room": 0.60
        },
        "headphones": {
            "library": 0.90, "cafeteria": 0.70, "classroom": 0.80, "lab": 0.75,
            "gym": 0.85, "parking": 0.40, "auditorium": 0.80, "office": 0.70,
            "hallway": 0.60, "restroom": 0.30, "entrance": 0.45, "bus stop": 0.65,
            "hostel": 0.80, "pool": 0.40, "server room": 0.30
        },
        "watch": {
            "library": 0.70, "cafeteria": 0.65, "classroom": 0.70, "lab": 0.60,
            "gym": 0.90, "parking": 0.50, "auditorium": 0.65, "office": 0.70,
            "hallway": 0.55, "restroom": 0.85, "entrance": 0.50, "bus stop": 0.55,
            "hostel": 0.75, "pool": 0.90, "server room": 0.25
        },
        # Bags and Personal Items
        "wallet": {
            "library": 0.75, "cafeteria": 0.90, "classroom": 0.75, "lab": 0.60,
            "gym": 0.85, "parking": 0.70, "auditorium": 0.80, "office": 0.75,
            "hallway": 0.65, "restroom": 0.85, "entrance": 0.60, "bus stop": 0.75,
            "hostel": 0.80, "pool": 0.85, "server room": 0.20
        },
        "bag": {
            "library": 0.90, "cafeteria": 0.85, "classroom": 0.90, "lab": 0.80,
            "gym": 0.90, "parking": 0.60, "auditorium": 0.85, "office": 0.80,
            "hallway": 0.70, "restroom": 0.50, "entrance": 0.65, "bus stop": 0.80,
            "hostel": 0.85, "pool": 0.75, "server room": 0.30
        },
        "backpack": {
            "library": 0.95, "cafeteria": 0.85, "classroom": 0.95, "lab": 0.85,
            "gym": 0.85, "parking": 0.55, "auditorium": 0.85, "office": 0.70,
            "hallway": 0.70, "restroom": 0.40, "entrance": 0.65, "bus stop": 0.80,
            "hostel": 0.90, "pool": 0.60, "server room": 0.25
        },
        "keys": {
            "library": 0.65, "cafeteria": 0.80, "classroom": 0.70, "lab": 0.65,
            "gym": 0.80, "parking": 0.90, "auditorium": 0.70, "office": 0.85,
            "hallway": 0.75, "restroom": 0.85, "entrance": 0.80, "bus stop": 0.70,
            "hostel": 0.90, "pool": 0.75, "server room": 0.40
        },
        "umbrella": {
            "library": 0.80, "cafeteria": 0.85, "classroom": 0.80, "lab": 0.65,
            "gym": 0.50, "parking": 0.40, "auditorium": 0.80, "office": 0.75,
            "hallway": 0.85, "restroom": 0.60, "entrance": 0.90, "bus stop": 0.90,
            "hostel": 0.80, "pool": 0.30, "server room": 0.15
        },
        # Clothing/Sports
        "jacket": {
            "library": 0.85, "cafeteria": 0.85, "classroom": 0.85, "lab": 0.70,
            "gym": 0.80, "parking": 0.50, "auditorium": 0.90, "office": 0.80,
            "hallway": 0.80, "restroom": 0.60, "entrance": 0.85, "bus stop": 0.85,
            "hostel": 0.85, "pool": 0.40, "server room": 0.25
        },
        "glasses": {
            "library": 0.90, "cafeteria": 0.75, "classroom": 0.85, "lab": 0.80,
            "gym": 0.60, "parking": 0.45, "auditorium": 0.80, "office": 0.85,
            "hallway": 0.65, "restroom": 0.75, "entrance": 0.55, "bus stop": 0.60,
            "hostel": 0.80, "pool": 0.80, "server room": 0.45
        },
        "swimsuit": {
            "library": 0.05, "cafeteria": 0.10, "classroom": 0.05, "lab": 0.02,
            "gym": 0.70, "parking": 0.15, "auditorium": 0.05, "office": 0.03,
            "hallway": 0.10, "restroom": 0.60, "entrance": 0.15, "bus stop": 0.10,
            "hostel": 0.60, "pool": 0.95, "server room": 0.01
        },
        "sports_equipment": {
            "library": 0.10, "cafeteria": 0.20, "classroom": 0.15, "lab": 0.05,
            "gym": 0.95, "parking": 0.50, "auditorium": 0.30, "office": 0.15,
            "hallway": 0.40, "restroom": 0.30, "entrance": 0.45, "bus stop": 0.35,
            "hostel": 0.70, "pool": 0.60, "server room": 0.02
        },
        # Musical Instruments
        "guitar": {
            "auditorium": 0.95, "classroom": 0.90, "hostel": 0.85,
            "library": 0.10, "cafeteria": 0.30, "lab": 0.10,
            "gym": 0.15, "parking": 0.40, "office": 0.20,
            "hallway": 0.40, "restroom": 0.05, "entrance": 0.40, "bus stop": 0.50,
            "pool": 0.05, "server room": 0.01
        },
    }
    
    # P(Time|Item) - Probability of losing item at time of day
    TIME_PRIORS: Dict[str, Dict[str, float]] = {
        "phone": {
            "early_morning": 0.40, "morning": 0.75, "noon": 0.85, "afternoon": 0.90,
            "evening": 0.85, "night": 0.60, "late_night": 0.30
        },
        "laptop": {
            "early_morning": 0.30, "morning": 0.85, "noon": 0.80, "afternoon": 0.90,
            "evening": 0.75, "night": 0.50, "late_night": 0.20
        },
        "tablet": {
            "early_morning": 0.35, "morning": 0.80, "noon": 0.85, "afternoon": 0.90,
            "evening": 0.80, "night": 0.55, "late_night": 0.25
        },
        "headphones": {
            "early_morning": 0.50, "morning": 0.80, "noon": 0.75, "afternoon": 0.85,
            "evening": 0.80, "night": 0.65, "late_night": 0.40
        },
        "watch": {
            "early_morning": 0.45, "morning": 0.70, "noon": 0.75, "afternoon": 0.80,
            "evening": 0.85, "night": 0.70, "late_night": 0.50
        },
        "wallet": {
            "early_morning": 0.35, "morning": 0.80, "noon": 0.90, "afternoon": 0.85,
            "evening": 0.80, "night": 0.60, "late_night": 0.40
        },
        "bag": {
            "early_morning": 0.40, "morning": 0.85, "noon": 0.85, "afternoon": 0.90,
            "evening": 0.85, "night": 0.55, "late_night": 0.30
        },
        "backpack": {
            "early_morning": 0.45, "morning": 0.90, "noon": 0.85, "afternoon": 0.90,
            "evening": 0.80, "night": 0.50, "late_night": 0.25
        },
        "keys": {
            "early_morning": 0.60, "morning": 0.80, "noon": 0.75, "afternoon": 0.80,
            "evening": 0.85, "night": 0.70, "late_night": 0.55
        },
        "umbrella": {
            "early_morning": 0.50, "morning": 0.85, "noon": 0.80, "afternoon": 0.90,
            "evening": 0.85, "night": 0.60, "late_night": 0.35
        },
        "jacket": {
            "early_morning": 0.55, "morning": 0.80, "noon": 0.70, "afternoon": 0.85,
            "evening": 0.90, "night": 0.65, "late_night": 0.40
        },
        "glasses": {
            "early_morning": 0.45, "morning": 0.75, "noon": 0.80, "afternoon": 0.85,
            "evening": 0.80, "night": 0.60, "late_night": 0.35
        },
        "swimsuit": {
            "early_morning": 0.30, "morning": 0.70, "noon": 0.85, "afternoon": 0.90,
            "evening": 0.60, "night": 0.20, "late_night": 0.10
        },
        "sports_equipment": {
            "early_morning": 0.50, "morning": 0.75, "noon": 0.70, "afternoon": 0.85,
            "evening": 0.90, "night": 0.45, "late_night": 0.20
        },
        "guitar": {
            "early_morning": 0.20, "morning": 0.60, "noon": 0.70, "afternoon": 0.85,
            "evening": 0.95, "night": 0.70, "late_night": 0.30
        },
    }
    
    # Item category mapping for unknown items
    ITEM_CATEGORY_MAP: Dict[str, str] = {
        # Electronics
        "iphone": "phone", "samsung": "phone", "smartphone": "phone", 
        "mobile": "phone", "cellphone": "phone", "android": "phone",
        "macbook": "laptop", "notebook": "laptop", "chromebook": "laptop",
        "keyboard": "laptop", "mouse": "laptop", "charger": "laptop",
        "ipad": "tablet", "headset": "headphones", "airpods": "headphones", "earbuds": "headphones",
        "beats": "headphones", "beats by dre": "headphones", "beats solo": "headphones",
        "wireless headphones": "headphones", "bluetooth headset": "headphones",
        "earphones": "headphones", "smartwatch": "watch", "apple watch": "watch",
        # Accesssories
        "key": "keys", "car key": "keys", "house key": "keys", "fob": "keys",
        # Bags
        "purse": "bag", "handbag": "bag", "suitcase": "bag", "luggage": "bag",
        "tote": "bag", "messenger bag": "bag", "duffel": "bag",
        # Sports/Clothing
        "goggles": "swimsuit", "swim cap": "swimsuit", "towel": "swimsuit",
        "sunglasses": "glasses", "spectacles": "glasses",
        "coat": "jacket", "hoodie": "jacket", "sweater": "jacket",
        "ball": "sports_equipment", "racket": "sports_equipment",
        "yoga mat": "sports_equipment",
        # Musical Instruments
        "acoustic guitar": "guitar", "electric guitar": "guitar", 
        "bass": "guitar", "bass guitar": "guitar", "ukulele": "guitar",
    }
    
    # Location aliases for normalization
    LOCATION_ALIASES: Dict[str, str] = {
        "canteen": "cafeteria", "food court": "cafeteria", "mess": "cafeteria", "cafe": "cafeteria", "dining": "cafeteria",
        "reading room": "library", "study room": "library", "study area": "library", "study": "library",
        "lecture hall": "classroom", "seminar room": "classroom", "faculty": "classroom", "lecture": "classroom", "class": "classroom",
        "computer lab": "lab", "research lab": "lab", "computing": "lab", "laboratory": "lab",
        "locker room": "gym", "fitness center": "gym", "sports hall": "gym", "ground": "gym", "stadium": "gym",
        "parking lot": "parking", "garage": "parking", "car park": "parking", "parking area": "parking", "parking space": "parking",
        "main entrance": "entrance", "gate": "entrance", "lobby": "entrance", "foyer": "entrance", "reception": "entrance",
        "bathroom": "restroom", "toilet": "restroom", "washroom": "restroom", "lavatory": "restroom",
        "corridor": "hallway", "passage": "hallway", "stairs": "hallway", "staircase": "hallway",
        "dorm": "hostel", "dormitory": "hostel", "residence": "hostel", "accommodation": "hostel", "room": "hostel",
        "swimming pool": "pool", "aquatic center": "pool",
        "data center": "server room", "it room": "server room",
        "building": "office", "department": "office", "headquarters": "office", "hq": "office",
    }
    
    # Time period mapping
    TIME_PERIODS = {
        "early_morning": (5, 7),   # 5am - 7am
        "morning": (7, 12),        # 7am - 12pm
        "noon": (12, 14),          # 12pm - 2pm
        "afternoon": (14, 17),     # 2pm - 5pm
        "evening": (17, 21),       # 5pm - 9pm
        "night": (21, 24),         # 9pm - 12am
        "late_night": (0, 5),      # 12am - 5am
    }
    
    def __init__(self):
        """Initialize the Spatial-Temporal Validator with hybrid learning."""
        self.learned_location_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.learned_time_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.total_observations: int = 0
        
        # Weights for combining static priors with learned data
        self.static_weight = 0.7  # Weight for static priors
        self.learned_weight = 0.3  # Weight for learned patterns
        
        # Load learned patterns from database (if available)
        self._load_from_database()
        
        logger.info(
            f"SpatialTemporalValidator initialized with {self.total_observations} learned observations"
        )
    
    def normalize_item(self, item: str) -> str:
        """Normalize item name to known category."""
        item_lower = item.lower().strip()
        
        # Direct match
        if item_lower in self.LOCATION_PRIORS:
            return item_lower
        
        # Mapped match
        if item_lower in self.ITEM_CATEGORY_MAP:
            return self.ITEM_CATEGORY_MAP[item_lower]
        
        # Partial match
        for key in self.ITEM_CATEGORY_MAP:
            if key in item_lower or item_lower in key:
                return self.ITEM_CATEGORY_MAP[key]
        
        for key in self.LOCATION_PRIORS:
            if key in item_lower or item_lower in key:
                return key
        
        return "unknown"
    
    def normalize_location(self, location: str) -> str:
        """Normalize location name."""
        loc_lower = location.lower().strip()
        
        # Direct match
        if loc_lower in list(self.LOCATION_PRIORS.get("phone", {}).keys()):
            return loc_lower
        
        # Aliased match
        if loc_lower in self.LOCATION_ALIASES:
            return self.LOCATION_ALIASES[loc_lower]
        
        # Partial match
        for alias, canonical in self.LOCATION_ALIASES.items():
            if alias in loc_lower or loc_lower in alias:
                return canonical
        
        for canon in self.LOCATION_PRIORS.get("phone", {}).keys():
            if canon in loc_lower or loc_lower in canon:
                return canon
        
        return "unknown"
    
    def normalize_time(self, time_input: str) -> str:
        """Normalize time input to time period."""
        time_lower = time_input.lower().strip()
        
        # Direct period match
        if time_lower in self.TIME_PERIODS:
            return time_lower
        
        # Keyword mapping
        time_keywords = {
            "early morning": "early_morning",
            "dawn": "early_morning",
            "morning": "morning",
            "am": "morning",
            "noon": "noon",
            "lunch": "noon",
            "midday": "noon",
            "afternoon": "afternoon",
            "pm": "afternoon",
            "evening": "evening",
            "dusk": "evening",
            "night": "night",
            "late night": "late_night",
            "midnight": "late_night",
        }
        
        for keyword, period in time_keywords.items():
            if keyword in time_lower:
                return period
        
        # Try to parse time (e.g., "9am", "14:30", "2pm")
        try:
            import re
            # Match patterns like "9am", "2pm", "4 p.m.", "14:30"
            hour_match = re.search(r'(\d{1,2})\s*([ap]\.?m\.?|:\d{2})?', time_lower)
            if hour_match:
                hour = int(hour_match.group(1))
                raw_ampm = hour_match.group(2)
                
                # Normalize am/pm (remove dots)
                ampm = raw_ampm.replace('.', '').lower() if raw_ampm else None
                
                if ampm and 'pm' in ampm and hour < 12:
                    hour += 12
                elif ampm and 'am' in ampm and hour == 12:
                    hour = 0
                
                # Map hour to period
                for period, (start, end) in self.TIME_PERIODS.items():
                    if start <= hour < end or (period == "late_night" and (hour < 5 or hour >= 24)):
                        return period
        except Exception:
            pass
        
        return "unknown"  # No default assumption
    
    def get_location_probability(self, item: str, location: str) -> float:
        """
        Get P(Location|Item) using hybrid approach.
        Combines static priors with learned patterns.
        """
        norm_item = self.normalize_item(item)
        norm_location = self.normalize_location(location)
        
        # Get static prior
        static_prob = self.LOCATION_PRIORS.get(norm_item, {}).get(norm_location, 0.5)
        
        # Get learned probability (if we have enough data)
        learned_prob = 0.5
        if norm_item in self.learned_location_counts:
            item_counts = self.learned_location_counts[norm_item]
            total = sum(item_counts.values())
            if total >= 5:  # Minimum observations to use learned data
                learned_prob = item_counts.get(norm_location, 0) / total
                learned_prob = max(0.1, min(0.95, learned_prob))  # Clamp
        
        # Combine with weighting (favor learned if we have enough data)
        if self.total_observations >= 100:
            # More data = more trust in learned patterns
            effective_learned_weight = min(0.6, self.learned_weight + 0.01 * (self.total_observations / 100))
            effective_static_weight = 1.0 - effective_learned_weight
        else:
            effective_static_weight = self.static_weight
            effective_learned_weight = self.learned_weight
        
        combined_prob = (effective_static_weight * static_prob) + (effective_learned_weight * learned_prob)
        return round(combined_prob, 3)
    
    def get_time_probability(self, item: str, time_period: str) -> float:
        """
        Get P(Time|Item) using hybrid approach.
        """
        if time_period == "unknown":
            return 0.5 # Neutral probability for unknown time
            
        norm_item = self.normalize_item(item)
        norm_time = self.normalize_time(time_period)
        
        # Get static prior
        static_prob = self.TIME_PRIORS.get(norm_item, {}).get(norm_time, 0.6)
        
        # Get learned probability
        learned_prob = 0.6
        if norm_item in self.learned_time_counts:
            item_counts = self.learned_time_counts[norm_item]
            total = sum(item_counts.values())
            if total >= 5:
                learned_prob = item_counts.get(norm_time, 0) / total
                learned_prob = max(0.1, min(0.95, learned_prob))
        
        # Combine
        if self.total_observations >= 100:
            effective_learned_weight = min(0.6, self.learned_weight + 0.01 * (self.total_observations / 100))
            effective_static_weight = 1.0 - effective_learned_weight
        else:
            effective_static_weight = self.static_weight
            effective_learned_weight = self.learned_weight
        
        combined_prob = (effective_static_weight * static_prob) + (effective_learned_weight * learned_prob)
        return round(combined_prob, 3)
    
    def calculate_plausibility(
        self,
        item: str,
        location: str,
        time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate the Bayesian plausibility score for an item-location-time combination.
        """
        norm_item = self.normalize_item(item)
        norm_location = self.normalize_location(location)
        norm_time = self.normalize_time(time) if time else "unknown"
        
        # Get individual probabilities
        p_location = self.get_location_probability(item, location)
        
        if norm_time != "unknown":
            p_time = self.get_time_probability(item, norm_time)
            # Bayesian combination: Plausibility = P(Location|Item) × P(Time|Item)
            raw_plausibility = p_location * p_time
            # Apply smoothing
            plausibility_score = round(math.pow(raw_plausibility, 0.6), 2)
            time_display = norm_time
        else:
            p_time = 0.0
            # If time is unknown, rely mostly on location but dampen slightly to reflect uncertainty
            # Using sqrt(p_location) to be charitable like the power 0.6 above, 
            # but maybe just p_location is fair.
            # Let's use p_location * 0.9 to prevent perfect scores without full context?
            # Or just p_location. Let's stick to p_location logic similar to above.
            raw_plausibility = p_location
            # Apply similar smoothing but maybe distinct for single variable
            plausibility_score = round(math.pow(raw_plausibility, 0.7), 2)
            time_display = "unspecified"
        
        # Determine validity threshold (initial statistical)
        is_valid = plausibility_score >= 0.40
        
        # --- LLM INTELLIGENCE FALLBACK ---
        # If the statistical model fails to identify the context or gives a low score,
        # fallback to the advanced reasoning of Gemini/Groq.
        llm_used = False
        explanation = ""
        
        if not is_valid or norm_location == "unknown" or norm_item == "unknown":
            try:
                from src.intelligence.llm_client import get_llm_client
                import json
                llm = get_llm_client()
                
                if llm.provider in ["gemini", "openai"]:
                    prompt = f"""
Analyze the real-world plausibility of this lost & found scenario:
Item: {item}
Location: {location}
Time: {time if time else 'Not specified'}

Based on human behavior and environmental logic, is it plausible to find this item here?
Return ONLY a valid JSON object:
{{
  "plausibility_score": <float between 0.01 and 0.99>,
  "valid": <boolean (true if score >= 0.40)>,
  "explanation": "<Concise, friendly explanation starting with an emoji (e.g. ✅ or ⚠️)>"
}}
"""
                    response_text = ""
                    if llm.provider == "gemini":
                        response_text = llm._call_gemini_with_retry(prompt, use_fallback=True)
                    else:
                        response = llm.openai_client.chat.completions.create(
                            model=llm.model,
                            messages=[{"role": "user", "content": prompt}],
                            response_format={"type": "json_object"}
                        )
                        response_text = response.choices[0].message.content
                    
                    data = json.loads(response_text)
                    plausibility_score = float(data.get("plausibility_score", plausibility_score))
                    is_valid = bool(data.get("valid", is_valid))
                    explanation = data.get("explanation", explanation)
                    llm_used = True
                    logger.info(f"LLM Plausibility Fallback Success for {item} at {location} -> Score: {plausibility_score}")
            except Exception as e:
                logger.warning(f"LLM Plausibility Fallback failed: {e}")
        
        # Generate statistical explanation if LLM wasn't used or failed
        if not llm_used or not explanation:
            explanation = self._generate_explanation(
                norm_item, norm_location, time_display,
                p_location, p_time, plausibility_score, is_valid
            )
        
        # Generate suggestions for low plausibility
        suggestions = []
        if not is_valid:
            suggestions = self._generate_suggestions(norm_item, norm_location, norm_time if norm_time != "unknown" else "")
        
        return {
            "plausibility_score": plausibility_score,
            "valid": is_valid,
            "location_probability": p_location,
            "time_probability": p_time if norm_time != "unknown" else None,
            "explanation": explanation,
            "suggestions": suggestions,
            "normalized_inputs": {
                "item": norm_item,
                "location": norm_location,
                "time": time_display,
                "original_item": item,
                "original_location": location,
                "original_time": time
            },
            "confidence_level": self._get_confidence_level(plausibility_score)
        }
    
    def _get_confidence_level(self, score: float) -> str:
        """Map score to human-readable confidence level."""
        if score >= 0.80:
            return "very_high"
        elif score >= 0.60:
            return "high"
        elif score >= 0.40:
            return "moderate"
        elif score >= 0.20:
            return "low"
        else:
            return "very_low"
    
    def _generate_explanation(
        self,
        item: str, location: str, time: str,
        p_loc: float, p_time: float, score: float, valid: bool
    ) -> str:
        """Generate human-readable explanation for the plausibility score."""
        
        if item == "unknown":
            return "⚠️ Could not identify the item type to verify plausibility."
            
        if location == "unknown":
            return "⚠️ Could not identify the location to verify plausibility."

        item_display = item.replace("_", " ").title()
        location_display = location.replace("_", " ").title()
        time_display = time.replace("_", " ").title()
        
        # Proper pluralization helper
        def pluralize(word: str) -> str:
            word = word.replace("_", " ").title()
            if word.lower().endswith("y") and word.lower() not in ["key", "boy", "day", "guy", "toy"]:
                return word[:-1] + "ies"
            return word + "s"

        item_plural = pluralize(item)
        location_plural = pluralize(location)

        time_part = f"during {time_display} hours" if time != "unspecified" else "at an unspecified time"
        if time == "unspecified":
            time_part = "(time not specified)"
        
        if score >= 0.80:
            return (
                f"✅ Very plausible! {item_plural} are commonly found in {location_plural}."
                + (f" The {time_display} timing matches patterns." if time != "unspecified" else "")
            )
        elif score >= 0.60:
            return (
                f"✅ Plausible. {item_plural} are sometimes found in {location_plural}."
            )
        elif score >= 0.40:
            return (
                f"⚠️ Somewhat unusual. {item_plural} are not commonly found in {location_plural}, "
                f"but it's still possible."
            )
        elif score >= 0.20:
            return (
                f"⚠️ Unusual combination. A {item_display} in a {location_display} {time_part} "
                f"is uncommon. Please verify the details."
            )
        else:
            return (
                f"❌ Highly unusual! Finding a {item_display} in a {location_display} "
                f"is very rare. Please double-check your report."
            )
    
    def _generate_suggestions(self, item: str, location: str, time: str) -> List[str]:
        """Generate suggestions for more plausible combinations."""
        suggestions = []
        
        # Find better locations for this item
        if item in self.LOCATION_PRIORS:
            item_priors = self.LOCATION_PRIORS[item]
            best_locations = sorted(item_priors.items(), key=lambda x: x[1], reverse=True)[:3]
            if best_locations:
                locations_str = ", ".join([loc.replace("_", " ").title() for loc, _ in best_locations])
                suggestions.append(
                    f"📍 {item.replace('_', ' ').title()}s are most commonly found in: {locations_str}"
                )
        
        # Find better times for this item (only if time was specified or we want to educate)
        if time and item in self.TIME_PRIORS:
            time_priors = self.TIME_PRIORS[item]
            best_times = sorted(time_priors.items(), key=lambda x: x[1], reverse=True)[:2]
            if best_times:
                times_str = ", ".join([t.replace("_", " ").title() for t, _ in best_times])
                suggestions.append(
                    f"⏰ {item.replace('_', ' ').title()}s are typically lost during: {times_str}"
                )
        
        # Generic suggestion
        suggestions.append(
            "💡 If you're sure about the details, please add more context to your description."
        )
        
        return suggestions
    
    def record_validated_item(self, item: str, location: str, time: Optional[str] = None) -> None:
        """
        Record a validated item to update learned patterns.
        Also persists to database for long-term learning.
        """
        norm_item = self.normalize_item(item)
        norm_location = self.normalize_location(location)
        # Only record time if it was actually provided
        norm_time = self.normalize_time(time) if time else "unknown"
        
        if norm_item != "unknown" and norm_location != "unknown":
            # Update in-memory counts
            self.learned_location_counts[norm_item][norm_location] += 1
            if norm_time != "unknown":
                self.learned_time_counts[norm_item][norm_time] += 1
            
            self.total_observations += 1
            
            # Persist to database
            self._save_to_database(norm_item, norm_location, norm_time)
            
            logger.debug(
                f"Recorded observation: {norm_item} at {norm_location} "
                f"{f'during {norm_time}' if norm_time != 'unknown' else '(no time)'}. "
                f"Total observations: {self.total_observations}"
            )
    
    def _load_from_database(self) -> None:
        """Load learned patterns from database on initialization."""
        try:
            from src.database.db import DatabaseManager
            import os
            
            if not os.getenv("DATABASE_URL"):
                logger.debug("DATABASE_URL not configured, skipping pattern loading")
                return
            
            db = DatabaseManager()
            patterns = db.load_spatial_temporal_patterns()
            
            # Convert database format to in-memory format
            for item, locations in patterns["location"].items():
                for loc, count in locations.items():
                    self.learned_location_counts[item][loc] = count
            
            for item, times in patterns["time"].items():
                for time_p, count in times.items():
                    self.learned_time_counts[item][time_p] = count
            
            # Calculate total observations
            self.total_observations = sum(
                sum(locs.values()) for locs in self.learned_location_counts.values()
            )
            
            logger.info(f"Loaded {self.total_observations} learned patterns from database")
            
        except Exception as e:
            logger.warning(f"Failed to load patterns from database: {e}")
            # Continue with empty learned patterns
    
    def _save_to_database(self, item: str, location: str, time: Optional[str] = None) -> None:
        """Persist a single observation to database."""
        try:
            from src.database.db import DatabaseManager
            import os
            
            if not os.getenv("DATABASE_URL"):
                return  # Silently skip if DB not configured
            
            db = DatabaseManager()
            db.save_spatial_temporal_pattern(
                item_type=item,
                location=location,
                time_period=time if time != "unknown" else None
            )
            
        except Exception as e:
            logger.debug(f"Failed to persist pattern to database: {e}")
            # Don't fail the operation if DB save fails
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get statistics about learned patterns."""
        return {
            "total_observations": self.total_observations,
            "items_tracked": len(self.learned_location_counts),
            "locations_tracked": sum(len(v) for v in self.learned_location_counts.values()),
            "times_tracked": sum(len(v) for v in self.learned_time_counts.values()),
            "learning_weight": self.learned_weight,
            "static_weight": self.static_weight,
            "ready_for_inference": self.total_observations >= 5
        }


# ------------------------------------------------------------------ #
# Singleton Pattern for Global Access
# ------------------------------------------------------------------ #
_spatial_temporal_validator_instance = None


def get_spatial_temporal_validator() -> SpatialTemporalValidator:
    """
    Get or create the global SpatialTemporalValidator instance (singleton pattern).
    
    Returns:
        SpatialTemporalValidator: The global validator instance
    """
    global _spatial_temporal_validator_instance
    if _spatial_temporal_validator_instance is None:
        _spatial_temporal_validator_instance = SpatialTemporalValidator()
    return _spatial_temporal_validator_instance
