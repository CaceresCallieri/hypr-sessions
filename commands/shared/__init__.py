"""
Shared utilities and core types for hypr-sessions commands
"""

from .config import SessionConfig, get_config
from .operation_result import OperationResult
from .session_types import *
from .utils import Utils
from .validation import (
    SessionError, SessionValidationError, SessionNotFoundError,
    InvalidSessionNameError, SessionAlreadyExistsError,
    SessionValidator, validate_session_name
)

__all__ = [
    'SessionConfig', 'get_config',
    'OperationResult',
    'Utils',
    'SessionError', 'SessionValidationError', 'SessionNotFoundError',
    'InvalidSessionNameError', 'SessionAlreadyExistsError',
    'SessionValidator', 'validate_session_name'
]