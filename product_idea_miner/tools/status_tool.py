import threading
from datetime import datetime
from typing import Dict, List, Any

class ScraperStatusTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self.status = "idle"  # idle | active
        self.current_step = "Inactive"
        self.progress = 0  # 0 to 100
        self.logs: List[Dict[str, Any]] = []
        self.stats: Dict[str, int] = {"scraped": 0, "saved": 0}
        self.error: str | None = None

    def start_run(self):
        with self._lock:
            self.status = "active"
            self.current_step = "Initializing pipeline..."
            self.progress = 5
            self.logs = []
            self.stats = {"scraped": 0, "saved": 0}
            self.error = None
            self._log("Pipeline triggered.")

    def update_step(self, step_name: str, progress: int):
        with self._lock:
            self.current_step = step_name
            self.progress = progress
            self._log(step_name)

    def add_log_msg(self, message: str):
        with self._lock:
            self._log(message)

    def set_stats(self, scraped: int = None, saved: int = None):
        with self._lock:
            if scraped is not None:
                self.stats["scraped"] = scraped
            if saved is not None:
                self.stats["saved"] = saved

    def complete_run(self, saved_count: int, error_msg: str | None = None):
        with self._lock:
            self.status = "idle"
            self.progress = 100
            if error_msg:
                self.error = error_msg
                self.current_step = "Failed"
                self._log(f"Pipeline failed: {error_msg}")
            else:
                self.current_step = "Completed"
                self.stats["saved"] = saved_count
                self._log(f"Pipeline completed. Saved {saved_count} ideas.")

    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "status": self.status,
                "current_step": self.current_step,
                "progress": self.progress,
                "logs": self.logs[-100:],  # limit to last 100 log messages
                "stats": self.stats,
                "error": self.error,
            }

    def _log(self, message: str):
        timestamp = datetime.now().isoformat()
        self.logs.append({"timestamp": timestamp, "message": message})


# Global singleton instance
tracker = ScraperStatusTracker()
