import subprocess
import time
import os

def start_mongodb():
    """Start MongoDB process"""
    mongod_path = r"C:\Program Files\MongoDB\Server\8.2\bin\mongod.exe"
    db_path = r"C:\data\db"
    
    # Create directory if it doesn't exist
    os.makedirs(db_path, exist_ok=True)
    
    try:
        # Start MongoDB
        process = subprocess.Popen([mongod_path, f"--dbpath={db_path}"])
        print("MongoDB started successfully")
        time.sleep(3)  # Wait for MongoDB to start
        return process
    except Exception as e:
        print(f"Error starting MongoDB: {e}")
        return None

if __name__ == "__main__":
    start_mongodb()