"""
Reproduction script for plausibility check (Gucci iPhone).
"""
import sys
sys.path.insert(0, '.')
from src.text.validator import TextValidator

def test_plausibility():
    tv = TextValidator(enable_logging=False)
    
    # Case: "red Gucci iPhone"
    # Expected: Should trigger a clarification question about the brand/item combination.
    text = "I lost my red Gucci iPhone in the library"
    print(f"Input: '{text}'")
    
    result = tv.validate_text(text, 'en')
    
    print(f"Valid: {result['valid']}")
    print(f"Entities: {result['entities']}")
    print(f"Feedback: {result['feedback']}")
    
    # Check if we have clarification questions (currently we don't, so this will show what's missing)
    if 'clarification_questions' in result:
        print(f"Clarifications: {result['clarification_questions']}")
    else:
        print("Clarifications: None (Feature missing)")

if __name__ == "__main__":
    test_plausibility()
