import json
import os
from datetime import datetime
from ..models.responses import AnalysisResponse

HISTORY_FILE = "analytics_history.json"

class HistoryService:
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(__file__), "..", "..", HISTORY_FILE)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_scan(self, response: AnalysisResponse):
        """Save a scan result for analytics."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

        scan_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_issues": response.summary.total,
            "security": response.summary.by_category.security,
            "quality": response.summary.by_category.quality,
            "performance": response.summary.by_category.performance,
            "style": response.summary.by_category.style,
            "structure": response.summary.by_category.structure,
            "mode": response.mode
        }

        history.append(scan_record)

        # Keep only the last 100 scans to prevent unbounded growth
        history = history[-100:]

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def get_history(self):
        """Retrieve the scan history."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

history_service = HistoryService()
