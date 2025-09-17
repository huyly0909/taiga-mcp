# project.py
"""
Project management tools for Taiga MCP bridge.
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


def register_project_tools(mcp: FastMCP) -> None:
    """Register project management tools with the FastMCP instance."""

    @mcp.tool("list_projects", description="Lists projects accessible to the user associated with the provided session_id.")
    def list_projects(session_id: str) -> List[Dict[str, Any]]:
        """Lists projects accessible by the authenticated user."""
        log_operation("list", "projects", session_id)
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            projects = taiga_client_wrapper.api.projects.list()
            logger.info(
                f"list_projects successful for session {session_id[:8]}, found {len(projects)} projects.")
            return projects
        except TaigaException as e:
            handle_taiga_exception("listing", "projects", "", e)
        except Exception as e:
            handle_general_exception("listing", "projects", "", e)

    @mcp.tool("list_all_projects", description="Lists all projects visible to the user (requires admin privileges for full list). Uses the provided session_id.")
    def list_all_projects(session_id: str) -> List[Dict[str, Any]]:
        """Lists all projects visible to the authenticated user (scope depends on permissions)."""
        log_operation("list_all", "projects", session_id)
        # pytaigaclient's list() likely behaves similarly to python-taiga's
        return list_projects(session_id)

    @mcp.tool("get_project", description="Gets detailed information about a specific project by its ID.")
    def get_project(session_id: str, project_id: int) -> Dict[str, Any]:
        """Retrieves project details by ID."""
        log_operation("get", "project", session_id, f"ID {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            project = taiga_client_wrapper.api.projects.get(project_id)
            return project
        except TaigaException as e:
            handle_taiga_exception("getting", "project", project_id, e)
        except Exception as e:
            handle_general_exception("getting", "project", project_id, e)

    @mcp.tool("get_project_by_slug", description="Gets detailed information about a specific project by its slug.")
    def get_project_by_slug(session_id: str, slug: str) -> Dict[str, Any]:
        """Retrieves project details by slug."""
        log_operation("get", "project_by_slug", session_id, f"'{slug}'")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            project = taiga_client_wrapper.api.projects.get(slug=slug)
            return project
        except TaigaException as e:
            handle_taiga_exception("getting", "project by slug", slug, e)
        except Exception as e:
            handle_general_exception("getting", "project by slug", slug, e)

    @mcp.tool("create_project", description="Creates a new project.")
    def create_project(session_id: str, name: str, description: str, **kwargs) -> Dict[str, Any]:
        """Creates a new project. Requires name and description. Optional args (e.g., is_private) via kwargs."""
        log_operation("create", "project", session_id, f"'{name}' with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not name or not description:
            raise ValueError("Project name and description are required.")
        try:
            new_project = taiga_client_wrapper.api.projects.create(
                name=name, description=description, **kwargs
            )
            log_success("created", "project", new_project.get('id', 'N/A'), name)
            return new_project
        except TaigaException as e:
            handle_taiga_exception("creating", "project", name, e)
        except Exception as e:
            handle_general_exception("creating", "project", name, e)

    @mcp.tool("update_project", description="Updates details of an existing project.")
    def update_project(session_id: str, project_id: int, **kwargs) -> Dict[str, Any]:
        """Updates a project. Pass fields to update as keyword arguments (e.g., name='New Name', description='New Desc')."""
        log_operation("update", "project", session_id, f"ID {project_id} with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            if not kwargs:
                 logger.info(f"No fields provided for update on project {project_id}")
                 return taiga_client_wrapper.api.projects.get(project_id)

            # First fetch the project to get its current version
            current_project = taiga_client_wrapper.api.projects.get(project_id)
            version = current_project.get('version')
            if not version:
                raise ValueError(f"Could not determine version for project {project_id}")
                
            # Fix: Use edit method for partial updates with **kwargs
            updated_project = taiga_client_wrapper.api.projects.edit(
                project_id=project_id, 
                version=version,
                **kwargs
            )
            logger.info(f"Project {project_id} update request sent.")
            return updated_project
        except TaigaException as e:
            handle_taiga_exception("updating", "project", project_id, e)
        except Exception as e:
            handle_general_exception("updating", "project", project_id, e)

    @mcp.tool("delete_project", description="Deletes a project by its ID. This is irreversible.")
    def delete_project(session_id: str, project_id: int) -> Dict[str, Any]:
        """Deletes a project by ID."""
        logger.warning(
            f"Executing delete_project ID {project_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.projects.delete(project_id)
            log_success("deleted", "project", project_id)
            return {"status": "deleted", "project_id": project_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "project", project_id, e)
        except Exception as e:
            handle_general_exception("deleting", "project", project_id, e)
