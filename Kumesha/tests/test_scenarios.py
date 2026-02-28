"""
Comprehensive Test Scenarios for Multimodal Validation System.
Run: python test_scenarios.py

This script tests the system's robustness across various dimensions:
1. Intent Classification (Lost/Found/Inquiry)
2. Urgency Analysis (Critical/High/Normal)
3. Item Category Adaptive Thresholds
4. Description Quality (Complete vs Vague)
5. Edge Cases
"""
import sys
import logging
from typing import Dict, List, Any

# Configure logging to suppress verbose output during tests
logging.basicConfig(level=logging.ERROR)

# Add project root to path
sys.path.insert(0, '.')

from src.text.validator import TextValidator
from src.cross_modal.consistency_engine import ConsistencyEngine

# Setup output file
OUTPUT_FILE = "test_results.log"

def log_result(message: str):
    print(message)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")

def run_test_case(name: str, input_text: str, validator: TextValidator, expected: Dict[str, Any] = None):
    log_result(f"\n[TEST CASE]: {name}")
    log_result(f"   Input: \"{input_text}\"")
    
    try:
        # Run validation
        result = validator.analyze_text_enhanced(input_text)
        
        # Extract key metrics
        intent = result.get("intent", {}).get("intent", "unknown")
        urgency = result.get("urgency", {}).get("urgency", "normal")
        completeness = result.get("completeness", {}).get("score", 0.0)
        entities = result.get("entities", {})
        
        log_result(f"   -> Intent: {intent.upper()} | Urgency: {urgency.upper()} | Completeness: {completeness:.2f}")
        log_result(f"   -> Entities: {list(entities.keys())}")
        
        # Verify expectations if provided
        if expected:
            passed = True
            for key, val in expected.items():
                actual = locals().get(key)
                if actual != val:
                    log_result(f"   [FAIL] Mismatch on {key}: Expected {val}, got {actual}")
                    passed = False
            if passed:
                log_result(f"   [PASS] {name}")
        
    except Exception as e:
        log_result(f"   [ERROR] {e}")

def run_adaptive_test(name: str, category: str, validator: ConsistencyEngine):
    log_result(f"\n[ADAPTIVE THRESHOLD TEST]: {name}")
    log_result(f"   Category: {category}")
    
    thresholds = validator.get_adaptive_thresholds(category)
    log_result(f"   -> Image Quality Req: {thresholds['image_quality']:.0%}")
    log_result(f"   -> Text Completeness Req: {thresholds['text_completeness']:.0%}")
    log_result(f"   -> Description: {thresholds.get('description', 'N/A')}")

def main():
    # Clear previous log
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("TEST EXECUTION STARTED\n")

    log_result("="*60)
    log_result("MULTIMODAL VALIDATION SYSTEM - ROBUSTNESS CHECK")
    log_result("="*60)
    
    # Initialize validators
    log_result("Initializing validators...")
    tv = TextValidator(enable_logging=False)
    ce = ConsistencyEngine(enable_logging=False)
    
    # ---------------------------------------------------------
    # SCENARIO 1: INTENT VARIATIONS
    # ---------------------------------------------------------
    print("\n" + "-"*30)
    print("SCENARIO 1: INTENT VARIATIONS")
    print("-"*30)
    
    run_test_case(
        "Lost Item Report",
        "I lost my black leather wallet at the central station yesterday.",
        tv,
        {"intent": "lost"}
    )
    
    run_test_case(
        "Found Item Report",
        "I found a silver iPhone 14 Pro on a bench in the park.",
        tv,
        {"intent": "found"}
    )
    
    run_test_case(
        "Inquiry/Question",
        "Has anyone turned in a red scarf? I think I left it in the library.",
        tv,
        {"intent": "inquiry"}
    )

    # ---------------------------------------------------------
    # SCENARIO 2: URGENCY LEVELS
    # ---------------------------------------------------------
    print("\n" + "-"*30)
    print("SCENARIO 2: URGENCY LEVELS")
    print("-"*30)
    
    run_test_case(
        "Critical Urgency (Medical/Travel)",
        "URGENT! I lost my bag with my insulin and passport! My flight is in 3 hours!",
        tv,
        {"urgency": "critical"}
    )
    
    run_test_case(
        "High Urgency (Valuable)",
        "Please help, I lost my wedding ring. It is very expensive and sentimental.",
        tv,
        {"urgency": "high"}
    )
    
    run_test_case(
        "Low Urgency",
        "I think I left my old umbrella somewhere. No rush, just checking.",
        tv,
        {"urgency": "low"}
    )

    # ---------------------------------------------------------
    # SCENARIO 3: DESCRIPTION QUALITY
    # ---------------------------------------------------------
    print("\n" + "-"*30)
    print("SCENARIO 3: DESCRIPTION QUALITY")
    print("-"*30)
    
    run_test_case(
        "High Quality Description",
        "I lost a blue Dell XPS 13 laptop. It has a sticker of a cat on the lid and a small scratch near the charging port. Last seen in Room 304.",
        tv
    )
    
    run_test_case(
        "Vague/Poor Description",
        "I lost my stuff.",
        tv
    )

    # ---------------------------------------------------------
    # SCENARIO 4: ADAPTIVE THRESHOLDS (Consistency Engine)
    # ---------------------------------------------------------
    print("\n" + "-"*30)
    print("SCENARIO 4: ADAPTIVE THRESHOLDS")
    print("-"*30)
    
    run_adaptive_test("High Value Electronics", "iphone", ce)
    run_adaptive_test("Clothing Item", "jacket", ce)
    run_adaptive_test("Document/ID", "passport", ce)
    run_adaptive_test("Generic Item", "box", ce)

    # ---------------------------------------------------------
    # SCENARIO 5: EDGE CASES
    # ---------------------------------------------------------
    print("\n" + "-"*30)
    print("SCENARIO 5: EDGE CASES")
    print("-"*30)
    
    run_test_case(
        "Mixed Intent (Confusing)",
        "I found a phone but I also lost my keys. Can you help?",
        tv
    )
    
    run_test_case(
        "Gibberish/Nonsense",
        "asdf jkl; qwerty uiop 12345",
        tv
    )
    
    run_test_case(
        "Multi-lingual Input (Simulated)",
        "I lost my wallet. C'est noir. Es muy importante.",
        tv
    )

if __name__ == "__main__":
    main()
