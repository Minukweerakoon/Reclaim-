"""
Test script for Research-Grade Intelligence (LLM Integration).
"""
import sys
sys.path.insert(0, '.')
from src.text.validator import TextValidator

def test_llm_intelligence():
    tv = TextValidator(enable_logging=False)
    
    print("=== Test Case 1: Sentimental Value ===")
    text1 = "I lost my late grandmother's locket. It means the world to me."
    print(f"Input: '{text1}'")
    result1 = tv.validate_text(text1, 'en')
    print(f"Feedback: {result1['feedback']}")
    
    print("\n=== Test Case 2: High Value Ambiguity ===")
    text2 = "I lost a diamond ring in the bathroom."
    print(f"Input: '{text2}'")
    result2 = tv.validate_text(text2, 'en')
    print(f"Feedback: {result2['feedback']}")
    print(f"Clarification Questions: {result2.get('clarification_questions', [])}")
    
    print("\n=== Test Case 3: Standard Item ===")
    text3 = "I lost my blue backpack."
    print(f"Input: '{text3}'")
    result3 = tv.validate_text(text3, 'en')
    print(f"Feedback: {result3['feedback']}")

if __name__ == "__main__":
    test_llm_intelligence()
