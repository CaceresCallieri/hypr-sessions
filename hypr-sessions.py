#!/usr/bin/env python3
"""
Hyprland Session Manager - Main CLI Interface
Captures and restores workspace sessions in Hyprland
"""

import argparse
import json
import os
import re
import sys
from typing import Optional

from commands.delete import SessionArchive
from commands.list import SessionList
from commands.recover import SessionRecovery
from commands.restore import SessionRestore
from commands.save import SessionSaver
from commands.shared.config import get_config
from commands.shared.operation_result import OperationResult
from commands.shared.utils import Utils
from commands.shared.validation import (
    SessionValidationError, InvalidSessionNameError, SessionNotFoundError,
    SessionAlreadyExistsError, validate_session_name, SessionValidator
)


class HyprlandSessionManager:
    def __init__(self, debug: bool = False, json_output: bool = False) -> None:
        self.debug: bool = debug
        self.json_output: bool = json_output
        self.config = get_config()
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
        except SessionValidationError as e:
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

    def health_check(self) -> bool:
        """Perform comprehensive system health checks"""
        result = OperationResult(operation_name="System Health Check")
        
        # Directory accessibility validation
        self._check_directory_health(result)
        
        # Configuration bounds validation
        self._check_configuration_health(result)
        
        # Recovery system health
        self._check_recovery_health(result)
        
        if self.json_output:
            self._output_json_result(result)
            sys.exit(0 if result.success else 1)
        
        # Normal output mode
        if self.debug:
            result.print_detailed_result()
        else:
            # Print summary for normal operation
            if result.success:
                print(f"✓ System health check passed")
                if result.has_warnings:
                    print(f"  ⚠ {result.warning_count} warnings found")
                    for warning in result.warnings:
                        print(f"    - {warning.message}")
            else:
                print(f"✗ System health check failed")
                for error in result.errors:
                    print(f"  Error: {error.message}")
            
            # Always show successes in health check for transparency
            if result.has_successes:
                print(f"\nHealthy components:")
                for success in result.successes:
                    print(f"  ✓ {success.message}")
        
        return result.success
    
    def _check_directory_health(self, result: OperationResult) -> None:
        """Check directory permissions and accessibility"""
        directories_to_check = [
            (self.config.get_active_sessions_dir(), "active sessions"),
            (self.config.get_archived_sessions_dir(), "archived sessions"),
        ]
        
        for directory, name in directories_to_check:
            try:
                if not directory.exists():
                    result.add_warning(f"{name.title()} directory does not exist: {directory}")
                elif not os.access(directory, os.R_OK | os.W_OK):
                    result.add_error(f"Insufficient permissions for {name} directory: {directory}")
                else:
                    result.add_success(f"{name.title()} directory accessible")
            except Exception as e:
                result.add_error(f"Error checking {name} directory: {e}")
    
    def _check_configuration_health(self, result: OperationResult) -> None:
        """Validate configuration settings and bounds"""
        try:
            # Check archive configuration bounds
            if self.config.archive_max_sessions < 1 or self.config.archive_max_sessions > 1000:
                result.add_error(f"Archive max sessions out of range (1-1000): {self.config.archive_max_sessions}")
            else:
                result.add_success(f"Archive configuration valid (max: {self.config.archive_max_sessions})")
            
            # Check timing configuration bounds
            if self.config.delay_between_instructions < 0.0 or self.config.delay_between_instructions > 10.0:
                result.add_error(f"Delay between instructions out of range (0.0-10.0s): {self.config.delay_between_instructions}")
            else:
                result.add_success(f"Timing configuration valid (delay: {self.config.delay_between_instructions}s)")
            
            # Check browser timeout configuration bounds
            if self.config.browser_tab_file_timeout < 1 or self.config.browser_tab_file_timeout > 120:
                result.add_error(f"Browser tab file timeout out of range (1-120s): {self.config.browser_tab_file_timeout}")
            else:
                result.add_success(f"Browser timeout configuration valid ({self.config.browser_tab_file_timeout}s)")
                
        except Exception as e:
            result.add_error(f"Error validating configuration: {e}")
    
    def _check_recovery_health(self, result: OperationResult) -> None:
        """Check for interrupted recovery operations"""
        try:
            interrupted_recoveries = self.recoverer.check_interrupted_recoveries()
            
            if interrupted_recoveries:
                result.add_warning(f"Found {len(interrupted_recoveries)} interrupted recovery operations")
                if self.debug:
                    for recovery in interrupted_recoveries:
                        result.add_warning(f"Interrupted recovery marker: {recovery}")
            else:
                result.add_success("No interrupted recovery operations found")
                
        except Exception as e:
            result.add_error(f"Error checking recovery system health: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hyprland Session Manager")
    parser.add_argument(
        "action",
        choices=["save", "restore", "list", "delete", "recover", "health"],
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
        
        # Three-layer validation for defense in depth
        try:
            # Layer 1: Format validation - archived names must contain timestamp
            if not re.match(r'^.+-\d{8}-\d{6}$', args.session_name):
                print("Error: Invalid archived session name format. Expected: session-name-YYYYMMDD-HHMMSS")
                sys.exit(1)
            
            # Layer 2: Content validation - extract and validate base session name
            base_name = args.session_name.rsplit('-', 2)[0]  # Remove timestamp suffix safely
            validate_session_name(base_name)  # Reuse comprehensive validation
            
            # Layer 3: New name validation if provided
            if args.new_name:
                validate_session_name(args.new_name)
                
        except SessionValidationError as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: Invalid session name format: {e}")
            sys.exit(1)
        
        manager.recover_session(args.session_name, args.new_name)
    
    elif args.action == "health":
        manager.health_check()


if __name__ == "__main__":
    main()

