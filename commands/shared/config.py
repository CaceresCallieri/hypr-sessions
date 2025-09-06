"""
Configuration management for hypr-sessions
Centralizes all constants and provides environment variable support
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Set, Optional

from .session_types import TimeoutSeconds


@dataclass
class SessionConfig:
    """Central configuration for hypr-sessions"""

    # Session Management
    sessions_dir: Path = Path.home() / ".config" / "hypr-sessions"
    
    # Archive Configuration
    archive_enabled: bool = True
    archive_max_sessions: int = 20
    archive_auto_cleanup: bool = True
    archive_cleanup_strategy: str = "oldest_first"  # or "largest_first"

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

    def _validate_env_numeric(self, env_var: str, current_value, min_val, max_val, value_type=int):
        """Validate and set numeric environment variable with bounds checking"""
        if env_var in os.environ:
            try:
                new_value = value_type(os.environ[env_var])
                if min_val <= new_value <= max_val:
                    return new_value
                else:
                    print(f"Warning: {env_var} value {new_value} out of range ({min_val}-{max_val}), using default {current_value}")
                    return current_value
            except ValueError:
                print(f"Warning: Invalid {env_var} value '{os.environ[env_var]}', using default {current_value}")
        return current_value

    def __post_init__(self) -> None:
        """Initialize default values and apply environment variable overrides"""
        # Apply environment variable overrides for archive settings with bounds validation
        self.archive_max_sessions = self._validate_env_numeric(
            "ARCHIVE_MAX_SESSIONS", self.archive_max_sessions, 1, 1000
        )
        
        if "ARCHIVE_AUTO_CLEANUP" in os.environ:
            self.archive_auto_cleanup = os.environ["ARCHIVE_AUTO_CLEANUP"].lower() in ("true", "1", "yes")
        
        if "ARCHIVE_ENABLED" in os.environ:
            self.archive_enabled = os.environ["ARCHIVE_ENABLED"].lower() in ("true", "1", "yes")
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
        
        # Perform automatic migration if needed
        self._ensure_folder_structure()

    @staticmethod
    def _safe_int_from_env(env_var: str, default_value: int, min_val: int, max_val: int) -> int:
        """Safely parse integer environment variable with bounds checking"""
        env_str = os.getenv(env_var)
        if env_str is None:
            return default_value
        try:
            value = int(env_str)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Warning: {env_var} value {value} out of range ({min_val}-{max_val}), using default {default_value}")
                return default_value
        except ValueError:
            print(f"Warning: Invalid {env_var} value '{env_str}', using default {default_value}")
            return default_value

    @staticmethod
    def _safe_float_from_env(env_var: str, default_value: float, min_val: float, max_val: float) -> float:
        """Safely parse float environment variable with bounds checking"""
        env_str = os.getenv(env_var)
        if env_str is None:
            return default_value
        try:
            value = float(env_str)
            if min_val <= value <= max_val:
                return value
            else:
                print(f"Warning: {env_var} value {value} out of range ({min_val:.1f}-{max_val:.1f}), using default {default_value}")
                return default_value
        except ValueError:
            print(f"Warning: Invalid {env_var} value '{env_str}', using default {default_value}")
            return default_value

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
            # Archive configuration
            archive_enabled=os.getenv("HYPR_ARCHIVE_ENABLED", "true").lower()
            in ("true", "1", "yes"),
            archive_max_sessions=cls._safe_int_from_env(
                "HYPR_ARCHIVE_MAX", defaults.archive_max_sessions, 1, 1000
            ),
            archive_auto_cleanup=os.getenv("HYPR_ARCHIVE_AUTO_CLEANUP", "true").lower()
            in ("true", "1", "yes"),
            archive_cleanup_strategy=os.getenv(
                "HYPR_ARCHIVE_CLEANUP_STRATEGY", defaults.archive_cleanup_strategy
            ),
            # Timing configuration
            delay_between_instructions=cls._safe_float_from_env(
                "HYPR_DELAY", defaults.delay_between_instructions, 0.0, 10.0
            ),
            browser_tab_file_timeout=cls._safe_int_from_env(
                "HYPR_BROWSER_TIMEOUT", defaults.browser_tab_file_timeout, 1, 120
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
        """Get the full path for a session file in the new folder structure"""
        session_dir = self.sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / "session.json"

    def get_session_directory(self, session_name: str) -> Path:
        """Get the session directory path"""
        session_dir = self.sessions_dir / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def get_neovide_session_file_path(self, session_name: str, pid: int) -> Path:
        """Get the path for a Neovide session file within a session directory"""
        session_dir = self.get_session_directory(session_name)
        return session_dir / f"neovide-session-{pid}.vim"

    def get_legacy_session_file_path(self, session_name: str) -> Path:
        """Get the legacy session file path (for migration purposes)"""
        return self.sessions_dir / f"{session_name}.json"

    def get_legacy_neovide_session_file_path(self, pid: int) -> Path:
        """Get the legacy Neovide session file path (for migration purposes)"""
        return self.sessions_dir / f"neovide-session-{pid}.vim"

    # Archive System Methods
    
    def get_active_sessions_dir(self) -> Path:
        """Get the active sessions directory path (new folder structure)"""
        active_dir = self.sessions_dir / "sessions"
        active_dir.mkdir(parents=True, exist_ok=True)
        return active_dir
    
    def get_archived_sessions_dir(self) -> Path:
        """Get the archived sessions directory path"""
        archived_dir = self.sessions_dir / "archived"
        archived_dir.mkdir(parents=True, exist_ok=True)
        return archived_dir
    
    def get_active_session_directory(self, session_name: str) -> Path:
        """Get an active session directory path (new structure)"""
        session_dir = self.get_active_sessions_dir() / session_name
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir
    
    def get_active_session_file_path(self, session_name: str) -> Path:
        """Get the active session file path (new structure)"""
        return self.get_active_session_directory(session_name) / "session.json"
    
    def get_archived_session_directory(self, archived_session_name: str) -> Path:
        """Get an archived session directory path"""
        return self.get_archived_sessions_dir() / archived_session_name
    
    def get_archived_session_file_path(self, archived_session_name: str) -> Path:
        """Get an archived session file path"""
        return self.get_archived_session_directory(archived_session_name) / "session.json"
    
    def get_archive_metadata_path(self, archived_session_name: str) -> Path:
        """Get the archive metadata file path"""
        return self.get_archived_session_directory(archived_session_name) / ".archive-metadata.json"
    
    def _ensure_folder_structure(self) -> None:
        """Ensure proper folder structure and migrate if needed"""
        # Check if we need to migrate from old flat structure to new nested structure
        if self._needs_migration():
            self._migrate_to_new_structure()
    
    def _needs_migration(self) -> bool:
        """Check if migration from flat structure to nested structure is needed"""
        active_dir = self.sessions_dir / "sessions"
        archived_dir = self.sessions_dir / "archived"
        
        # If both directories exist, assume migration is already done
        if active_dir.exists() and archived_dir.exists():
            return False
        
        # Check for session directories in the root sessions_dir (old structure)
        try:
            root_dirs = [d for d in self.sessions_dir.iterdir() 
                        if d.is_dir() and not d.name.startswith('.') 
                        and d.name not in ['sessions', 'archived', 'zen-browser-backups']]
            
            # If we have session directories in root, we need migration
            return len(root_dirs) > 0
        except (OSError, PermissionError):
            # If we can't read the directory, assume no migration needed
            return False
    
    def _migrate_to_new_structure(self) -> None:
        """Migrate from flat structure to nested active/archived structure"""
        import shutil
        
        print("🔄 Migrating session storage to new archive-enabled structure...")
        
        # Create the new directories
        active_dir = self.get_active_sessions_dir()
        archived_dir = self.get_archived_sessions_dir()
        
        # Find all session directories in root
        session_dirs = [d for d in self.sessions_dir.iterdir() 
                       if d.is_dir() and not d.name.startswith('.') 
                       and d.name not in ['sessions', 'archived', 'zen-browser-backups']]
        
        migrated_count = 0
        for session_dir in session_dirs:
            try:
                # Move to active sessions directory
                new_location = active_dir / session_dir.name
                shutil.move(str(session_dir), str(new_location))
                migrated_count += 1
                print(f"  ✓ Migrated session: {session_dir.name}")
            except (OSError, PermissionError) as e:
                print(f"  ✗ Failed to migrate session {session_dir.name}: {e}")
        
        print(f"✅ Migration complete: {migrated_count} sessions moved to new structure")
        print(f"   Active sessions: {active_dir}")
        print(f"   Archive location: {archived_dir}")
    
    def is_using_legacy_structure(self) -> bool:
        """Check if we're still using the legacy flat structure"""
        return not (self.sessions_dir / "sessions").exists()


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

