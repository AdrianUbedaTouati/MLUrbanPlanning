"""
Global cancel flags for long-running operations
Allows users to cancel indexing operations in progress
"""
from threading import Lock
from typing import Dict

# Global dictionary to store cancel flags per user
# Structure: {user_id: {'indexing': bool}}
_cancel_flags: Dict[int, Dict[str, bool]] = {}
_lock = Lock()


def set_cancel_flag(user_id: int, operation: str = 'indexing'):
    """
    Set cancellation flag for a user's operation

    Args:
        user_id: User ID
        operation: Operation type ('indexing', etc.)
    """
    with _lock:
        if user_id not in _cancel_flags:
            _cancel_flags[user_id] = {}
        _cancel_flags[user_id][operation] = True


def check_cancel_flag(user_id: int, operation: str = 'indexing') -> bool:
    """
    Check if cancellation has been requested

    Args:
        user_id: User ID
        operation: Operation type ('indexing', etc.)

    Returns:
        True if cancellation requested, False otherwise
    """
    with _lock:
        return _cancel_flags.get(user_id, {}).get(operation, False)


def clear_cancel_flag(user_id: int, operation: str = 'indexing'):
    """
    Clear cancellation flag for a user's operation

    Args:
        user_id: User ID
        operation: Operation type ('indexing', etc.)
    """
    with _lock:
        if user_id in _cancel_flags and operation in _cancel_flags[user_id]:
            del _cancel_flags[user_id][operation]


def clear_all_flags(user_id: int):
    """
    Clear all cancellation flags for a user

    Args:
        user_id: User ID
    """
    with _lock:
        if user_id in _cancel_flags:
            del _cancel_flags[user_id]
