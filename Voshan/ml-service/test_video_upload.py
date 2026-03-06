"""
Test script to debug video upload issues
Run with: python test_video_upload.py
"""

import requests
import os
import sys

# Test video upload endpoint
ML_SERVICE_URL = "http://localhost:5001/api/v1/detect/process-video"

def test_video_upload(video_path):
    """Test uploading a video file"""
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    print(f"📹 Testing video upload: {video_path}")
    print(f"   File size: {os.path.getsize(video_path)} bytes")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'video_file': (os.path.basename(video_path), f, 'video/mp4')}
            data = {
                'save_output': 'true'
            }
            
            print(f"📤 Uploading to: {ML_SERVICE_URL}")
            response = requests.post(
                ML_SERVICE_URL,
                files=files,
                data=data,
                timeout=300
            )
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"   Status: {result.get('status')}")
                print(f"   Total frames: {result.get('total_frames')}")
                print(f"   Total alerts: {result.get('total_alerts')}")
            else:
                print(f"❌ Error response:")
                print(f"   Status: {response.status_code}")
                
                # Try to parse as JSON
                try:
                    error_data = response.json()
                    print(f"   Error data: {error_data}")
                except:
                    # If not JSON, show text
                    print(f"   Response text (first 500 chars): {response.text[:500]}")
                    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to ML service at {ML_SERVICE_URL}")
        print(f"   Make sure the ML service is running on port 5001")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    # Check if video path provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Look for test video in uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
        videos = [f for f in os.listdir(uploads_dir) if f.endswith(('.mp4', '.avi', '.mov'))] if os.path.exists(uploads_dir) else []
        
        if videos:
            video_path = os.path.join(uploads_dir, videos[0])
            print(f"📹 Using video from uploads: {video_path}")
        else:
            print("❌ No video file provided and no videos found in uploads directory")
            print("Usage: python test_video_upload.py <video_path>")
            sys.exit(1)
    
    test_video_upload(video_path)

