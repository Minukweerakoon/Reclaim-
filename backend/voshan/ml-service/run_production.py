"""
Production Server Runner for ML Service
Uses Gunicorn for better handling of long-running requests and large responses
"""

import os
import sys
import subprocess

if __name__ == '__main__':
    # Get configuration
    host = os.getenv('ML_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('ML_SERVICE_PORT', '5001'))
    workers = int(os.getenv('ML_SERVICE_WORKERS', '2'))
    timeout = int(os.getenv('ML_SERVICE_TIMEOUT', '1200'))  # 20 minutes
    
    print(f"Starting ML Service with Gunicorn on {host}:{port}")
    print(f"Workers: {workers}, Timeout: {timeout}s")
    
    # Build gunicorn command
    cmd = [
        'gunicorn',
        '--bind', f'{host}:{port}',
        '--workers', str(workers),
        '--timeout', str(timeout),
        '--keep-alive', '65',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--access-logfile', '-',
        '--error-logfile', '-',
        '--log-level', 'info',
        'app:app'
    ]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Gunicorn: {e}")
        print("\nFalling back to Flask development server...")
        print("Note: For production, install gunicorn: pip install gunicorn")
        sys.exit(1)
    except FileNotFoundError:
        print("Gunicorn not found. Install with: pip install gunicorn")
        print("\nFalling back to Flask development server...")
        # Fallback to Flask dev server
        from app import app
        import yaml
        
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        app.run(
            host=config['api']['host'],
            port=config['api']['port'],
            debug=config['api']['debug']
        )

