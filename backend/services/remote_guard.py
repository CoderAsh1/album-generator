import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, db

from config import DATA_DIR, IS_APP_ENABLED, KILL_SWITCH_MESSAGE

logger = logging.getLogger("album_maker.guard")

# Initialize Firebase
FIREBASE_CREDENTIALS_PATH = Path(__file__).parent.parent / "firebase-adminsdk.json"
FIREBASE_DB_URL = "https://albumgeneration-4bdad-default-rtdb.asia-southeast1.firebasedatabase.app/"

try:
    if not firebase_admin._apps:
        # Check for environment variable first (for production/Render/Railway)
        env_cert = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        if env_cert:
            import json
            cred_dict = json.loads(env_cert)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback to local file (for local development)
            cred = credentials.Certificate(str(FIREBASE_CREDENTIALS_PATH))
            
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_DB_URL
        })
    firebase_initialized = True
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    firebase_initialized = False

class RemoteGuard:
    async def is_app_enabled(self) -> Tuple[bool, str]:
        """
        Checks if the application is enabled via Firebase remote config.
        Returns (is_enabled: bool, message: str).
        Fallback to local config if Firebase fails.
        """
        if firebase_initialized:
            try:
                ref = db.reference('config')
                config_data = ref.get()
                
                if config_data:
                    is_enabled = config_data.get('is_enabled', True)
                    message = config_data.get('message', 'Active')
                    return is_enabled, message
            except Exception as e:
                logger.error(f"Firebase fetch config failed: {e}")
                
        # Fallback to local config.py
        if not IS_APP_ENABLED:
            return False, KILL_SWITCH_MESSAGE
            
        return True, "Active"

    def record_usage(self, action: str, photos_count: int = 0, sheets_count: int = 0, prompt: Optional[str] = None):
        """
        Firebase Usage Counter:
        Stores and tracks all processing/upload operations in Firebase RTDB under /metrics.
        """
        if not firebase_initialized:
            logger.warning("Firebase not initialized. Metrics won't be recorded.")
            return
            
        try:
            ref = db.reference('metrics')
            
            # Using transaction or direct update for counts
            def update_counts(current_value):
                if current_value is None:
                    current_value = {
                        "total_uploads": 0,
                        "total_generations": 0,
                        "total_photos_processed": 0,
                        "total_sheets_compiled": 0
                    }
                
                if action == "upload":
                    current_value["total_uploads"] = current_value.get("total_uploads", 0) + 1
                elif action == "generate":
                    current_value["total_generations"] = current_value.get("total_generations", 0) + 1
                    current_value["total_photos_processed"] = current_value.get("total_photos_processed", 0) + photos_count
                    current_value["total_sheets_compiled"] = current_value.get("total_sheets_compiled", 0) + sheets_count
                    
                return current_value
                
            # Update the counts using transaction to prevent race conditions
            ref.transaction(update_counts)
            
            # Append to recent activity ledger (keeps last 100 entries)
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": action,
                "photos_count": photos_count,
                "sheets_count": sheets_count,
                "prompt": prompt[:100] if prompt else None
            }
            
            activities_ref = db.reference('metrics/recent_activity')
            # Fetch existing to limit to 100
            current_activities = activities_ref.get() or []
            if not isinstance(current_activities, list):
                # Handle edge case where it might be a dict due to deletion/holes in list in RTDB
                current_activities = [v for k,v in current_activities.items() if v]
                
            current_activities.insert(0, entry)
            # Limit to 100
            current_activities = current_activities[:100]
            activities_ref.set(current_activities)

        except Exception as e:
            logger.error(f"Failed to record usage metrics to Firebase: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Returns the current usage analytics from Firebase."""
        if not firebase_initialized:
             return {
                "total_uploads": 0,
                "total_generations": 0,
                "total_photos_processed": 0,
                "total_sheets_compiled": 0,
                "recent_activity": [],
                "error": "Firebase not initialized"
            }
            
        try:
            ref = db.reference('metrics')
            metrics = ref.get()
            if metrics:
                # Format to match expected output
                recent = metrics.get('recent_activity', [])
                if not isinstance(recent, list):
                     recent = [v for k,v in recent.items() if v]
                metrics['recent_activity'] = recent
                return metrics
        except Exception as e:
            logger.error(f"Failed to fetch metrics from Firebase: {e}")
            
        return {
            "total_uploads": 0,
            "total_generations": 0,
            "total_photos_processed": 0,
            "total_sheets_compiled": 0,
            "recent_activity": []
        }

remote_guard = RemoteGuard()
