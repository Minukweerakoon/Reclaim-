import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_simple():
    print("Testing Theft Prevention System Backend...")
    
    try:
        # Test health endpoint
        print("\n1. Testing health endpoint...")
        response = requests.get(f'{BASE_URL}/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test registration
        print("\n2. Testing user registration...")
        reg_data = {
            'username': 'teststudent',
            'email': 'student@example.com',
            'password': 'password123',
            'role': 'student'
        }
        response = requests.post(f'{BASE_URL}/register', json=reg_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test login
        print("\n3. Testing user login...")
        login_data = {
            'email': 'student@example.com',
            'password': 'password123'
        }
        response = requests.post(f'{BASE_URL}/login', json=login_data)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            login_response = response.json()
            token = login_response['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            print("Login successful!")
            
            # Test device registration
            print("\n4. Testing device registration...")
            device_data = {
                'name': 'My Laptop',
                'mac_address': '00:1B:44:11:3A:B7',
                'type': 'laptop'
            }
            response = requests.post(f'{BASE_URL}/devices', json=device_data, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json()}")
            
            # Test getting devices
            print("\n5. Testing get devices...")
            response = requests.get(f'{BASE_URL}/devices', headers=headers)
            print(f"Status: {response.status_code}")
            devices = response.json()
            print(f"Found {len(devices)} devices")
            
        else:
            print(f"Login failed: {response.json()}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to backend. Make sure the server is running!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_simple()