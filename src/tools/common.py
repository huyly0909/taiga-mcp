# common.py
"""
Common utilities and shared code for Taiga MCP tools.
"""

import logging
from typing import Dict, Any
from pytaigaclient.exceptions import TaigaException
from src.taiga_client import TaigaClientWrapper

# Get logger for all tool modules
logger = logging.getLogger(__name__)

# Store active sessions: session_id -> TaigaClientWrapper instance
active_sessions: Dict[str, TaigaClientWrapper] = {}


def get_authenticated_client(session_id: str) -> TaigaClientWrapper:
    """
    Retrieves the authenticated TaigaClientWrapper for a given session ID.
    Raises PermissionError if the session is invalid or not found.
    """
    client = active_sessions.get(session_id)
    # Also check if the client object itself exists and is authenticated
    if not client or not client.is_authenticated:
        logger.warning(f"Invalid or expired session ID provided: {session_id}")
        # Raise PermissionError - FastMCP will map this to an appropriate error response
        raise PermissionError(
            f"Invalid or expired session ID: '{session_id}'. Please login again.")
    logger.debug(f"Retrieved valid client for session ID: {session_id}")
    return client


def handle_taiga_exception(operation: str, entity_type: str, entity_id: Any, e: TaigaException) -> None:
    """
    Standard error handling for TaigaException across all tool modules.
    """
    logger.error(f"Taiga API error {operation} {entity_type} {entity_id}: {e}", exc_info=False)
    raise e


def handle_general_exception(operation: str, entity_type: str, entity_id: Any, e: Exception) -> None:
    """
    Standard error handling for general exceptions across all tool modules.
    """
    logger.error(f"Unexpected error {operation} {entity_type} {entity_id}: {e}", exc_info=True)
    raise RuntimeError(f"Server error {operation} {entity_type}: {e}")


def log_operation(operation: str, entity_type: str, session_id: str, extra_info: str = "") -> None:
    """
    Standard operation logging across all tool modules.
    """
    session_short = session_id[:8] if session_id else "unknown"
    info_str = f" {extra_info}" if extra_info else ""
    logger.info(f"Executing {operation}_{entity_type}{info_str} for session {session_short}...")


def log_success(operation: str, entity_type: str, entity_id: Any, entity_name: str = "") -> None:
    """
    Standard success logging across all tool modules.
    """
    name_str = f" '{entity_name}'" if entity_name else ""
    id_str = f" (ID: {entity_id})" if entity_id else ""
    logger.info(f"{entity_type.title()}{name_str} {operation} successful{id_str}.")
