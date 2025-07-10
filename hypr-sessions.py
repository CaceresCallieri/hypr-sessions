#!/usr/bin/env python3
"""
Hyprland Session Manager - Main CLI Interface
Captures and restores workspace sessions in Hyprland
"""

import argparse
import sys

from session_capture import SessionCapture
from session_manager import SessionManager
from session_restore import SessionRestore


class HyprlandSessionManager:
    def __init__(self):
        self.capturer = SessionCapture()
        self.restorer = SessionRestore()
        self.manager = SessionManager()

    def capture_session(self, session_name):
        return self.capturer.capture_session(session_name)

    def restore_session(self, session_name):
        return self.restorer.restore_session(session_name)

    def list_sessions(self):
        return self.manager.list_sessions()

    def delete_session(self, session_name):
        return self.manager.delete_session(session_name)


def main():
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

    args = parser.parse_args()

    manager = HyprlandSessionManager()

    if args.action == "save":
        if not args.session_name:
            print("Session name is required for save action")
            sys.exit(1)
        manager.capture_session(args.session_name)

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

