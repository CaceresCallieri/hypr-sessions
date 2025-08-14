#!/usr/bin/env python3
"""
Hyprland Session Manager - Main CLI Interface
Captures and restores workspace sessions in Hyprland
"""

import argparse
import json
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
    def __init__(self, debug: bool = False, json_output: bool = False) -> None:
        self.debug: bool = debug
        self.json_output: bool = json_output
        self.saver: SessionSaver = SessionSaver(debug=debug)
        self.restorer: SessionRestore = SessionRestore(debug=debug)
        self.lister: SessionList = SessionList(debug=debug)
        self.deleter: SessionDelete = SessionDelete(debug=debug)

    def save_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            result = self.saver.save_session(session_name)
            
            if self.json_output:
                self._output_json_result(result)
                sys.exit(0 if result.success else 1)
            
            # Normal output mode
            if self.debug:
                result.print_detailed_result()
            else:
                # Print summary for normal operation
                if result.success:
                    print(f"✓ Session saved successfully")
                    if result.has_warnings:
                        print(f"  ⚠ {result.warning_count} warnings occurred during save")
                else:
                    print(f"✗ Session save failed")
                    for error in result.errors:
                        print(f"  Error: {error.message}")
            
            return result.success
        except SessionValidationError as e:
            if self.json_output:
                error_result = {
                    "success": False,
                    "operation": f"Save session '{session_name}'",
                    "error": str(e),
                    "messages": [{"status": "error", "message": str(e), "context": None}]
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)
            else:
                print(f"Error: {e}")
            return False

    def restore_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            result = self.restorer.restore_session(session_name)
            
            if self.json_output:
                self._output_json_result(result)
                sys.exit(0 if result.success else 1)
            
            # Normal output mode
            if self.debug:
                result.print_detailed_result()
            else:
                # Print summary for normal operation
                if result.success:
                    print(f"✓ Session restored successfully")
                    if result.has_warnings:
                        print(f"  ⚠ {result.warning_count} warnings occurred during restore")
                else:
                    print(f"✗ Session restore failed")
                    for error in result.errors:
                        print(f"  Error: {error.message}")
            
            return result.success
        except SessionValidationError as e:
            if self.json_output:
                error_result = {
                    "success": False,
                    "operation": f"Restore session '{session_name}'",
                    "error": str(e),
                    "messages": [{"status": "error", "message": str(e), "context": None}]
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)
            else:
                print(f"Error: {e}")
            return False

    def list_sessions(self) -> None:
        result = self.lister.list_sessions()
        
        if self.json_output:
            self._output_json_result(result)
            sys.exit(0 if result.success else 1)
        
        # Normal output mode - CLI handles all presentation
        if result.success and result.data:
            self._print_session_list(result.data)
        
        if self.debug:
            result.print_detailed_result()
        else:
            # For normal operation, just show warnings/errors if any
            if result.has_warnings:
                print(f"⚠ {result.warning_count} warnings occurred")
            if result.has_errors:
                print(f"✗ {result.error_count} errors occurred")
                for error in result.errors:
                    print(f"  Error: {error.message}")
    
    def _print_session_list(self, data: dict) -> None:
        """Handle session list presentation in CLI"""
        sessions = data.get('sessions', [])
        
        if not sessions:
            print("No saved sessions found")
            return

        print("Saved sessions:")
        print("-" * 40)

        for session in sessions:
            if session.get('valid', False):
                print(f"  {session['name']}")
                print(f"    Windows: {session['windows']}")
                print(f"    Files: {session['files']}")
                print(f"    Saved: {session['timestamp']}")
                print()
            else:
                error = session.get('error', 'Unknown error')
                print(f"  {session['name']} (Error: {error})")
                print()
    
    def _output_json_result(self, result) -> None:
        """Output structured JSON result"""
        json_result = {
            "success": result.success,
            "operation": result.operation_name,
            "data": result.data,
            "messages": [
                {
                    "status": msg.status.value,
                    "message": msg.message,
                    "context": msg.context
                } for msg in result.messages
            ],
            "summary": {
                "success_count": result.success_count,
                "warning_count": result.warning_count,
                "error_count": result.error_count
            }
        }
        print(json.dumps(json_result, indent=2))

    def delete_session(self, session_name: str) -> bool:
        try:
            validate_session_name(session_name)
            result = self.deleter.delete_session(session_name)
            
            if self.json_output:
                self._output_json_result(result)
                sys.exit(0 if result.success else 1)
            
            # Normal output mode
            if self.debug:
                result.print_detailed_result()
            else:
                # Print summary for normal operation
                if result.success:
                    print(f"✓ Session deleted successfully")
                    if result.has_warnings:
                        print(f"  ⚠ {result.warning_count} warnings occurred during deletion")
                else:
                    print(f"✗ Session deletion failed")
                    for error in result.errors:
                        print(f"  Error: {error.message}")
            
            return result.success
        except SessionValidationError as e:
            if self.json_output:
                error_result = {
                    "success": False,
                    "operation": f"Delete session '{session_name}'",
                    "error": str(e),
                    "messages": [{"status": "error", "message": str(e), "context": None}]
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)
            else:
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
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format for UI integration",
    )

    args = parser.parse_args()

    manager = HyprlandSessionManager(debug=args.debug, json_output=args.json)

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

