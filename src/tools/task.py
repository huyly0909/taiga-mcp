# task.py
"""
Task management tools for Taiga MCP bridge.
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


def register_task_tools(mcp: FastMCP) -> None:
    """Register task management tools with the FastMCP instance."""

    @mcp.tool("list_tasks", description="Lists tasks within a specific project, optionally filtered.")
    def list_tasks(session_id: str, project_id: int, **filters) -> List[Dict[str, Any]]:
        """Lists tasks for a project. Optional filters like 'milestone', 'status', 'user_story', 'assigned_to' can be passed as keyword arguments."""
        log_operation("list", "tasks", session_id, f"for project {project_id}, filters: {filters}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Pass filters as query_params dictionary with project included
            query_params = {"project": project_id, **filters}
            tasks = taiga_client_wrapper.api.tasks.list(query_params=query_params)
            return tasks
        except TaigaException as e:
            handle_taiga_exception("listing", "tasks", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "tasks", f"project {project_id}", e)

    @mcp.tool("create_task", description="Creates a new task within a project with full field support.")
    def create_task(session_id: str, project_id: int, subject: str, description: str = None, 
                   due_date: str = None, tags: str = None, assigned_to: int = None, 
                   milestone_id: int = None, status_id: int = None, user_story_id: int = None, 
                   **kwargs) -> Dict[str, Any]:
        """
        Creates a comprehensive task with all available fields.
        
        Args:
            session_id: User session ID
            project_id: Project ID where task will be created
            subject: Task title/subject (required)
            description: Detailed task description (Markdown supported)
            due_date: Due date in YYYY-MM-DD format 
            tags: Comma-separated tags (e.g., "frontend,urgent,bug")
            assigned_to: User ID to assign task to
            milestone_id: Milestone/sprint ID to assign task to
            status_id: Status ID for the task
            user_story_id: User story ID to link task to
            **kwargs: Additional optional fields (is_blocked, blocked_note, etc.)
        
        Returns:
            Dict containing the created task details
        """
        log_operation("create", "task", session_id, f"'{subject}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        if not subject:
            raise ValueError("Task subject cannot be empty.")
        
        try:
            # Build task data with all provided fields
            task_data = {}
            
            if description:
                task_data["description"] = description
            if due_date:
                task_data["due_date"] = due_date
            if tags:
                # Convert comma-separated tags to list
                task_data["tags"] = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if assigned_to:
                task_data["assigned_to"] = assigned_to
            if milestone_id:
                task_data["milestone"] = milestone_id
            if status_id:
                task_data["status"] = status_id
            if user_story_id:
                task_data["user_story"] = user_story_id
                
            # Add any additional kwargs
            task_data.update(kwargs)
            
            task = taiga_client_wrapper.api.tasks.create(project=project_id, subject=subject, data=task_data)
            log_success("created", "task", task.get('id', 'N/A'), subject)
            return task
        except TaigaException as e:
            handle_taiga_exception("creating", "task", subject, e)
        except Exception as e:
            handle_general_exception("creating", "task", subject, e)

    @mcp.tool("get_task", description="Gets detailed information about a specific task by its ID.")
    def get_task(session_id: str, task_id: int) -> Dict[str, Any]:
        """Retrieves task details by ID."""
        log_operation("get", "task", session_id, f"ID {task_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            task = taiga_client_wrapper.api.tasks.get(task_id)
            return task
        except TaigaException as e:
            handle_taiga_exception("getting", "task", task_id, e)
        except Exception as e:
            handle_general_exception("getting", "task", task_id, e)

    @mcp.tool("update_task", description="Updates details of an existing task with full field support.")
    def update_task(session_id: str, task_id: int, subject: str = None, description: str = None,
                   due_date: str = None, tags: str = None, assigned_to: int = None,
                   milestone_id: int = None, status_id: int = None, user_story_id: int = None,
                   **kwargs) -> Dict[str, Any]:
        """
        Updates a task with comprehensive field support.
        
        Args:
            session_id: User session ID
            task_id: Task ID to update
            subject: New task title/subject
            description: Updated task description (Markdown supported)
            due_date: Due date in YYYY-MM-DD format
            tags: Comma-separated tags (e.g., "frontend,urgent,bug")
            assigned_to: User ID to assign task to
            milestone_id: Milestone/sprint ID to assign task to
            status_id: Status ID for the task
            user_story_id: User story ID to link task to
            **kwargs: Additional fields (is_blocked, blocked_note, etc.)
        
        Returns:
            Dict containing the updated task details
        """
        log_operation("update", "task", session_id, f"ID {task_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        
        # Build update data from provided parameters
        update_data = {}
        
        if subject is not None:
            update_data["subject"] = subject
        if description is not None:
            update_data["description"] = description
        if due_date is not None:
            update_data["due_date"] = due_date
        if tags is not None:
            # Convert comma-separated tags to list
            update_data["tags"] = [tag.strip() for tag in tags.split(',') if tag.strip()]
        if assigned_to is not None:
            update_data["assigned_to"] = assigned_to
        if milestone_id is not None:
            update_data["milestone"] = milestone_id
        if status_id is not None:
            update_data["status"] = status_id
        if user_story_id is not None:
            update_data["user_story"] = user_story_id
            
        # Add any additional kwargs
        update_data.update(kwargs)
        
        try:
            if not update_data:
                 logger.info(f"No fields provided for update on task {task_id}")
                 return taiga_client_wrapper.api.tasks.get(task_id)

            # Get current task data to retrieve version
            current_task = taiga_client_wrapper.api.tasks.get(task_id)
            version = current_task.get('version')
            if not version:
                raise ValueError(f"Could not determine version for task {task_id}")
                
            # Use edit method for partial updates with data dictionary
            updated_task = taiga_client_wrapper.api.tasks.edit(
                task_id=task_id,
                version=version,
                data=update_data
            )
            logger.info(f"Task {task_id} update request sent.")
            return updated_task
        except TaigaException as e:
            handle_taiga_exception("updating", "task", task_id, e)
        except Exception as e:
            handle_general_exception("updating", "task", task_id, e)

    @mcp.tool("delete_task", description="Deletes a task by its ID.")
    def delete_task(session_id: str, task_id: int) -> Dict[str, Any]:
        """Deletes a task by ID."""
        logger.warning(
            f"Executing delete_task ID {task_id} for session {session_id[:8]}...")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            taiga_client_wrapper.api.tasks.delete(task_id)
            log_success("deleted", "task", task_id)
            return {"status": "deleted", "task_id": task_id}
        except TaigaException as e:
            handle_taiga_exception("deleting", "task", task_id, e)
        except Exception as e:
            handle_general_exception("deleting", "task", task_id, e)

    @mcp.tool("assign_task_to_user", description="Assigns a specific task to a specific user.")
    def assign_task_to_user(session_id: str, task_id: int, user_id: int) -> Dict[str, Any]:
        """Assigns a task to a user."""
        log_operation("assign", "task_to_user", session_id, f"Task {task_id} -> User {user_id}")
        # Delegate to update_task
        return update_task(session_id, task_id, assigned_to=user_id)

    @mcp.tool("unassign_task_from_user", description="Unassigns a specific task (sets assigned user to null).")
    def unassign_task_from_user(session_id: str, task_id: int) -> Dict[str, Any]:
        """Unassigns a task."""
        log_operation("unassign", "task_from_user", session_id, f"Task {task_id}")
        # Delegate to update_task
        return update_task(session_id, task_id, assigned_to=None)
    
    @mcp.tool("search_users", description="Search for users by name or email within a project.")
    def search_users(session_id: str, project_id: int, query: str) -> List[Dict[str, Any]]:
        """
        Search for users by name or email within a project context.
        
        Args:
            session_id: User session ID
            project_id: Project ID to search within
            query: Search query (name, username, or email)
        
        Returns:
            List of matching users with their details
        """
        log_operation("search", "users", session_id, f"query '{query}' in project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # First get project members as the most relevant users
            members = taiga_client_wrapper.api.memberships.list(query_params={"project": project_id})
            
            # Filter members by the search query
            matching_users = []
            query_lower = query.lower()
            
            for member in members:
                user = member.get('user', {})
                full_name = user.get('full_name', '').lower()
                username = user.get('username', '').lower()
                email = user.get('email', '').lower()
                
                if (query_lower in full_name or 
                    query_lower in username or 
                    query_lower in email):
                    matching_users.append({
                        'id': user.get('id'),
                        'username': user.get('username'),
                        'full_name': user.get('full_name'),
                        'email': user.get('email'),
                        'role': member.get('role_name'),
                        'is_active': user.get('is_active', False)
                    })
            
            logger.info(f"Found {len(matching_users)} users matching '{query}'")
            return matching_users
        except TaigaException as e:
            handle_taiga_exception("searching", "users", query, e)
        except Exception as e:
            handle_general_exception("searching", "users", query, e)
    
    @mcp.tool("assign_task_by_username", description="Assigns a task to a user by their username or name.")
    def assign_task_by_username(session_id: str, task_id: int, project_id: int, username: str) -> Dict[str, Any]:
        """
        Assigns a task to a user by searching for them by username or name.
        
        Args:
            session_id: User session ID
            task_id: Task ID to assign
            project_id: Project ID where the task exists
            username: Username, full name, or email to search for
        
        Returns:
            Dict containing the updated task with assignment details
        """
        log_operation("assign", "task_by_username", session_id, f"Task {task_id} -> {username}")
        
        try:
            # Search for the user
            users = search_users(session_id, project_id, username)
            
            if not users:
                raise ValueError(f"No user found matching '{username}' in project {project_id}")
            
            if len(users) > 1:
                # Return multiple matches for user to choose from
                return {
                    "status": "multiple_matches",
                    "message": f"Multiple users found matching '{username}'. Please specify:",
                    "users": users,
                    "suggestion": "Use assign_task_to_user with specific user ID"
                }
            
            # Single match found - assign the task
            user = users[0]
            result = update_task(session_id, task_id, assigned_to=user['id'])
            result['assigned_user'] = user
            logger.info(f"Task {task_id} assigned to {user['full_name']} (ID: {user['id']})")
            return result
            
        except ValueError as e:
            logger.error(f"User search error: {e}")
            raise e
        except Exception as e:
            handle_general_exception("assigning task by username", f"task {task_id}", e)

    @mcp.tool("get_task_activity", description="Gets activity timeline for a specific task.")
    def get_task_activity(session_id: str, task_id: int) -> List[Dict[str, Any]]:
        """
        Gets the activity timeline/history for a task.
        
        Args:
            session_id: User session ID
            task_id: Task ID to get activity for
            
        Returns:
            List of activity entries for the task
        """
        log_operation("get", "task_activity", session_id, f"for task {task_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Get user timeline and filter for this task
            timeline = taiga_client_wrapper.api.timeline.user_timeline()
            
            # Filter timeline entries related to this task
            task_activities = []
            for entry in timeline:
                if (entry.get('data', {}).get('task', {}).get('id') == task_id or 
                    entry.get('event_type', '').startswith('tasks.')):
                    task_activities.append({
                        'id': entry.get('id'),
                        'event_type': entry.get('event_type'),
                        'created': entry.get('created'),
                        'data': entry.get('data', {}),
                        'user': entry.get('user', {}),
                        'description': entry.get('data', {}).get('comment', '')
                    })
            
            logger.info(f"Found {len(task_activities)} activity entries for task {task_id}")
            return task_activities
        except TaigaException as e:
            handle_taiga_exception("getting", "task activity", task_id, e)
        except Exception as e:
            handle_general_exception("getting", "task activity", task_id, e)
            
    @mcp.tool("add_task_tags", description="Adds tags to an existing task.")
    def add_task_tags(session_id: str, task_id: int, new_tags: str) -> Dict[str, Any]:
        """
        Adds new tags to an existing task without removing existing ones.
        
        Args:
            session_id: User session ID
            task_id: Task ID to add tags to
            new_tags: Comma-separated tags to add (e.g., "urgent,frontend,bug")
        
        Returns:
            Dict containing the updated task with new tags
        """
        log_operation("add", "task_tags", session_id, f"'{new_tags}' to task {task_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        
        try:
            # Get current task to merge tags
            current_task = taiga_client_wrapper.api.tasks.get(task_id)
            current_tags = current_task.get('tags', [])
            
            # Parse new tags
            new_tag_list = [tag.strip() for tag in new_tags.split(',') if tag.strip()]
            
            # Merge with existing tags (avoid duplicates)
            all_tags = list(set(current_tags + new_tag_list))
            
            # Update the task with merged tags
            result = update_task(session_id, task_id, tags=','.join(all_tags))
            logger.info(f"Added tags {new_tag_list} to task {task_id}. Total tags: {len(all_tags)}")
            return result
            
        except TaigaException as e:
            handle_taiga_exception("adding", "task tags", task_id, e)
        except Exception as e:
            handle_general_exception("adding", "task tags", task_id, e)
