import os
import sys

# Ensure project root is on sys.path so we can import the FastAPI app
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, os.pardir, os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Re-export the FastAPI app defined at the project root
from app import app  # noqa: F401

