import os
from app import create_app

app = create_app()

def get_local_ip():
    """Get local IP address for mobile access"""
    import socket
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "localhost"

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("=" * 60)
    print("Theft Prevention System Starting...")
    print(f"Local Access: http://localhost:5000")
    print(f"Mobile Access: http://{local_ip}:5000")
    print(f"Frontend URL: http://{local_ip}:3000")
    print("API Health: http://localhost:5000/api/health")
    print("=" * 60)
    print("IMPORTANT FOR MOBILE TESTING:")
    print(f"1. Connect mobile to same WiFi")
    print(f"2. Open: http://{local_ip}:3000 on mobile browser")
    print("3. Use same credentials as laptop")
    print("=" * 60)
    
    # Allow connections from any IP on the network
    app.run(debug=True, host='0.0.0.0', port=5000)