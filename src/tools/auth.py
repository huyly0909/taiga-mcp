# auth.py
"""
Authentication and session management tools for Taiga MCP bridge.
"""

import uuid
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP
from pytaigaclient.exceptions import TaigaException

from src.taiga_client import TaigaClientWrapper
from .common import active_sessions, logger


def register_auth_tools(mcp: FastMCP) -> None:
    """Register authentication tools with the FastMCP instance."""
    
    @mcp.tool("ping", description="Tests connectivity to a Taiga instance without authentication.")
    def ping(host: str) -> Dict[str, Any]:
        """
        Tests connectivity to a Taiga instance.

        Args:
            host: The URL of the Taiga instance (e.g., 'https://tree.taiga.io').

        Returns:
            A dictionary containing the ping status and response time.
        """
        import time
        import requests
        
        logger.info(f"Executing ping tool for host '{host}'")
        
        try:
            start_time = time.time()
            
            # Try to ping the Taiga API root endpoint
            api_url = host.rstrip('/') + '/api/v1/'
            response = requests.get(api_url, timeout=10)
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
            
            if response.status_code == 200:
                logger.info(f"Ping successful to '{host}' - Response time: {response_time}ms")
                return {
                    "status": "success",
                    "host": host,
                    "response_time_ms": response_time,
                    "http_status": response.status_code
                }
            else:
                logger.warning(f"Ping to '{host}' returned HTTP {response.status_code}")
                return {
                    "status": "warning", 
                    "host": host,
                    "response_time_ms": response_time,
                    "http_status": response.status_code,
                    "message": f"HTTP {response.status_code} response"
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"Ping to '{host}' timed out")
            return {
                "status": "timeout",
                "host": host,
                "message": "Connection timed out after 10 seconds"
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Could not connect to '{host}'")
            return {
                "status": "error",
                "host": host, 
                "message": "Could not connect to host"
            }
        except Exception as e:
            logger.error(f"Unexpected error pinging '{host}': {e}", exc_info=True)
            return {
                "status": "error",
                "host": host,
                "message": f"Unexpected error: {str(e)}"
            }

    @mcp.tool("login", description="Logs into a Taiga instance using username/password and returns a session_id for subsequent authenticated calls.")
    def login(host: str, username: str, password: str) -> Dict[str, str]:
        """
        Handles Taiga login and creates a session.

        Args:
            host: The URL of the Taiga instance (e.g., 'https://tree.taiga.io').
            username: The Taiga username.
            password: The Taiga password.

        Returns:
            A dictionary containing the session_id upon successful login.
            Example: {"session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"}
        """
        logger.info(f"Executing login tool for user '{username}' on host '{host}'")

        try:
            wrapper = TaigaClientWrapper(host=host)
            login_successful = wrapper.login(username=username, password=password)

            if login_successful:
                # Generate a unique session ID
                new_session_id = str(uuid.uuid4())
                # Store the authenticated wrapper in our manual session store
                active_sessions[new_session_id] = wrapper
                logger.info(
                    f"Login successful for '{username}'. Created session ID: {new_session_id}")
                # Return the session ID to the client
                return {"session_id": new_session_id}
            else:
                # Should not happen if login raises exception on failure, but handle defensively
                logger.error(
                    f"Login attempt for '{username}' returned False unexpectedly.")
                raise RuntimeError("Login failed for an unknown reason.")

        except (ValueError, TaigaException) as e:
            logger.error(f"Login failed for '{username}': {e}", exc_info=False)
            # Re-raise the exception - FastMCP will turn it into an error response
            raise e
        except Exception as e:
            logger.error(
                f"Unexpected error during login for '{username}': {e}", exc_info=True)
            raise RuntimeError(
                f"An unexpected server error occurred during login: {e}")

    @mcp.tool("logout", description="Invalidates the current session_id.")
    def logout(session_id: str) -> Dict[str, Any]:
        """Logs out the current session, invalidating the session_id."""
        logger.info(f"Executing logout for session {session_id[:8]}...")
        # Remove from dict, return None if not found
        client_wrapper = active_sessions.pop(session_id, None)
        if client_wrapper:
            logger.info(f"Session {session_id[:8]} logged out successfully.")
            # No specific API logout call needed usually for token-based auth
            return {"status": "logged_out", "session_id": session_id}
        else:
            logger.warning(
                f"Attempted to log out non-existent session: {session_id}")
            return {"status": "session_not_found", "session_id": session_id}

    @mcp.tool("session_status", description="Checks if the provided session_id is currently active and valid.")
    def session_status(session_id: str) -> Dict[str, Any]:
        """Checks the validity of the current session_id."""
        logger.debug(
            f"Executing session_status check for session {session_id[:8]}...")
        client_wrapper = active_sessions.get(session_id)
        if client_wrapper and client_wrapper.is_authenticated:
            try:
                # Use pytaigaclient users.me() call
                me = client_wrapper.api.users.me()
                # Extract username from the returned dict
                username = me.get('username', 'Unknown')
                logger.debug(
                    f"Session {session_id[:8]} is active for user {username}.")
                return {"status": "active", "session_id": session_id, "username": username}
            except TaigaException:
                logger.warning(
                    f"Session {session_id[:8]} found but token seems invalid (API check failed).")
                # Clean up invalid session
                active_sessions.pop(session_id, None)
                return {"status": "inactive", "reason": "token_invalid", "session_id": session_id}
            except Exception as e: # Catch broader exceptions during the 'me' call
                 logger.error(f"Unexpected error during session status check for {session_id[:8]}: {e}", exc_info=True)
                 # Return a distinct status for unexpected errors during check
                 return {"status": "error", "reason": "check_failed", "session_id": session_id}
        elif client_wrapper: # Client exists but not authenticated (shouldn't happen with current login logic)
            logger.warning(
                f"Session {session_id[:8]} exists but client wrapper is not authenticated.")
            return {"status": "inactive", "reason": "not_authenticated", "session_id": session_id}
        else: # Session ID not found
            logger.debug(f"Session {session_id[:8]} not found.")
            return {"status": "inactive", "reason": "not_found", "session_id": session_id}
