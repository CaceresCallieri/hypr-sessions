"""
Type definitions for hypr-sessions
Provides meaningful type aliases for complex or domain-specific concepts
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

# Time-related types (clarify units)
TimeoutSeconds = int | float  # Timeout durations in seconds

# Hyprland-specific types
WindowAddress = str  # Hyprland window address (e.g., "0x55b073d05bf0")
Position = List[int]  # [x, y] window coordinates  
Size = List[int]      # [width, height] window dimensions

# Browser integration types
TabData = Dict[str, str | int | bool]  # Individual browser tab data
BrowserTabs = List[TabData]
BrowserSession = Dict[str, str | int | bool | BrowserTabs]

# Neovide session types
NeovideSession = Dict[str, str | bool | Path]

# Terminal program types
RunningProgram = Dict[str, str | List[str]]

# Window information structure
WindowInfo = Dict[str, (
    str |              # address, class, title, etc.
    int |              # pid, fullscreen
    bool |             # floating
    Position |         # window position
    Size |             # window size  
    List[str] |        # grouped windows
    Optional[str] |    # group_id, working_directory
    BrowserSession |   # browser_session
    NeovideSession |   # neovide_session
    RunningProgram     # running_program
)]

# Session data structures
GroupMapping = Dict[Optional[str], List[WindowAddress]]  # group_id -> window addresses
SessionData = Dict[str, str | List[WindowInfo] | GroupMapping]

# Process and command types
ProcessTree = Dict[int, List[int]]  # pid -> child_pids mapping

# Result types for operations that can succeed/fail
OperationResult = Dict[str, bool | str | Any]