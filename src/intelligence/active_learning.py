"""
Active Learning Module (Novel Feature #2)
Implements human-in-the-loop feedback system for continuous improvement

Research Novelty: First lost-and-found system with self-improving validation via user corrections.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque

logger = logging.getLogger(__name__)


class ActiveLearningSystem:
    """
    Manages user feedback and model adaptation.
    
    Key Features:
    - Episodic memory buffer (stores recent corrections)
    - Confidence-based sampling (only ask when uncertain)
    - Feedback analytics (track improvement over time)
    """
    
    def __init__(self, buffer_size=1000, confidence_threshold=0.7):
        """
        Initialize Active Learning System.
        
        Args:
            buffer_size: Maximum number of feedback entries to store
            confidence_threshold: Only request feedback below this confidence
        """
        self.buffer_size = buffer_size
        self.confidence_threshold = confidence_threshold
        
        # Episodic memory (circular buffer)
        self.feedback_buffer = deque(maxlen=buffer_size)
        
        # Feedback storage path
        self.feedback_file = Path("data/active_learning_feedback.json")
        self.feedback_file.parent.mkdir(exist_ok=True)
        
        # Load existing feedback
        self._load_feedback()
        
        # Statistics
        self.total_corrections = 0
        self.accepted_corrections = 0
    
    def _load_feedback(self):
        """Load previously stored feedback."""
        if self.feedback_file.exists():
            try:
                with open(self.feedback_file, 'r') as f:
                    data = json.load(f)
                    self.feedback_buffer.extend(data)
                    self.total_corrections = len(data)
                logger.info(f"Loaded {len(data)} feedback entries")
            except Exception as e:
                logger.error(f"Failed to load feedback: {e}")
    
    def _save_feedback(self):
        """Persist feedback to disk."""
        try:
            with open(self.feedback_file, 'w') as f:
                json.dump(list(self.feedback_buffer), f, indent=2)
            logger.info(f"Saved {len(self.feedback_buffer)} feedback entries")
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
    
    def should_request_feedback(self, confidence: float) -> bool:
        """
        Decide whether to request user feedback based on confidence.
        
        Args:
            confidence: Model's confidence score (0-1)
        
        Returns:
            True if feedback should be requested
        """
        return confidence < self.confidence_threshold
    
    def record_feedback(
        self,
        input_text: str,
        original_prediction: Dict,
        user_correction: Dict,
        feedback_type: str = "correction"
    ):
        """
        Record user feedback for later learning.
        
        Args:
            input_text: Original user input
            original_prediction: System's original output
            user_correction: User's corrected version
            feedback_type: Type of feedback (correction, confirmation, clarification)
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "input": input_text,
            "original": original_prediction,
            "correction": user_correction,
            "type": feedback_type
        }
        
        self.feedback_buffer.append(feedback_entry)
        self.total_corrections += 1
        
        # Save to disk
        self._save_feedback()
        
        logger.info(f"Recorded feedback: {feedback_type}")
        
        return feedback_entry
    
    def get_recent_corrections(self, n=10) -> List[Dict]:
        """Get the N most recent corrections."""
        return list(self.feedback_buffer)[-n:]
    
    def analyze_feedback_trends(self) -> Dict:
        """
        Analyze patterns in user feedback.
        
        Returns:
            Dict with statistics about corrections
        """
        if not self.feedback_buffer:
            return {"message": "No feedback data available"}
        
        # Count feedback types
        type_counts = {}
        error_patterns = {}
        
        for entry in self.feedback_buffer:
            feedback_type = entry.get('type', 'unknown')
            type_counts[feedback_type] = type_counts.get(feedback_type, 0) + 1
            
            # Analyze what was corrected
            orig = entry.get('original', {})
            corr = entry.get('correction', {})
            
            if 'item' in corr and corr['item'] != orig.get('item'):
                error_patterns['item_misidentification'] = error_patterns.get('item_misidentification', 0) + 1
            
            if 'location' in corr and corr['location'] != orig.get('location'):
                error_patterns['location_error'] = error_patterns.get('location_error', 0) + 1
        
        return {
            "total_feedback": len(self.feedback_buffer),
            "feedback_types": type_counts,
            "common_errors": error_patterns,
            "buffer_usage": f"{len(self.feedback_buffer)}/{self.buffer_size}"
        }
    
    def generate_training_examples(self) -> List[Dict]:
        """
        Convert feedback into training examples for fine-tuning.
        
        Returns:
            List of (input, expected_output) pairs
        """
        training_examples = []
        
        for entry in self.feedback_buffer:
            if entry.get('type') == 'correction':
                example = {
                    "input": entry['input'],
                    "expected_output": entry['correction'],
                    "timestamp": entry['timestamp']
                }
                training_examples.append(example)
        
        return training_examples
    
    def apply_corrections_to_knowledge_graph(self, knowledge_graph):
        """
        Update knowledge graph probabilities based on user corrections.
        
        This is a simple approach - in production, you'd use more sophisticated methods.
        """
        corrections_applied = 0
        
        for entry in self.feedback_buffer:
            if entry.get('type') == 'correction':
                correction = entry.get('correction', {})
                item = correction.get('item')
                location = correction.get('location')
                
                if item and location:
                    # Boost probability for corrected item-location pair
                    current_prob = knowledge_graph.p_item_location[item][location]
                    boosted_prob = min(1.0, current_prob + 0.1)  # Increase by 10%
                    knowledge_graph.p_item_location[item][location] = boosted_prob
                    
                    corrections_applied += 1
        
        logger.info(f"Applied {corrections_applied} corrections to knowledge graph")
        return corrections_applied


# Singleton instance
_active_learning_system = None

def get_active_learning_system() -> ActiveLearningSystem:
    """Get or create the global Active Learning System instance."""
    global _active_learning_system
    if _active_learning_system is None:
        _active_learning_system = ActiveLearningSystem()
    return _active_learning_system
