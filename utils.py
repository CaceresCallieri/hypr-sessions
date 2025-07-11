"""
Utility functions and shared configuration
"""

from pathlib import Path


class Utils:
    def __init__(self):
        self.sessions_dir = Path.home() / ".config" / "hypr-sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
