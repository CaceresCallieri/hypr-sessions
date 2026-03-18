"""
Type definitions for hypr-sessions
Provides meaningful type aliases for complex or domain-specific concepts
"""

from typing import Dict, List, Optional, Any, TypedDict
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
# Uses functional TypedDict form because "class" is a Python reserved word
# but is the actual key name in hyprctl JSON output. total=False because
# fields like browser_session, neovide_session, running_program, and
# working_directory are only added conditionally during session save.
WindowInfo = TypedDict("WindowInfo", {
    "address": str,
    "class": str,
    "title": str,
    "pid": int,
    "floating": bool,
    "fullscreen": bool,
    "at": Position,
    "size": Size,
    "grouped": List[str],
    "group_id": Optional[str],
    "initialClass": str,
    "initialTitle": str,
    "swallowing": str,
    "working_directory": Optional[str],
    "browser_session": Optional[BrowserSession],
    "neovide_session": Optional[NeovideSession],
    "running_program": Optional[RunningProgram],
    "launch_command": str,
}, total=False)

# Session data structures
GroupMapping = Dict[Optional[str], List[WindowAddress]]  # group_id -> window addresses
SessionData = Dict[str, str | List[WindowInfo] | GroupMapping]

# Process and command types
ProcessTree = Dict[int, List[int]]  # pid -> child_pids mapping

# Result types for operations that can succeed/fail
OperationResult = Dict[str, bool | str | Any]