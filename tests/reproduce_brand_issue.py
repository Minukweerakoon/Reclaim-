"""
Reproduction script for brand misclassification issue.
"""
import sys
sys.path.insert(0, '.')
from src.text.validator import TextValidator

def test_brand_extraction():
    tv = TextValidator(enable_logging=False)
    
    # Case 1: "red Gucci iPhone"
    # Expected: Brand should be Apple (implicit) or at least contain Apple. 
    # Current behavior: Likely just Gucci.
    text = "I lost my red Gucci iPhone in the library"
    print(f"Input: '{text}'")
    result = tv.extract_entities(text, 'en')
    print(f"Extracted Brands: {result['brand_mentions']}")
    
    # Case 2: "Samsung Galaxy S21"
    # Expected: Samsung
    text = "Found a Samsung Galaxy S21"
    print(f"\nInput: '{text}'")
    result = tv.extract_entities(text, 'en')
    print(f"Extracted Brands: {result['brand_mentions']}")

    # Case 3: "Nike Air Jordan"
    # Expected: Nike
    text = "Lost my Nike Air Jordans"
    print(f"\nInput: '{text}'")
    result = tv.extract_entities(text, 'en')
    print(f"Extracted Brands: {result['brand_mentions']}")

if __name__ == "__main__":
    test_brand_extraction()
