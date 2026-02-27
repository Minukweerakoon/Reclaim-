"""
Firebase Auth — Firebase Authentication helpers.

Initializes the Firebase Admin SDK and provides token verification
for user authentication. Data storage is handled by Supabase.
"""

import logging
import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

logger = logging.getLogger("FirebaseAuth")

# ------------------------------------------------------------------ #
# Singleton Firebase App Initialization
# ------------------------------------------------------------------ #
_firebase_app = None


def get_firebase_app():
    """Initialize Firebase Admin SDK (once)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    cred_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH", "./firebase-service-account.json"
    )
    if not os.path.exists(cred_path):
        logger.warning("Firebase service account file not found at %s", cred_path)
        return None

    try:
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("✓ Firebase Admin SDK initialized (project: %s)", cred.project_id)
        return _firebase_app
    except Exception as exc:
        logger.error("Failed to initialize Firebase: %s", exc)
        return None


def verify_firebase_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verify a Firebase ID token and return the decoded claims."""
    app = get_firebase_app()
    if app is None:
        return None
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as exc:
        logger.warning("Firebase token verification failed: %s", exc)
        return None
