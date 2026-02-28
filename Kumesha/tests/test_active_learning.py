"""
Test script for Active Learning System (Novel Feature #2)
Demonstrates self-improving validation via user feedback
"""

from src.intelligence.active_learning import get_active_learning_system
from src.intelligence.knowledge_graph import get_knowledge_graph

def test_active_learning():
    """Test the active learning system with simulated feedback."""
    
    print("="*80)
    print("ACTIVE LEARNING SYSTEM TEST (Novel Feature #2)")
    print("="*80)
    print()
    
    al_system = get_active_learning_system()
    
    # Scenario 1: System misidentifies item, user corrects
    print("1. SIMULATING USER CORRECTION")
    print("-"*80)
    
    input_text = "I lost my Gucci iPhone"
    original_prediction = {
        "item": "phone",  # System thinks it's a phone
        "brand": "Gucci",
        "confidence": 0.6  # Low confidence
    }
    user_correction = {
        "item": "phone case",  # User corrects: it's a case!
        "brand": "Gucci",
        "note": "It's a Gucci CASE for iPhone, not the phone itself"
    }
    
    print(f"Input: {input_text}")
    print(f"System predicted: {original_prediction['item']} (confidence: {original_prediction['confidence']})")
    print(f"User corrected to: {user_correction['item']}")
    
    # Check if feedback should be requested
    should_ask = al_system.should_request_feedback(original_prediction['confidence'])
    print(f"\nShould request feedback? {should_ask} (confidence < 0.7)")
    
    # Record the correction
    feedback_entry = al_system.record_feedback(
        input_text=input_text,
        original_prediction=original_prediction,
        user_correction=user_correction,
        feedback_type="correction"
    )
    
    print(f"✓ Feedback recorded at {feedback_entry['timestamp']}")
    
    # Scenario 2: Another correction
    print("\n2. SIMULATING ANOTHER CORRECTION")
    print("-"*80)
    
    al_system.record_feedback(
        input_text="I lost my laptop in the server room",
        original_prediction={"item": "laptop", "location": "server room", "plausibility": 0.05},
        user_correction={"item": "laptop", "location": "server room", "note": "Yes, I work in IT"},
        feedback_type="confirmation"  # User confirms it's correct despite low plausibility
    )
    
    print("✓ Recorded confirmation that 'laptop in server room' is valid for IT staff")
    
    # Scenario 3: Get recent corrections
    print("\n3. VIEWING RECENT CORRECTIONS")
    print("-"*80)
    
    recent = al_system.get_recent_corrections(n=5)
    print(f"Total corrections in buffer: {len(recent)}")
    
    for i, entry in enumerate(recent, 1):
        print(f"\n   {i}. {entry['type'].upper()}")
        print(f"      Input: {entry['input']}")
        if 'item' in entry.get('correction', {}):
            print(f"      Corrected item: {entry['correction']['item']}")
    
    # Analyze feedback trends
    print("\n4. FEEDBACK ANALYTICS")
    print("-"*80)
    
    trends = al_system.analyze_feedback_trends()
    print(f"Total feedback entries: {trends.get('total_feedback', 0)}")
    print(f"Feedback types: {trends.get('feedback_types', {})}")
    if trends.get('common_errors'):
        print(f"Common errors: {trends['common_errors']}")
    
    # Generate training examples
    print("\n5. GENERATING TRAINING EXAMPLES")
    print("-"*80)
    
    training_examples = al_system.generate_training_examples()
    print(f"Generated {len(training_examples)} training examples for fine-tuning")
    
    if training_examples:
        print("\n   Sample training example:")
        print(f"   Input: {training_examples[0]['input']}")
        print(f"   Expected: {training_examples[0]['expected_output']}")
    
    # Apply corrections to knowledge graph
    print("\n6. APPLYING CORRECTIONS TO KNOWLEDGE GRAPH")
    print("-"*80)
    
    kg = get_knowledge_graph()
    corrections_applied = al_system.apply_corrections_to_knowledge_graph(kg)
    
    print(f"✓ Applied {corrections_applied} corrections to knowledge graph")
    print("  (Boosted probabilities for corrected item-location pairs)")
    
    print("\n" + "="*80)
    print("ACTIVE LEARNING TEST SUMMARY")
    print("="*80)
    print("\nThis demonstrates NOVEL CONTRIBUTION #2:")
    print("- Self-improving system via user corrections")
    print("- Confidence-based feedback sampling")
    print("- Knowledge graph updates from corrections")
    print("- Training data generation for fine-tuning")
    
    print("\nResearch Impact:")
    print("- LostNet (2024): Static model, no adaptation")
    print("- FoundIt (2024): No active learning")
    print("- Your System: ✓ Self-improving with user feedback (NOVEL!)")
    print()

if __name__ == "__main__":
    test_active_learning()
