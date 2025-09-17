# wiki.py
"""
Wiki page management tools for Taiga MCP bridge.
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


def register_wiki_tools(mcp: FastMCP) -> None:
    """Register wiki page management tools with the FastMCP instance."""

    @mcp.tool("list_wiki_pages", description="Lists wiki pages within a specific project.")
    def list_wiki_pages(session_id: str, project_id: int) -> List[Dict[str, Any]]:
        """Lists wiki pages for a project."""
        log_operation("list", "wiki_pages", session_id, f"for project {project_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            # Fix: Use query_params dictionary for wiki list
            query_params = {"project": project_id}
            pages = taiga_client_wrapper.api.wiki.list(query_params=query_params)
            return pages
        except TaigaException as e:
            handle_taiga_exception("listing", "wiki pages", f"project {project_id}", e)
        except Exception as e:
            handle_general_exception("listing", "wiki pages", f"project {project_id}", e)

    @mcp.tool("get_wiki_page", description="Gets a specific wiki page by its ID.")
    def get_wiki_page(session_id: str, wiki_page_id: int) -> Dict[str, Any]:
        """Retrieves wiki page details by ID."""
        log_operation("get", "wiki_page", session_id, f"ID {wiki_page_id}")
        taiga_client_wrapper = get_authenticated_client(session_id)
        try:
            page = taiga_client_wrapper.api.wiki.get(wiki_page_id)
            return page
        except TaigaException as e:
            handle_taiga_exception("getting", "wiki page", wiki_page_id, e)
        except Exception as e:
            handle_general_exception("getting", "wiki page", wiki_page_id, e)
