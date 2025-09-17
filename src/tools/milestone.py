# milestone.py
"""
Milestone (Sprint) management tools for Taiga MCP bridge.
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


def register_milestone_tools(mcp: FastMCP) -> None:
    """Register milestone (sprint) management tools with the FastMCP instance."""

    @mcp.tool("list_milestones", description="Lists milestones (sprints) within a specific project.")
    def list_milestones(session_id: str, project_id: int, closed: bool = None) -> List[Dict[str, Any]]:
        """Lists milestones for a project. Optionally filter by closed status."""
        log_operation("list", "milestones", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Milestones list takes individual parameters, not query_params
            milestones = taiga_client_wrapper.api.milestones.list(project=project_id, closed=closed)
            return milestones
        except TaigaException as e:
            handle_taiga_exception("listing", "milestones", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "milestones", f"project {project_id}", e)

    @mcp.tool("create_milestone", description="Creates a new milestone (sprint) within a project.")
    def create_milestone(session_id: str, project_id: int, name: str, estimated_start: str, estimated_finish: str) -> Dict[str, Any]:
        """Creates a milestone. Requires project_id, name, estimated_start (YYYY-MM-DD), and estimated_finish (YYYY-MM-DD)."""
        log_operation("create", "milestone", session_id, f"'{name}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not all([name, estimated_start, estimated_finish]):
            raise ValueError(
                "Milestone requires name, estimated_start, and estimated_finish.")
        try:
            milestone = taiga_client_wrapper.api.milestones.create(
                project=project_id,
                name=name,
                estimated_start=estimated_start,
                estimated_finish=estimated_finish
            )
            log_success("created", "milestone", milestone.get('id', 'N/A'), name)
            return milestone
        except TaigaException as e:
            handle_taiga_exception("creating", "milestone", name, e)
        except Exception as e:
            handle_general_exception("creating", "milestone", name, e)

    @mcp.tool("get_milestone", description="Gets detailed information about a specific milestone by its ID.")
    def get_milestone(session_id: str, milestone_id: int) -> Dict[str, Any]:
        """Retrieves milestone details by ID."""
        log_operation("get", "milestone", session_id, f"ID {milestone_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            milestone = taiga_client_wrapper.api.milestones.get(milestone_id)
            return milestone
        except TaigaException as e:
            handle_taiga_exception("getting", "milestone", milestone_id, e)
        except Exception as e:
            handle_general_exception("getting", "milestone", milestone_id, e)

    @mcp.tool("update_milestone", description="Updates details of an existing milestone.")
    def update_milestone(session_id: str, milestone_id: int, **kwargs) -> Dict[str, Any]:
        """Updates a milestone. Pass fields to update as kwargs (e.g., name, estimated_start, estimated_finish)."""
        log_operation("update", "milestone", session_id, f"ID {milestone_id} with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            if not kwargs:
                 logger.info(f"No fields provided for update on milestone {milestone_id}")
                 return taiga_client_wrapper.api.milestones.get(milestone_id)

            # Get current milestone data to retrieve version
            current_milestone = taiga_client_wrapper.api.milestones.get(milestone_id)
            version = current_milestone.get('version')
            if not version:
                raise ValueError(f"Could not determine version for milestone {milestone_id}")
                
            # Use edit method for partial updates with **kwargs
            updated_milestone = taiga_client_wrapper.api.milestones.edit(
                milestone_id=milestone_id,
                version=version,
                **kwargs
            )
            logger.info(f"Milestone {milestone_id} update request sent.")
            return updated_milestone
        except TaigaException as e:
            handle_taiga_exception("updating", "milestone", milestone_id, e)
        except Exception as e:
            handle_general_exception("updating", "milestone", milestone_id, e)

    @mcp.tool("delete_milestone", description="Deletes a milestone by its ID.")
    def delete_milestone(session_id: str, milestone_id: int) -> Dict[str, Any]:
        """Deletes a milestone by ID."""
        logger.warning(
            f"Executing delete_milestone ID {milestone_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.milestones.delete(milestone_id)
            log_success("deleted", "milestone", milestone_id)
            return {"status": "deleted", "milestone_id": milestone_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "milestone", milestone_id, e)
        except Exception as e:
            handle_general_exception("deleting", "milestone", milestone_id, e)
