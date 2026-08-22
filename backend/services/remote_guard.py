import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any, Optional

from config import DATA_DIR, IS_APP_ENABLED, KILL_SWITCH_MESSAGE

logger = logging.getLogger("album_maker.guard")

METRICS_FILE = DATA_DIR / "usage_metrics.json"

class RemoteGuard:
    async def is_app_enabled(self) -> Tuple[bool, str]:
        """
        Checks if the application is enabled via IS_APP_ENABLED in config.py.
        Returns (is_enabled: bool, message: str).
        """
        if not IS_APP_ENABLED:
            return False, KILL_SWITCH_MESSAGE
            
        return True, "Active"

    def record_usage(self, action: str, photos_count: int = 0, sheets_count: int = 0, prompt: Optional[str] = None):
        """
        Zero-DB Persistent Usage Counter:
        Stores and tracks all processing/upload operations in backend/data/usage_metrics.json.
        """
        try:
            metrics = {
                "total_uploads": 0,
                "total_generations": 0,
                "total_photos_processed": 0,
                "total_sheets_compiled": 0,
                "recent_activity": []
            }

            if METRICS_FILE.exists():
                try:
                    with open(METRICS_FILE, "r", encoding="utf-8") as f:
                        metrics = json.load(f)
                except Exception:
                    pass

            if action == "upload":
                metrics["total_uploads"] = metrics.get("total_uploads", 0) + 1
            elif action == "generate":
                metrics["total_generations"] = metrics.get("total_generations", 0) + 1
                metrics["total_photos_processed"] = metrics.get("total_photos_processed", 0) + photos_count
                metrics["total_sheets_compiled"] = metrics.get("total_sheets_compiled", 0) + sheets_count

            # Append to recent activity ledger (keeps last 100 entries)
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "action": action,
                "photos_count": photos_count,
                "sheets_count": sheets_count,
                "prompt": prompt[:100] if prompt else None
            }
            activities = metrics.get("recent_activity", [])
            activities.insert(0, entry)
            metrics["recent_activity"] = activities[:100]

            with open(METRICS_FILE, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to record usage metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Returns the current usage analytics."""
        if METRICS_FILE.exists():
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_uploads": 0,
            "total_generations": 0,
            "total_photos_processed": 0,
            "total_sheets_compiled": 0,
            "recent_activity": []
        }

remote_guard = RemoteGuard()
