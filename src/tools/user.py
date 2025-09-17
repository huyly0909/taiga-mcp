# user.py
"""
User management tools for Taiga MCP bridge.
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


def register_user_tools(mcp: FastMCP) -> None:
    """Register user management tools with the FastMCP instance."""

    @mcp.tool("get_project_members", description="Lists members of a specific project.")
    def get_project_members(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of members for a project."""
        log_operation("get", "project_members", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Use query_params dictionary for memberships list
            query_params = {"project": project_id}
            members = taiga_client_wrapper.api.memberships.list(query_params=query_params)
            return members
        except TaigaException as e:
            handle_taiga_exception("getting", "members", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "project members", f"project {project_id}", e)

    @mcp.tool("invite_project_user", description="Invites a user to a project by email with a specific role.")
    def invite_project_user(session_id: str, project_id: int, email: str, role_id: int) -> Dict[str, Any]:
        """Invites a user via email to join the project with the specified role ID."""
        log_operation("invite", "project_user", session_id, f"{email} to project {project_id} (role {role_id})")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not email:
            raise ValueError("Email cannot be empty.")
        try:
            # Fix: Use create method with project, role, and username (email) parameters
            invitation_result = taiga_client_wrapper.api.memberships.create(
                project=project_id, role=role_id, username=email
            )
            logger.info(f"Invitation request sent to {email} for project {project_id}.")
            return invitation_result
        except TaigaException as e:
            handle_taiga_exception("inviting", "user", f"{email} to project {project_id}", e)
        except Exception as e:
            handle_general_exception("inviting", "user", f"{email} to project {project_id}", e)
