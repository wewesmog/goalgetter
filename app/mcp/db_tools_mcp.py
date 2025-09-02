# MCP server for database tools
from mcp.server.fastmcp import FastMCP
from typing import Optional, List, Dict, Any
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import DatabaseError
from app.shared_services.db import get_db
from app.shared_services.logger_setup import setup_logger
from app.mcp.mcp_tools_helpers import get_goals, update_goals, insert_goal

logger = setup_logger()



mcp = FastMCP("goalgetter-db")

@mcp.tool()
async def update_goal_tool(user_id: str,
                         goal_id: str,
                         updates: Dict[str, str]) -> Dict[str, Any]:
    """
    Update multiple properties of a single goal. This tool enforces safe updates of goals.
    
    IMPORTANT RULES:
    1. You MUST provide both user_id and goal_id - updates are only allowed one goal at a time
    2. NEVER attempt to delete goals - instead, set status to 'cancelled' and update end_date
    3. You can update multiple properties at once using the updates dictionary
    4. For dates, use YYYY-MM-DD format (e.g., '2024-03-26')
       Note: Current date will be provided to you by the client
    
    Examples:
    1. To cancel a goal:
       updates = {
           'goal_status': 'cancelled',
           'goal_end_date': '2024-03-26'  # Use the current date provided by client
       }
    
    2. To update goal end date:
       updates = {
           'goal_end_date': '2024-12-31'  # Specific future date
       }
    
    2. To update priority and status:
       updates = {
           'goal_priority': 'high',
           'goal_status': 'in_progress'
       }
    
    3. To update name and future end date:
       updates = {
           'goal_name': 'New goal name',
           'goal_end_date': '2024-12-31'
       }

Parameters:
    - user_id: str (Required) - The user's ID who owns the goal
    - goal_id: str (Required) - The specific goal to update
    - updates: Dict[str, str] (Required) - Dictionary of updates to make. Keys must be from:
        * 'goal_name' - Any string
        * 'goal_status' - One of: 'in_progress', 'completed', 'cancelled'
        * 'goal_priority' - One of: 'high', 'medium', 'low'
        * 'goal_end_date' - Date in format: 'YYYY-MM-DD'
    
    Returns:
    - Dictionary containing:
        * success: bool - Whether update was successful
        * message: str - Description of what happened
        * updated_goal_id: str - ID of the updated goal
    
    Raises:
    - ValueError: If parameters are invalid or if trying to perform disallowed operations
    - DatabaseError: If database operation fails
    """
    try:
        result = await update_goals(
            user_id=user_id,
            goal_id=goal_id,
            updates=updates
        )
        
        return {
            "success": result,
            "message": f"Successfully updated goal {goal_id}" if result else f"No goal found with ID {goal_id}",
            "updated_goal_id": goal_id if result else None
        }
        
    except ValueError as ve:
        error_response = {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure both user_id and goal_id are provided",
                "Check if column_to_update is one of: goal_name, goal_status, goal_priority, goal_end_date",
                "For status updates, use: in_progress, completed, cancelled",
                "For priority updates, use: high, medium, low",
                "For date updates, use format: YYYY-MM-DD",
                "To delete/stop a goal, update status to 'cancelled' and set end_date"
            ]
        }
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": "Failed to update goal",
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=error_response)

