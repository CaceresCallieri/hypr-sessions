"""
Configuration management for hypr-sessions
Centralizes all constants and provides environment variable support
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Optional

from session_types import TimeoutSeconds


@dataclass
class SessionConfig:
    """Central configuration for hypr-sessions"""

    # Session Management
    sessions_dir: Path = Path.home() / ".config" / "hypr-sessions"

    # Timing Configuration
    delay_between_instructions: TimeoutSeconds = 0.4  # Seconds between window operations

    # Browser Integration
    browser_keyboard_shortcut: str = "Alt+U"
    browser_tab_file_timeout: TimeoutSeconds = 10  # Seconds to wait for tab capture file
    browser_tab_file_poll_interval: TimeoutSeconds = 0.25  # Seconds between file checks
    downloads_dir: Path = Path.home() / "Downloads"

    # Supported Applications
    supported_browsers: Optional[Set[str]] = None
    supported_terminals: Optional[Set[str]] = None
    application_commands: Optional[Dict[str, str]] = None

    # Neovide Integration
    neovide_socket_timeout: TimeoutSeconds = 5  # Seconds for socket operations
    neovide_session_timeout: TimeoutSeconds = 10  # Seconds for session capture
    neovide_file_wait_timeout: TimeoutSeconds = 3  # Seconds to wait for session file creation

    # Debug Configuration
    debug_enabled: bool = False

    def __post_init__(self) -> None:
        """Initialize default values that can't be set as dataclass defaults"""
        if self.supported_browsers is None:
            self.supported_browsers = {
                "zen-alpha",  # Zen Browser (alpha)
                "zen",  # Zen Browser (stable)
                "firefox",  # Firefox (future support)
            }

        if self.supported_terminals is None:
            self.supported_terminals = {
                "com.mitchellh.ghostty",
                # Add more terminals as supported
            }

        if self.application_commands is None:
            self.application_commands = {
                "com.mitchellh.ghostty": "ghostty",
                "zen-alpha": "zen-browser",
                "zen": "zen-browser",
                "firefox": "firefox",
                "neovide": "neovide",
            }

        # Ensure sessions directory exists
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_env(cls) -> "SessionConfig":
        """Create configuration from environment variables"""
        # Create instance with defaults first
        defaults = cls()

        return cls(
            # Session paths
            sessions_dir=Path(
                os.getenv("HYPR_SESSIONS_DIR", str(defaults.sessions_dir))
            ),
            downloads_dir=Path(
                os.getenv("HYPR_DOWNLOADS_DIR", str(defaults.downloads_dir))
            ),
            # Timing configuration
            delay_between_instructions=float(
                os.getenv("HYPR_DELAY", str(defaults.delay_between_instructions))
            ),
            browser_tab_file_timeout=int(
                os.getenv(
                    "HYPR_BROWSER_TIMEOUT", str(defaults.browser_tab_file_timeout)
                )
            ),
            # Browser configuration
            browser_keyboard_shortcut=os.getenv(
                "HYPR_BROWSER_SHORTCUT", defaults.browser_keyboard_shortcut
            ),
            # Debug configuration
            debug_enabled=os.getenv("HYPR_DEBUG", "false").lower()
            in ("true", "1", "yes"),
        )

    def get_session_file_path(self, session_name: str) -> Path:
        """Get the full path for a session file"""
        return self.sessions_dir / f"{session_name}.json"

    def get_neovide_session_file_path(self, pid: int) -> Path:
        """Get the path for a Neovide session file"""
        return self.sessions_dir / f"neovide-session-{pid}.vim"


# Global configuration instance
# This can be imported and used throughout the application
_config: Optional[SessionConfig] = None


def get_config() -> SessionConfig:
    """Get the global configuration instance"""
    global _config
    if _config is None:
        _config = SessionConfig.from_env()
    return _config


def set_config(config: SessionConfig) -> None:
    """Set the global configuration instance (for testing/customization)"""
    global _config
    _config = config

