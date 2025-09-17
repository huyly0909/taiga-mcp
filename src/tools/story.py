# story.py
"""
User Story management tools for Taiga MCP bridge.
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


def register_story_tools(mcp: FastMCP) -> None:
    """Register user story management tools with the FastMCP instance."""

    @mcp.tool("list_user_stories", description="Lists user stories within a specific project, optionally filtered.")
    def list_user_stories(session_id: str, project_id: int, **filters) -> List[Dict[str, Any]]:
        """Lists user stories for a project. Optional filters like 'milestone', 'status', 'assigned_to' can be passed as keyword arguments."""
        log_operation("list", "user_stories", session_id, f"for project {project_id}, filters: {filters}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: User stories use **query_params pattern, so pass project with filters
            query_params = {"project": project_id, **filters}
            stories = taiga_client_wrapper.api.user_stories.list(**query_params)
            return stories
        except TaigaException as e:
            handle_taiga_exception("listing", "user stories", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "user stories", f"project {project_id}", e)

    @mcp.tool("create_user_story", description="Creates a new user story within a project.")
    def create_user_story(session_id: str, project_id: int, subject: str, **kwargs) -> Dict[str, Any]:
        """Creates a user story. Requires project_id and subject. Optional fields (description, milestone_id, status_id, assigned_to_id, etc.) via kwargs."""
        log_operation("create", "user_story", session_id, f"'{subject}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not subject:
            raise ValueError("User story subject cannot be empty.")
        try:
            story = taiga_client_wrapper.api.user_stories.create(
                project=project_id, subject=subject, **kwargs)
            log_success("created", "user story", story.get('id', 'N/A'), subject)
            return story
        except TaigaException as e:
            handle_taiga_exception("creating", "user story", subject, e)
        except Exception as e:
            handle_general_exception("creating", "user story", subject, e)

    @mcp.tool("get_user_story", description="Gets detailed information about a specific user story by its ID.")
    def get_user_story(session_id: str, user_story_id: int) -> Dict[str, Any]:
        """Retrieves user story details by ID."""
        log_operation("get", "user_story", session_id, f"ID {user_story_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            story = taiga_client_wrapper.api.user_stories.get(user_story_id)
            return story
        except TaigaException as e:
            handle_taiga_exception("getting", "user story", user_story_id, e)
        except Exception as e:
            handle_general_exception("getting", "user story", user_story_id, e)

    @mcp.tool("update_user_story", description="Updates details of an existing user story.")
    def update_user_story(session_id: str, user_story_id: int, **kwargs) -> Dict[str, Any]:
        """Updates a user story. Pass fields to update as keyword arguments (e.g., subject, description, status_id, assigned_to)."""
        log_operation("update", "user_story", session_id, f"ID {user_story_id} with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            if not kwargs:
                 logger.info(f"No fields provided for update on user story {user_story_id}")
                 return taiga_client_wrapper.api.user_stories.get(user_story_id)

            # Get current user story data to retrieve version
            current_story = taiga_client_wrapper.api.user_stories.get(user_story_id)
            version = current_story.get('version')
            if not version:
                raise ValueError(f"Could not determine version for user story {user_story_id}")
                
            # Use edit method for partial updates with **kwargs
            updated_story = taiga_client_wrapper.api.user_stories.edit(
                user_story_id=user_story_id,
                version=version,
                **kwargs
            )
            logger.info(f"User story {user_story_id} update request sent.")
            return updated_story
        except TaigaException as e:
            handle_taiga_exception("updating", "user story", user_story_id, e)
        except Exception as e:
            handle_general_exception("updating", "user story", user_story_id, e)

    @mcp.tool("delete_user_story", description="Deletes a user story by its ID.")
    def delete_user_story(session_id: str, user_story_id: int) -> Dict[str, Any]:
        """Deletes a user story by ID."""
        logger.warning(
            f"Executing delete_user_story ID {user_story_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.user_stories.delete(user_story_id)
            log_success("deleted", "user story", user_story_id)
            return {"status": "deleted", "user_story_id": user_story_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "user story", user_story_id, e)
        except Exception as e:
            handle_general_exception("deleting", "user story", user_story_id, e)

    @mcp.tool("assign_user_story_to_user", description="Assigns a specific user story to a specific user.")
    def assign_user_story_to_user(session_id: str, user_story_id: int, user_id: int) -> Dict[str, Any]:
        """Assigns a user story to a user."""
        log_operation("assign", "user_story_to_user", session_id, f"US {user_story_id} -> User {user_id}")
        # Delegate to update_user_story, assuming 'assigned_to' key works
        return update_user_story(session_id, user_story_id, assigned_to=user_id)

    @mcp.tool("unassign_user_story_from_user", description="Unassigns a specific user story (sets assigned user to null).")
    def unassign_user_story_from_user(session_id: str, user_story_id: int) -> Dict[str, Any]:
        """Unassigns a user story."""
        log_operation("unassign", "user_story_from_user", session_id, f"US {user_story_id}")
        # Delegate to update_user_story with assigned_to=None
        return update_user_story(session_id, user_story_id, assigned_to=None)

    @mcp.tool("get_user_story_statuses", description="Lists the available statuses for user stories within a specific project.")
    def get_user_story_statuses(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of user story statuses for a project."""
        log_operation("get", "user_story_statuses", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            statuses = taiga_client_wrapper.api.userstory_statuses.list(query_params={"project_id": project_id})
            return statuses
        except TaigaException as e:
            handle_taiga_exception("getting", "user story statuses", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "user story statuses", f"project {project_id}", e)
