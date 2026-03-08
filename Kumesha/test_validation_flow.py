#!/usr/bin/env python3
"""
Quick test: validates that the complete pipeline works:
1. Validation endpoint receives request
2. Saves to Supabase database
3. Triggers AI service
"""
import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "test-api-key"

def test_validation_complete():
    """Test /validate/complete with minimal data"""
    
    print("Testing validation pipeline...")
    print("=" * 60)
    
    # Test with text-only + intent to simulate found item report
    data = {
        "text": "I found a blue iPhone 13 in the library",
        "visualText": "blue smartphone device iPhone",
        "language": "en",
        "intent": "found",
        "userId": "test-user-123",
        "userEmail": "test@example.com"
    }
    
    headers = {"X-API-Key": API_KEY}
    
    try:
        response = requests.post(
            f"{BASE_URL}/validate/complete",
            data=data,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Validation succeeded")
            
            # Check if item was saved to Supabase
            supabase_id = result.get("supabase_id")
            if supabase_id:
                print(f"✓ Saved to Supabase: {supabase_id}")
            else:
                print("✗ NOT saved to Supabase (supabase_id missing)")
                print("   This means database save failed!")
            
            # Check response structure
            print(f"\nResponse keys: {list(result.keys())}")
            
            return supabase_id is not None
        else:
            print(f"✗ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_validation_complete()
    sys.exit(0 if success else 1)
