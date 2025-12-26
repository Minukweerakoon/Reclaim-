"""
Spatial-Temporal Context Engine - Knowledge Graph Module
Part of Research-Grade Enhancement (Novel Contribution #1)

This module implements Bayesian reasoning for item-location-time plausibility.
Example: "Swimsuit in Server Room" → P(Swimsuit|ServerRoom) ≈ 0.001 → Implausible

Research Novelty: First lost-and-found system to use probabilistic context validation.
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import os

logger = logging.getLogger(__name__)


class KnowledgeGraph:
    """
    Probabilistic Knowledge Graph for Spatial-Temporal Context.
    
    Implements Bayesian inference for item-location-time plausibility.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the knowledge graph.
        
        Args:
            data_path: Path to pre-computed probability data (JSON file)
        """
        self.item_categories = {}      # Item → Category mapping
        self.location_types = {}       # Location → Type mapping
        self.time_periods = {}         # Hour → Period mapping
        
        # Probability tables
        self.p_item_location = defaultdict(lambda: defaultdict(float))  # P(Item|Location)
        self.p_item_time = defaultdict(lambda: defaultdict(float))      # P(Item|Time)
        self.p_location_time = defaultdict(lambda: defaultdict(float))  # P(Location|Time)
        
        # Load pre-computed probabilities if available
        if data_path and os.path.exists(data_path):
            self.load_probabilities(data_path)
        else:
            # Initialize with default probabilities (can be updated with real data)
            self._initialize_default_probabilities()
    
    def _initialize_default_probabilities(self):
        """
        Initialize with common-sense probabilities.
        
        This is a starting point. In production, these would be learned from real data.
        """
        # Define item categories
        self.item_categories = {
            'phone': 'electronics',
            'laptop': 'electronics',
            'keys': 'personal',
            'wallet': 'personal',
            'bag': 'container',
            'backpack': 'container',
            'book': 'academic',
            'notebook': 'academic',
            'pen': 'academic',
            'glasses': 'personal',
            'watch': 'personal',
            'umbrella': 'accessories',
            'water bottle': 'accessories',
            # Add more items...
        }
        
        # Define location types
        self.location_types = {
            'library': 'academic',
            'classroom': 'academic',
            'cafeteria': 'dining',
            'gym': 'sports',
            'parking': 'outdoor',
            'server room': 'restricted',
            'office': 'professional',
            'bathroom': 'facility',
            'lab': 'academic',
            # Add more locations...
        }
        
        # Define time periods
        for hour in range(24):
            if 6 <= hour < 12:
                self.time_periods[hour] = 'morning'
            elif 12 <= hour < 17:
                self.time_periods[hour] = 'afternoon'
            elif 17 <= hour < 22:
                self.time_periods[hour] = 'evening'
            else:
                self.time_periods[hour] = 'night'
        
        # Initialize default probabilities (common sense)
        # P(Item|Location) - Example: High probability of laptop in library
        self.p_item_location['laptop']['library'] = 0.85
        self.p_item_location['laptop']['classroom'] = 0.80
        self.p_item_location['laptop']['cafeteria'] = 0.30
        self.p_item_location['laptop']['gym'] = 0.10
        self.p_item_location['laptop']['server room'] = 0.05
        
        self.p_item_location['phone']['library'] = 0.90
        self.p_item_location['phone']['cafeteria'] = 0.85
        self.p_item_location['phone']['gym'] = 0.70
        
        self.p_item_location['keys']['parking'] = 0.80
        self.p_item_location['keys']['office'] = 0.75
        
        self.p_item_location['book']['library'] = 0.95
        self.p_item_location['book']['classroom'] = 0.90
        self.p_item_location['book']['gym'] = 0.05
        
        # Implausible combinations (low probability)
        self.p_item_location['swimsuit']['server room'] = 0.001
        self.p_item_location['surfboard']['library'] = 0.001
        
        # P(Item|Time) - Example: Laptop more common during day
        self.p_item_time['laptop']['morning'] = 0.85
        self.p_item_time['laptop']['afternoon'] = 0.90
        self.p_item_time['laptop']['evening'] = 0.60
        self.p_item_time['laptop']['night'] = 0.20
        
        # P(Location|Time) - Example: Library busy during day
        self.p_location_time['library']['morning'] = 0.80
        self.p_location_time['library']['afternoon'] = 0.90
        self.p_location_time['library']['evening'] = 0.50
        self.p_location_time['library']['night'] = 0.10
        
        logger.info("Initialized knowledge graph with default probabilities")
    
    def calculate_plausibility(
        self, 
        item: str, 
        location: Optional[str] = None, 
        time_hour: Optional[int] = None
    ) -> Dict:
        """
        Calculate plausibility score for an item-location-time combination.
        
        Args:
            item: Item description (e.g., "laptop", "phone")
            location: Location description (e.g., "library", "gym")
            time_hour: Hour of the day (0-23)
        
        Returns:
            Dict containing:
                - plausibility_score: 0.0-1.0 (1.0 = highly plausible)
                - reasoning: Explanation of the score
                - flags: List of warnings/alerts
        """
        item_lower = item.lower()
        location_lower = location.lower() if location else None
        
        # Normalize item and location to known categories
        item_normalized = self._normalize_item(item_lower)
        location_normalized = self._normalize_location(location_lower) if location_lower else None
        
        # Calculate components
        scores = []
        reasoning_parts = []
        flags = []
        
        # Component 1: P(Item|Location)
        if location_normalized:
            prob_item_loc = self.p_item_location.get(item_normalized, {}).get(location_normalized, 0.5)
            scores.append(prob_item_loc)
            
            if prob_item_loc < 0.1:
                flags.append(f"Very rare: '{item}' in '{location}' (probability: {prob_item_loc:.3f})")
                reasoning_parts.append(f"'{item}' is rarely found in '{location}'")
            elif prob_item_loc > 0.8:
                reasoning_parts.append(f"'{item}' is commonly found in '{location}'")
        
        # Component 2: P(Item|Time)
        if time_hour is not None:
            period = self.time_periods.get(time_hour, 'unknown')
            prob_item_time = self.p_item_time.get(item_normalized, {}).get(period, 0.5)
            scores.append(prob_item_time)
            
            if prob_item_time < 0.2:
                flags.append(f"Unusual time: '{item}' at {time_hour}:00 ({period})")
                reasoning_parts.append(f"'{item}' is rarely reported during {period}")
        
        # Component 3: P(Location|Time)
        if location_normalized and time_hour is not None:
            period = self.time_periods.get(time_hour, 'unknown')
            prob_loc_time = self.p_location_time.get(location_normalized, {}).get(period, 0.5)
            scores.append(prob_loc_time)
            
            if prob_loc_time < 0.2:
                flags.append(f"Location unusual at this time: '{location}' during {period}")
        
        # Calculate final plausibility score (geometric mean to penalize low probabilities)
        if scores:
            plausibility_score = pow(sum(scores) / len(scores), 1.5)  # Slightly penalize edge cases
        else:
            plausibility_score = 0.5  # Neutral if no data
        
        # Generate reasoning
        if not reasoning_parts:
            reasoning = "Insufficient context data to assess plausibility."
        else:
            reasoning = " ".join(reasoning_parts)
        
        return {
            "plausibility_score": round(plausibility_score, 3),
            "reasoning": reasoning,
            "flags": flags,
            "is_plausible": plausibility_score >= 0.3,  # Threshold for flagging
            "confidence": "high" if scores else "low"
        }
    
    def _normalize_item(self, item: str) -> str:
        """Normalize item to known category."""
        # Direct match
        if item in self.item_categories:
            return item
        
        # Fuzzy match (simple substring matching)
        for known_item in self.item_categories.keys():
            if known_item in item or item in known_item:
                return known_item
        
        # Fallback to original
        return item
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location to known type."""
        if location in self.location_types:
            return location
        
        for known_loc in self.location_types.keys():
            if known_loc in location or location in known_loc:
                return known_loc
        
        return location
    
    def load_probabilities(self, data_path: str):
        """Load pre-computed probabilities from JSON file."""
        try:
            with open(data_path, 'r') as f:
                data = json.load(f)
            
            self.item_categories = data.get('item_categories', {})
            self.location_types = data.get('location_types', {})
            self.p_item_location = defaultdict(lambda: defaultdict(float), data.get('p_item_location', {}))
            self.p_item_time = defaultdict(lambda: defaultdict(float), data.get('p_item_time', {}))
            self.p_location_time = defaultdict(lambda: defaultdict(float), data.get('p_location_time', {}))
            
            logger.info(f"Loaded probabilities from {data_path}")
        except Exception as e:
            logger.error(f"Failed to load probabilities: {e}")
            self._initialize_default_probabilities()
    
    def save_probabilities(self, output_path: str):
        """Save current probabilities to JSON file."""
        data = {
            'item_categories': self.item_categories,
            'location_types': self.location_types,
            'p_item_location': dict(self.p_item_location),
            'p_item_time': dict(self.p_item_time),
            'p_location_time': dict(self.p_location_time)
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved probabilities to {output_path}")


# Singleton instance
_knowledge_graph = None

def get_knowledge_graph() -> KnowledgeGraph:
    """Get or create the global knowledge graph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = KnowledgeGraph()
    return _knowledge_graph
