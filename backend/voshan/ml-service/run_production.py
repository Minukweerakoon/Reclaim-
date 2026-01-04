"""
Production Server Runner for ML Service
Uses Waitress on Windows (Gunicorn doesn't work on Windows)
Uses Gunicorn on Unix/Linux/Mac
"""

import os
import sys
import platform

if __name__ == '__main__':
    # Get configuration
    host = os.getenv('ML_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('ML_SERVICE_PORT', '5001'))
    timeout = int(os.getenv('ML_SERVICE_TIMEOUT', '1200'))  # 20 minutes
    
    from app import app
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Use Waitress on Windows, Gunicorn on Unix
    if platform.system() == 'Windows':
        # Windows: Use Waitress (production WSGI server for Windows)
        try:
            from waitress import serve
            print(f"Starting ML Service with Waitress on {host}:{port}")
            print(f"Timeout: {timeout}s")
            print("Waitress is a production WSGI server that works on Windows")
            serve(
                app,
                host=host,
                port=port,
                threads=4,  # Number of threads (Waitress is multi-threaded)
                channel_timeout=timeout,
                cleanup_interval=30,
                asyncore_use_poll=True
            )
        except ImportError:
            print("Waitress not found. Install with: pip install waitress")
            print("\nFalling back to Flask development server...")
            print("WARNING: Flask dev server may have connection reset issues with long videos")
            app.run(
                host=config['api']['host'],
                port=config['api']['port'],
                debug=config['api']['debug'],
                threaded=True
            )
    else:
        # Unix/Linux/Mac: Use Gunicorn
        import subprocess
        workers = int(os.getenv('ML_SERVICE_WORKERS', '2'))
        
        print(f"Starting ML Service with Gunicorn on {host}:{port}")
        print(f"Workers: {workers}, Timeout: {timeout}s")
        
        cmd = [
            sys.executable,
            '-m', 'gunicorn',
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
            import gunicorn
            print(f"Using Gunicorn version: {gunicorn.__version__}")
            subprocess.run(cmd, check=True)
        except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"Error starting Gunicorn: {e}")
            print("\nFalling back to Flask development server...")
            app.run(
                host=config['api']['host'],
                port=config['api']['port'],
                debug=config['api']['debug']
            )
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

