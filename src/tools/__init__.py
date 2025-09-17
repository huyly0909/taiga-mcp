"""
Taiga MCP Tools Package

This package contains modular tool implementations for the Taiga MCP bridge,
organized by functionality for better maintainability.
"""

from .auth import *
from .project import *
from .story import *
from .task import *
from .issue import *
from .epic import *
from .milestone import *
from .user import *
from .wiki import *

__all__ = [
    # Auth tools
    "ping",
    "login",
    "logout", 
    "session_status",
    
    # Project tools
    "list_projects",
    "list_all_projects", 
    "get_project",
    "get_project_by_slug",
    "create_project",
    "update_project",
    "delete_project",
    
    # User Story tools
    "list_user_stories",
    "create_user_story",
    "get_user_story", 
    "update_user_story",
    "delete_user_story",
    "assign_user_story_to_user",
    "unassign_user_story_from_user",
    "get_user_story_statuses",
    
    # Task tools
    "list_tasks",
    "create_task",
    "get_task",
    "update_task", 
    "delete_task",
    "assign_task_to_user",
    "unassign_task_from_user",
    "search_users",
    "assign_task_by_username",
    "get_task_activity",
    "add_task_tags",
    
    # Issue tools
    "list_issues",
    "create_issue",
    "get_issue",
    "update_issue",
    "delete_issue", 
    "assign_issue_to_user",
    "unassign_issue_from_user",
    "get_issue_statuses",
    "get_issue_priorities",
    "get_issue_severities", 
    "get_issue_types",
    
    # Epic tools
    "list_epics",
    "create_epic",
    "get_epic",
    "update_epic",
    "delete_epic",
    "assign_epic_to_user",
    "unassign_epic_from_user",
    
    # Milestone tools
    "list_milestones",
    "create_milestone",
    "get_milestone",
    "update_milestone",
    "delete_milestone",
    
    # User management tools  
    "get_project_members",
    "invite_project_user",
    
    # Wiki tools
    "list_wiki_pages",
    "get_wiki_page"
]
