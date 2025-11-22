import requests
import json

BASE_URL = 'http://localhost:5000/api'

def test_backend():
    try:
        # Test health endpoint
        response = requests.get(f'{BASE_URL}/health')
        print('Health check:', response.json())
        
        # Test registration
        reg_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'role': 'student'
        }
        response = requests.post(f'{BASE_URL}/register', json=reg_data)
        print('Registration:', response.json())
        
        # Test login
        login_data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        response = requests.post(f'{BASE_URL}/login', json=login_data)
        print('Login:', response.json())
        
        if response.status_code == 200:
            token = response.json()['access_token']
            headers = {'Authorization': f'Bearer {token}'}
            
            # Test device registration
            device_data = {
                'name': 'Test Laptop',
                'mac_address': '00:1B:44:11:3A:B7',
                'type': 'laptop'
            }
            response = requests.post(f'{BASE_URL}/devices', json=device_data, headers=headers)
            print('Device registration:', response.json())
            
    except Exception as e:
        print('Error:', e)

if __name__ == '__main__':
    test_backend()




   