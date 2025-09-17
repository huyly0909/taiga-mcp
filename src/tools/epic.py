# epic.py
"""
Epic management tools for Taiga MCP bridge.
"""

from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP
from pytaigaclient.exceptions import TaigaException

from .common import (
    get_authenticated_client, 
    handle_taiga_exception,
    handle_general_exception,
    log_operation,
    log_success,
    logger
)


def register_epic_tools(mcp: FastMCP) -> None:
    """Register epic management tools with the FastMCP instance."""

    @mcp.tool("list_epics", description="Lists epics within a specific project, optionally filtered.")
    def list_epics(session_id: str, project_id: int, **filters) -> List[Dict[str, Any]]:
        """Lists epics for a project. Optional filters like 'status', 'assigned_to' can be passed as keyword arguments."""
        log_operation("list", "epics", session_id, f"for project {project_id}, filters: {filters}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Pass filters as query_params dictionary with project included
            query_params = {"project": project_id, **filters}
            epics = taiga_client_wrapper.api.epics.list(query_params=query_params)
            return epics
        except TaigaException as e:
            handle_taiga_exception("listing", "epics", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "epics", f"project {project_id}", e)

    @mcp.tool("create_epic", description="Creates a new epic within a project.")
    def create_epic(session_id: str, project_id: int, subject: str, **kwargs) -> Dict[str, Any]:
        """Creates an epic. Requires project_id and subject. Optional fields (description, status_id, assigned_to_id, color, etc.) via kwargs."""
        log_operation("create", "epic", session_id, f"'{subject}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not subject:
            raise ValueError("Epic subject cannot be empty.")
        try:
            epic = taiga_client_wrapper.api.epics.create(project=project_id, subject=subject, **kwargs)
            log_success("created", "epic", epic.get('id', 'N/A'), subject)
            return epic
        except TaigaException as e:
            handle_taiga_exception("creating", "epic", subject, e)
        except Exception as e:
            handle_general_exception("creating", "epic", subject, e)

    @mcp.tool("get_epic", description="Gets detailed information about a specific epic by its ID.")
    def get_epic(session_id: str, epic_id: int) -> Dict[str, Any]:
        """Retrieves epic details by ID."""
        log_operation("get", "epic", session_id, f"ID {epic_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            epic = taiga_client_wrapper.api.epics.get(epic_id)
            return epic
        except TaigaException as e:
            handle_taiga_exception("getting", "epic", epic_id, e)
        except Exception as e:
            handle_general_exception("getting", "epic", epic_id, e)

    @mcp.tool("update_epic", description="Updates details of an existing epic.")
    def update_epic(session_id: str, epic_id: int, **kwargs) -> Dict[str, Any]:
        """Updates an epic. Pass fields to update as keyword arguments (e.g., subject, description, status_id, assigned_to, color)."""
        log_operation("update", "epic", session_id, f"ID {epic_id} with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            if not kwargs:
                 logger.info(f"No fields provided for update on epic {epic_id}")
                 return taiga_client_wrapper.api.epics.get(epic_id)

            # Get current epic data to retrieve version
            current_epic = taiga_client_wrapper.api.epics.get(epic_id)
            version = current_epic.get('version')
            if not version:
                raise ValueError(f"Could not determine version for epic {epic_id}")
                
            # Use edit method for partial updates with **kwargs
            updated_epic = taiga_client_wrapper.api.epics.edit(
                epic_id=epic_id,
                version=version,
                **kwargs
            )
            logger.info(f"Epic {epic_id} update request sent.")
            return updated_epic
        except TaigaException as e:
            handle_taiga_exception("updating", "epic", epic_id, e)
        except Exception as e:
            handle_general_exception("updating", "epic", epic_id, e)

    @mcp.tool("delete_epic", description="Deletes an epic by its ID.")
    def delete_epic(session_id: str, epic_id: int) -> Dict[str, Any]:
        """Deletes an epic by ID."""
        logger.warning(
            f"Executing delete_epic ID {epic_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.epics.delete(epic_id)
            log_success("deleted", "epic", epic_id)
            return {"status": "deleted", "epic_id": epic_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "epic", epic_id, e)
        except Exception as e:
            handle_general_exception("deleting", "epic", epic_id, e)

    @mcp.tool("assign_epic_to_user", description="Assigns a specific epic to a specific user.")
    def assign_epic_to_user(session_id: str, epic_id: int, user_id: int) -> Dict[str, Any]:
        """Assigns an epic to a user."""
        log_operation("assign", "epic_to_user", session_id, f"Epic {epic_id} -> User {user_id}")
        # Delegate to update_epic
        return update_epic(session_id, epic_id, assigned_to=user_id)

    @mcp.tool("unassign_epic_from_user", description="Unassigns a specific epic (sets assigned user to null).")
    def unassign_epic_from_user(session_id: str, epic_id: int) -> Dict[str, Any]:
        """Unassigns an epic."""
        log_operation("unassign", "epic_from_user", session_id, f"Epic {epic_id}")
        # Delegate to update_epic
        return update_epic(session_id, epic_id, assigned_to=None)
