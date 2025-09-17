# server.py
"""
Main server file for Taiga MCP Bridge.

This file sets up the FastMCP server and registers all tools from the modular tool modules.
"""

import logging
import logging.config
from mcp.server.fastmcp import FastMCP

# Import tool registration functions
from tools.auth import register_auth_tools
from tools.project import register_project_tools  
from tools.story import register_story_tools
from tools.task import register_task_tools
from tools.issue import register_issue_tools
from tools.epic import register_epic_tools
from tools.milestone import register_milestone_tools
from tools.user import register_user_tools
from tools.wiki import register_wiki_tools

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Log to stderr by default
    ]
)
logger = logging.getLogger(__name__)
# Quiet down pytaigaclient library logging if needed
logging.getLogger("pytaigaclient").setLevel(logging.WARNING)

# --- MCP Server Definition ---
mcp = FastMCP(
    "Taiga Bridge (Session ID)",
    dependencies=["pytaigaclient"]
)

# --- Register All Tools ---
def register_all_tools():
    """Register all tool modules with the FastMCP instance."""
    logger.info("Registering authentication tools...")
    register_auth_tools(mcp)
    
    logger.info("Registering project management tools...")
    register_project_tools(mcp)
    
    logger.info("Registering user story tools...")
    register_story_tools(mcp)
    
    logger.info("Registering task management tools...")
    register_task_tools(mcp)
    
    logger.info("Registering issue management tools...")
    register_issue_tools(mcp)
    
    logger.info("Registering epic management tools...")
    register_epic_tools(mcp)
    
    logger.info("Registering milestone/sprint tools...")
    register_milestone_tools(mcp)
    
    logger.info("Registering user management tools...")
    register_user_tools(mcp)
    
    logger.info("Registering wiki page tools...")
    register_wiki_tools(mcp)
    
    logger.info("All tool modules registered successfully.")

# Register all tools when the module is imported
register_all_tools()

# Export the FastMCP instance for use by the MCP server
__all__ = ["mcp"]
