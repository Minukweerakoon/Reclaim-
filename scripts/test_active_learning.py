"""
Test script to verify Active Learning is working properly
"""

import requests
import json

API_URL = "http://localhost:8000"
API_KEY = "test-api-key"

def test_feedback_submission():
    """Test submitting user corrections"""
    print("=" * 50)
    print("Testing Active Learning: Feedback Submission")
    print("=" * 50)
    
    # Test Case 1: Color correction
    print("\n1. Testing color correction...")
    response = requests.post(
        f"{API_URL}/api/feedback/submit",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "input_text": "blue laptop",
            "original_prediction": {
                "item_type": "laptop",
                "color": "red"  # Wrong prediction
            },
            "user_correction": {
                "item_type": "laptop",
                "color": "blue"  # User corrects it
            },
            "feedback_type": "correction"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
        print(f"   Contribution count: {data['contribution_count']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test Case 2: Brand correction
    print("\n2. Testing brand correction...")
    response = requests.post(
        f"{API_URL}/api/feedback/submit",
        headers={
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "input_text": "Dell laptop",
            "original_prediction": {
                "item_type": "laptop",
                "brand": "HP"  # Wrong  
            },
            "user_correction": {
                "item_type": "laptop",
                "brand": "Dell"  # Correct
            }
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def test_feedback_stats():
    """Test retrieving feedback statistics"""
    print("\n" + "=" * 50)
    print("Testing Active Learning: Statistics")
    print("=" * 50 + "\n")
    
    response = requests.get(
        f"{API_URL}/api/feedback/stats",
        headers={"X-API-Key": API_KEY}
    )
    
    if response.status_code == 200:
        stats = response.json()
        print("📊 Active Learning Statistics:")
        print(f"   Total corrections: {stats.get('total_corrections', 0)}")
        print(f"   Buffer size: {stats.get('buffer_size', 0)}")
        print(f"   Max buffer: {stats.get('max_buffer_size', 1000)}")
        print(f"   Status: {stats.get('feature_status', 'unknown')}")
        
        if stats.get('feature_status') == 'active':
            print("\n✅ Active Learning is WORKING!")
        else:
            print(f"\n⚠️ Active Learning status: {stats.get('feature_status')}")
            if 'error' in stats:
                print(f"   Error: {stats['error']}")
    else:
        print(f"❌ Failed to get stats: {response.status_code}")

if __name__ == "__main__":
    print("\n🧪 Active Learning Test Suite\n")
    
    try:
        # Test feedback submission
        test_feedback_submission()
        
        # Test stats retrieval
        test_feedback_stats()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API at", API_URL)
        print("   Make sure the backend is running: python app.py")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
