# issue.py
"""
Issue management tools for Taiga MCP bridge.
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


def register_issue_tools(mcp: FastMCP) -> None:
    """Register issue management tools with the FastMCP instance."""

    @mcp.tool("list_issues", description="Lists issues within a specific project, optionally filtered.")
    def list_issues(session_id: str, project_id: int, **filters) -> List[Dict[str, Any]]:
        """Lists issues for a project. Optional filters like 'milestone', 'status', 'priority', 'severity', 'type', 'assigned_to' can be passed as kwargs."""
        log_operation("list", "issues", session_id, f"for project {project_id}, filters: {filters}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Pass filters as query_params dictionary with project included
            query_params = {"project": project_id, **filters}
            issues = taiga_client_wrapper.api.issues.list(query_params=query_params)
            return issues
        except TaigaException as e:
            handle_taiga_exception("listing", "issues", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "issues", f"project {project_id}", e)

    @mcp.tool("create_issue", description="Creates a new issue within a project.")
    def create_issue(session_id: str, project_id: int, subject: str, priority_id: int, status_id: int, severity_id: int, type_id: int, **kwargs) -> Dict[str, Any]:
        """Creates an issue. Requires project_id, subject, priority_id, status_id, severity_id, type_id. Optional fields (description, assigned_to_id, etc.) via kwargs."""
        log_operation("create", "issue", session_id, f"'{subject}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not subject:
            raise ValueError("Issue subject cannot be empty.")
        try:
            # Fix: Pass required IDs in data dictionary
            data = {
                "priority": priority_id,
                "status": status_id,
                "severity": severity_id,
                "type": type_id,
                **kwargs
            }
            issue = taiga_client_wrapper.api.issues.create(
                project=project_id,
                subject=subject,
                data=data
            )
            log_success("created", "issue", issue.get('id', 'N/A'), subject)
            return issue
        except TaigaException as e:
            handle_taiga_exception("creating", "issue", subject, e)
        except Exception as e:
            handle_general_exception("creating", "issue", subject, e)

    @mcp.tool("get_issue", description="Gets detailed information about a specific issue by its ID.")
    def get_issue(session_id: str, issue_id: int) -> Dict[str, Any]:
        """Retrieves issue details by ID."""
        log_operation("get", "issue", session_id, f"ID {issue_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            issue = taiga_client_wrapper.api.issues.get(issue_id)
            return issue
        except TaigaException as e:
            handle_taiga_exception("getting", "issue", issue_id, e)
        except Exception as e:
            handle_general_exception("getting", "issue", issue_id, e)

    @mcp.tool("update_issue", description="Updates details of an existing issue.")
    def update_issue(session_id: str, issue_id: int, **kwargs) -> Dict[str, Any]:
        """Updates an issue. Pass fields to update as keyword arguments (e.g., subject, description, status_id, assigned_to)."""
        log_operation("update", "issue", session_id, f"ID {issue_id} with data: {kwargs}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            if not kwargs:
                 logger.info(f"No fields provided for update on issue {issue_id}")
                 return taiga_client_wrapper.api.issues.get(issue_id)

            # Get current issue data to retrieve version
            current_issue = taiga_client_wrapper.api.issues.get(issue_id)
            version = current_issue.get('version')
            if not version:
                raise ValueError(f"Could not determine version for issue {issue_id}")
                
            # Use edit method for partial updates with data dictionary
            updated_issue = taiga_client_wrapper.api.issues.edit(
                issue_id=issue_id,
                version=version,
                data=kwargs
            )
            logger.info(f"Issue {issue_id} update request sent.")
            return updated_issue
        except TaigaException as e:
            handle_taiga_exception("updating", "issue", issue_id, e)
        except Exception as e:
            handle_general_exception("updating", "issue", issue_id, e)

    @mcp.tool("delete_issue", description="Deletes an issue by its ID.")
    def delete_issue(session_id: str, issue_id: int) -> Dict[str, Any]:
        """Deletes an issue by ID."""
        logger.warning(
            f"Executing delete_issue ID {issue_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.issues.delete(issue_id)
            log_success("deleted", "issue", issue_id)
            return {"status": "deleted", "issue_id": issue_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "issue", issue_id, e)
        except Exception as e:
            handle_general_exception("deleting", "issue", issue_id, e)

    @mcp.tool("assign_issue_to_user", description="Assigns a specific issue to a specific user.")
    def assign_issue_to_user(session_id: str, issue_id: int, user_id: int) -> Dict[str, Any]:
        """Assigns an issue to a user."""
        log_operation("assign", "issue_to_user", session_id, f"Issue {issue_id} -> User {user_id}")
        # Delegate to update_issue
        return update_issue(session_id, issue_id, assigned_to=user_id)

    @mcp.tool("unassign_issue_from_user", description="Unassigns a specific issue (sets assigned user to null).")
    def unassign_issue_from_user(session_id: str, issue_id: int) -> Dict[str, Any]:
        """Unassigns an issue."""
        log_operation("unassign", "issue_from_user", session_id, f"Issue {issue_id}")
        # Delegate to update_issue
        return update_issue(session_id, issue_id, assigned_to=None)

    @mcp.tool("get_issue_statuses", description="Lists the available statuses for issues within a specific project.")
    def get_issue_statuses(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of issue statuses for a project."""
        log_operation("get", "issue_statuses", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            statuses = taiga_client_wrapper.api.issue_statuses.list(query_params={"project_id": project_id})
            return statuses
        except TaigaException as e:
            handle_taiga_exception("getting", "issue statuses", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "issue statuses", f"project {project_id}", e)

    @mcp.tool("get_issue_priorities", description="Lists the available priorities for issues within a specific project.")
    def get_issue_priorities(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of issue priorities for a project."""
        log_operation("get", "issue_priorities", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            priorities = taiga_client_wrapper.api.issue_priorities.list(query_params={"project_id": project_id})
            return priorities
        except TaigaException as e:
            handle_taiga_exception("getting", "issue priorities", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "issue priorities", f"project {project_id}", e)

    @mcp.tool("get_issue_severities", description="Lists the available severities for issues within a specific project.")
    def get_issue_severities(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of issue severities for a project."""
        log_operation("get", "issue_severities", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            severities = taiga_client_wrapper.api.issue_severities.list(query_params={"project_id": project_id})
            return severities
        except TaigaException as e:
            handle_taiga_exception("getting", "issue severities", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "issue severities", f"project {project_id}", e)

    @mcp.tool("get_issue_types", description="Lists the available types for issues within a specific project.")
    def get_issue_types(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Retrieves the list of issue types for a project."""
        log_operation("get", "issue_types", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            types = taiga_client_wrapper.api.issue_types.list(query_params={"project_id": project_id})
            return types
        except TaigaException as e:
            handle_taiga_exception("getting", "issue types", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("getting", "issue types", f"project {project_id}", e)