@mcp.tool()
async def insert_goal_tool(user_id: str,
                         title: str,
                         description: str,
                         status: str = 'in_progress',
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new goal in the database.

    IMPORTANT RULES:
    1. You MUST provide user_id, title, and description
    2. Status must be one of: 'in_progress', 'completed', 'cancelled'
    3. Dates must be in YYYY-MM-DD format
    4. If start_date not provided, current date will be used
    
    Examples:
    1. Create a basic goal:
       {
           'user_id': '123',
           'title': 'Learn Python',
           'description': 'Master Python programming language'
       }
    
    2. Create goal with all fields:
       {
           'user_id': '123',
           'title': 'Complete Project',
           'description': 'Finish the web application',
           'status': 'in_progress',
           'start_date': '2024-03-26',
           'end_date': '2024-12-31'
       }

    Parameters:
    - user_id: str (Required) - The user's ID who owns the goal
    - title: str (Required) - Goal title
    - description: str (Required) - Goal description
    - status: str (Optional) - One of: 'in_progress', 'completed', 'cancelled'
    - start_date: str (Optional) - Start date in YYYY-MM-DD format
    - end_date: str (Optional) - End date in YYYY-MM-DD format

    Returns:
    - Dictionary containing:
        * success: bool - Whether creation was successful
        * goal_id: str - ID of the newly created goal
        * message: str - Success or error message
    """
    try:
        # Convert string dates to datetime if provided
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        goal_id = await insert_goal(
            user_id=user_id,
            title=title,
            description=description,
            status=status,
            start_date=start,
            end_date=end
        )
        
        return {
            "success": True,
            "goal_id": goal_id,
            "message": f"Successfully created goal {goal_id}"
        }
        
    except ValueError as ve:
        error_response = {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure user_id, title, and description are provided",
                "Check if status is one of: in_progress, completed, cancelled",
                "Ensure dates are in YYYY-MM-DD format"
            ]
        }
        raise HTTPException(status_code=400, detail=error_response)
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": "Failed to create goal",
            "error": str(e)
        }
        raise HTTPException(status_code=500, detail=error_response)

@mcp.tool()
async def get_goals_tool(user_id: str,
                        goal_id: Optional[str] = None,
                        goal_name: Optional[str] = None,
                        goal_status: Optional[str] = None,
                        goal_priority: Optional[str] = None,
                        goal_start_date: Optional[str] = None,
                        goal_end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve goals from the database based on various search criteria.

    Use this tool when you need to:
    1. Get all goals for a specific user
    2. Find a specific goal by ID
    3. Search goals by name, status, or priority
    4. Filter goals by date range

    Examples:
    - Get all goals: provide only user_id
    - Find specific goal: provide user_id and goal_id
    - Search by status: provide user_id and goal_status (e.g., "in_progress", "completed")
    - Date range search: provide goal_start_date and/or goal_end_date (format: YYYY-MM-DD)

Parameters:
    - user_id: str (Required) - The ID of the user whose goals to retrieve
    - goal_id: str (Optional) - Specific goal ID to find
    - goal_name: str (Optional) - Search by goal name
    - goal_status: str (Optional) - Filter by status (in_progress, completed, cancelled)
    - goal_priority: str (Optional) - Filter by priority (high, medium, low)
    - goal_start_date: str (Optional) - Filter goals starting from this date (YYYY-MM-DD)
    - goal_end_date: str (Optional) - Filter goals up to this date (YYYY-MM-DD)

    Returns:
    - List[Dict[str, Any]] - List of goals matching the criteria
      Each goal contains: id, name, status, priority, start_date, end_date, description

    Raises:
    - ValueError: If user_id is empty or if date format is invalid
    - DatabaseError: If database connection or query fails
    - Exception: For unexpected errors
    """
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
            
        # Date format validation if provided
        if goal_start_date:
            try:
                datetime.strptime(goal_start_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("goal_start_date must be in YYYY-MM-DD format")
                
        if goal_end_date:
            try:
                datetime.strptime(goal_end_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError("goal_end_date must be in YYYY-MM-DD format")
                
        # Status validation
        if goal_status and goal_status not in ["in_progress", "completed", "cancelled"]:
            raise ValueError("Invalid goal_status. Must be one of: in_progress, completed, cancelled")
            
        # Priority validation
        if goal_priority and goal_priority not in ["high", "medium", "low"]:
            raise ValueError("Invalid goal_priority. Must be one of: high, medium, low")
            
        return await get_goals(
            user_id=user_id,
            goal_id=goal_id,
            goal_name=goal_name,
            goal_status=goal_status,
            goal_priority=goal_priority,
            goal_start_date=goal_start_date,
            goal_end_date=goal_end_date
        )
    except ValueError as ve:
        error_response = {
            "error_type": "validation_error",
            "message": str(ve),
            "suggestions": [
                "Check if the provided dates are in YYYY-MM-DD format",
                "Ensure goal_status is one of: in_progress, completed, cancelled",
                "Ensure goal_priority is one of: high, medium, low"
            ],
            "valid_values": {
                "goal_status": ["in_progress", "completed", "cancelled"],
                "goal_priority": ["high", "medium", "low"],
                "date_format": "YYYY-MM-DD"
            }
        }
        logger.error(f"Validation error in get_goals_tool: {str(ve)}")
        raise HTTPException(status_code=400, detail=error_response)
    except DatabaseError as de:
        error_response = {
            "error_type": "database_error",
            "message": "Failed to retrieve goals from database",
            "details": str(de),
            "suggestions": [
                "Check if the goals table exists",
                "Verify database connection settings",
                "Ensure all required columns are present"
            ],
            "query_context": {
                "user_id": user_id,
                "filters_used": [k for k, v in locals().items() if k in ['goal_id', 'goal_name', 'goal_status', 'goal_priority'] and v is not None]
            }
        }
        logger.error(f"Database error in get_goals_tool: {str(de)}")
        raise HTTPException(status_code=500, detail=error_response)
    except Exception as e:
        error_response = {
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving goals",
            "details": str(e),
            "suggestions": [
                "Try the operation again",
                "Check if all required services are running",
                "Verify input parameters"
            ],
            "request_context": {
                "endpoint": "get_goals_tool",
                "parameters_provided": [k for k, v in locals().items() if k in ['user_id', 'goal_id', 'goal_name', 'goal_status', 'goal_priority', 'goal_start_date', 'goal_end_date'] and v is not None]
            }
        }
        logger.error(f"Unexpected error in get_goals_tool: {str(e)}")
        raise HTTPException(status_code=500, detail=error_response)
    

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')



