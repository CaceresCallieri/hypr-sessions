#!/usr/bin/env python3
"""
Hyprland Session Manager - Main CLI Interface
Captures and restores workspace sessions in Hyprland
"""

import argparse
import sys
from typing import Optional

from session_delete import SessionDelete
from session_list import SessionList
from session_restore import SessionRestore
from session_save import SessionSaver
from utils import Utils
from validation import (
    SessionValidationError, InvalidSessionNameError, SessionNotFoundError,
    SessionAlreadyExistsError, validate_session_name
)


class HyprlandSessionManager:
    def __init__(self, debug: bool = False) -> None:
        self.debug: bool = debug
        self.saver: SessionSaver = SessionSaver(debug=debug)
        self.restorer: SessionRestore = SessionRestore(debug=debug)
        self.lister: SessionList = SessionList(debug=debug)
        self.deleter: SessionDelete = SessionDelete(debug=debug)

    def save_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            return self.saver.save_session(session_name)
        except SessionValidationError as e:
            print(f"Error: {e}")
            return False

    def restore_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            return self.restorer.restore_session(session_name)
        except SessionValidationError as e:
            print(f"Error: {e}")
            return False

    def list_sessions(self) -> None:
        return self.lister.list_sessions()

    def delete_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            return self.deleter.delete_session(session_name)
        except SessionValidationError as e:
            print(f"Error: {e}")
            return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Hyprland Session Manager")
    parser.add_argument(
        "action",
        choices=["save", "restore", "list", "delete"],
        help="Action to perform",
    )
    parser.add_argument(
        "session_name",
        nargs="?",
        help="Name of the session (required for save/restore/delete)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output for troubleshooting",
    )

    args = parser.parse_args()

    manager = HyprlandSessionManager(debug=args.debug)

    if args.action == "save":
        if not args.session_name:
            print("Session name is required for save action")
            sys.exit(1)
        manager.save_session(args.session_name)

    elif args.action == "restore":
        if not args.session_name:
            print("Session name is required for restore action")
            sys.exit(1)
        manager.restore_session(args.session_name)

    elif args.action == "list":
        manager.list_sessions()

    elif args.action == "delete":
        if not args.session_name:
            print("Session name is required for delete action")
            sys.exit(1)
        manager.delete_session(args.session_name)


if __name__ == "__main__":
    main()

