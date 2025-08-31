#!/usr/bin/env python3
"""
Hyprland Session Manager - Main CLI Interface
Captures and restores workspace sessions in Hyprland
"""

import argparse
import json
import sys
from typing import Optional

from commands.delete import SessionArchive
from commands.list import SessionList
from commands.recover import SessionRecovery
from commands.restore import SessionRestore
from commands.save import SessionSaver
from commands.shared.utils import Utils
from commands.shared.validation import (
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
        self.archiver: SessionArchive = SessionArchive(debug=debug)
        self.recoverer: SessionRecovery = SessionRecovery(debug=debug)

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

    def list_sessions(self, archived: bool = False, show_all: bool = False) -> None:
        result = self.lister.list_sessions(archived=archived, show_all=show_all)
        
        if self.json_output:
            self._output_json_result(result)
            sys.exit(0 if result.success else 1)
        
        # Normal output mode - CLI handles all presentation
        if result.success and result.data:
            self._print_session_list(result.data, archived=archived, show_all=show_all)
        
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
    
    def _print_session_list(self, data: dict, archived: bool = False, show_all: bool = False) -> None:
        """Handle session list presentation in CLI"""
        active_sessions = data.get('active_sessions', [])
        archived_sessions = data.get('archived_sessions', [])
        
        # Handle legacy format for backward compatibility
        if 'sessions' in data and not active_sessions and not archived_sessions:
            active_sessions = data.get('sessions', [])
        
        if show_all:
            # Show both active and archived
            if active_sessions:
                print(f"Active sessions ({len(active_sessions)}):")
                print("-" * 40)
                self._print_sessions_section(active_sessions, session_type="active")
            
            if archived_sessions:
                print(f"Archived sessions ({len(archived_sessions)}):")
                print("-" * 40)
                self._print_sessions_section(archived_sessions, session_type="archived")
            
            if not active_sessions and not archived_sessions:
                print("No sessions found")
        elif archived:
            # Show only archived
            if archived_sessions:
                print(f"Archived sessions ({len(archived_sessions)}):")
                print("-" * 40)
                self._print_sessions_section(archived_sessions, session_type="archived")
            else:
                print("No archived sessions found")
        else:
            # Show only active (default behavior)
            if active_sessions:
                print("Saved sessions:")
                print("-" * 40)
                self._print_sessions_section(active_sessions, session_type="active")
            else:
                print("No saved sessions found")
    
    def _print_sessions_section(self, sessions: list, session_type: str) -> None:
        """Print a section of sessions with proper formatting"""
        for session in sessions:
            if session.get('valid', False):
                print(f"  {session['name']}")
                if session_type == "archived":
                    print(f"    Archived: {session.get('archive_timestamp', 'Unknown')}")
                    print(f"    Original name: {session.get('original_name', session['name'])}")
                else:
                    print(f"    Windows: {session.get('windows', 0)}")
                    print(f"    Saved: {session.get('timestamp', 'Unknown')}")
                print(f"    Files: {session.get('files', 0)}")
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
            result = self.archiver.archive_session(session_name)
            
            if self.json_output:
                self._output_json_result(result)
                sys.exit(0 if result.success else 1)
            
            # Normal output mode
            if self.debug:
                result.print_detailed_result()
            else:
                # Print summary for normal operation
                if result.success:
                    print(f"✓ Session archived successfully")
                    if result.has_warnings:
                        print(f"  ⚠ {result.warning_count} warnings occurred during archiving")
                else:
                    print(f"✗ Session archiving failed")
                    for error in result.errors:
                        print(f"  Error: {error.message}")
            
            return result.success
        except SessionValidationError as e:
            if self.json_output:
                error_result = {
                    "success": False,
                    "operation": f"Archive session '{session_name}'",
                    "error": str(e),
                    "messages": [{"status": "error", "message": str(e), "context": None}]
                }
                print(json.dumps(error_result, indent=2))
                sys.exit(1)
            else:
                print(f"Error: {e}")
            return False

    def recover_session(self, archived_session_name: str, new_name: Optional[str] = None) -> bool:
        try:
            result = self.recoverer.recover_session(archived_session_name, new_name)
            
            if self.json_output:
                self._output_json_result(result)
                sys.exit(0 if result.success else 1)
            
            # Normal output mode
            if self.debug:
                result.print_detailed_result()
            else:
                # Print summary for normal operation
                if result.success:
                    recovered_name = result.data.get("recovered_session_name", archived_session_name) if result.data else archived_session_name
                    print(f"✓ Session recovered successfully as '{recovered_name}'")
                    if result.has_warnings:
                        print(f"  ⚠ {result.warning_count} warnings occurred during recovery")
                else:
                    print(f"✗ Session recovery failed")
                    for error in result.errors:
                        print(f"  Error: {error.message}")
            
            return result.success
        except Exception as e:
            if self.json_output:
                error_result = {
                    "success": False,
                    "operation": f"Recover archived session '{archived_session_name}'",
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
        choices=["save", "restore", "list", "delete", "recover"],
        help="Action to perform",
    )
    parser.add_argument(
        "session_name",
        nargs="?",
        help="Name of the session (required for save/restore/delete/recover)",
    )
    parser.add_argument(
        "new_name",
        nargs="?",
        help="New name for recovered session (optional for recover action)",
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
    parser.add_argument(
        "--archived",
        action="store_true",
        help="Show only archived sessions (list command only)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show both active and archived sessions (list command only)",
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
        manager.list_sessions(archived=args.archived, show_all=args.all)

    elif args.action == "delete":
        if not args.session_name:
            print("Session name is required for delete action")
            sys.exit(1)
        manager.delete_session(args.session_name)

    elif args.action == "recover":
        if not args.session_name:
            print("Archived session name is required for recover action")
            sys.exit(1)
        manager.recover_session(args.session_name, args.new_name)


if __name__ == "__main__":
    main()

