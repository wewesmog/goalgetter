# MCP server for database tools
from mcp.server.fastmcp import FastMCP
from typing import Optional, List, Dict, Any
# from fastapi import Depends, HTTPException
# from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import DatabaseError
from app.shared_services.db import get_postgres_connection
from app.shared_services.logger_setup import setup_logger
from app.mcp.mcp_tools_helpers import get_goals, update_goals, insert_goal, get_habits, update_habits, insert_habit, get_milestones, update_milestones, insert_milestone, get_progress_logs, update_progress_log, insert_progress_log

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
    2. NEVER attempt to delete goals - instead, set status to 'cancelled' and update target_date
    3. You can update multiple properties at once using the updates dictionary
    4. For dates, use YYYY-MM-DD format (e.g., '2024-03-26')
    
    AVAILABLE COLUMNS TO UPDATE:
    - 'title' - Goal title (any string)
    - 'description' - Goal description (any string)  
    - 'status' - One of: 'in_progress', 'completed', 'cancelled'
    - 'start_date' - Start date in YYYY-MM-DD format
    - 'target_date' - Target completion date in YYYY-MM-DD format
    
    Examples:
    1. To cancel a goal:
       updates = {
           'status': 'cancelled',
           'target_date': '2024-03-26'
       }
    
    2. To update goal target date:
       updates = {
           'target_date': '2024-12-31'
       }
    
    3. To update title and status:
       updates = {
           'title': 'New goal title',
           'status': 'in_progress'
       }
    
    4. To update description and target date:
       updates = {
           'description': 'Updated goal description',
           'target_date': '2024-12-31'
       }

Parameters:
    - user_id: str (Required) - The user's ID who owns the goal
    - goal_id: str (Required) - The specific goal to update
    - updates: Dict[str, str] (Required) - Dictionary of updates to make
    
    Returns:
    - Dictionary containing:
        * success: bool - Whether update was successful
        * message: str - Description of what happened
        * updated_goal_id: str - ID of the updated goal
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
                "Check if column_to_update is one of: title, description, status, start_date, target_date",
                "For status updates, use: in_progress, completed, cancelled",
                "For date updates, use format: YYYY-MM-DD",
                "To cancel a goal, update status to 'cancelled' and set target_date"
            ]
        }
        return error_response
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": "Failed to update goal",
            "error": str(e)
        }
        return error_response

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
    - end_date: str (Optional) - Target completion date in YYYY-MM-DD format

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
        return error_response
        
    except Exception as e:
        error_response = {
            "success": False,
            "message": "Failed to create goal",
            "error": str(e)
        }
        return error_response

@mcp.tool()
async def get_goals_tool(user_id: str,
                        goal_id: Optional[str] = None,
                        title: Optional[str] = None,
                        status: Optional[str] = None,
                        start_date_begin: Optional[str] = None,
                        start_date_end: Optional[str] = None,
                        target_date_begin: Optional[str] = None,
                        target_date_end: Optional[str] = None) -> Any:
    """
    Retrieve goals from the database based on various search criteria.

    Use this tool when you need to:
    1. Get all goals for a specific user
    2. Find a specific goal by ID
    3. Search goals by title, status
    4. Filter goals by date range

    Examples:
    - Get all goals: provide only user_id
    - Find specific goal: provide user_id and goal_id
    - Search by status: provide user_id and status (e.g."cancelled", "in_progress", "completed")
    - "This year" goals: use start_date_begin="2024-01-01" + start_date_end="2024-12-31" (goals started during 2024)
    - "This month" goals: use start_date_begin="2024-01-01" + start_date_end="2024-01-31" (goals started during January)
    - "Show me my goals": provide only user_id (NO date filters needed)
    - "Goals ending this month": use target_date_begin="2024-01-01" + target_date_end="2024-01-31" (goals ending during January)
    - "Overdue goals": use target_date_begin="2024-01-01" + target_date_end="2024-01-15" (goals past deadline)


Parameters:
    - user_id: str (Required) - The ID of the user whose goals to retrieve
    - goal_id: str (Optional) - Specific goal ID to find
    - title: str (Optional) - Search by goal title
    - status: str (Optional) - Filter by status (in_progress, completed, cancelled)
    - start_date_begin: str (Optional) - Filter goals that started on or after this date (YYYY-MM-DD)
    - start_date_end: str (Optional) - Filter goals that started on or before this date (YYYY-MM-DD)
    - target_date_begin: str (Optional) - Filter goals that end on or after this date (YYYY-MM-DD)
    - target_date_end: str (Optional) - Filter goals that end on or before this date (YYYY-MM-DD)
    
    DATE RANGE LOGIC:
    - Use start_date_begin + start_date_end for start date ranges
    - Use target_date_begin + target_date_end for target date ranges
    - "This year" → start_date_begin="2024-01-01" + start_date_end="2024-12-31"
    - "This month" → start_date_begin="2024-01-01" + start_date_end="2024-01-31"

    Returns:
    - List[Dict[str, Any]] - List of goals matching the criteria (on success)
      Each goal contains: goal_id, user_id, title, description, status, start_date, target_date, created_at, last_updated
    - Dict[str, Any] - Error object (on failure)
      Contains: success=False, error_type, message, details, suggestions

    Note:
    - Returns a list of goals on successful query
    - Returns an error dictionary if validation fails or database error occurs
    """
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
            
        # Date format validation if provided
        if start_date_begin:
            try:
                datetime.strptime(start_date_begin, "%Y-%m-%d")
            except ValueError:
                raise ValueError("start_date_begin must be in YYYY-MM-DD format")
                
        if start_date_end:
            try:
                datetime.strptime(start_date_end, "%Y-%m-%d")
            except ValueError:
                raise ValueError("start_date_end must be in YYYY-MM-DD format")
                
        if target_date_begin:
            try:
                datetime.strptime(target_date_begin, "%Y-%m-%d")
            except ValueError:
                raise ValueError("target_date_begin must be in YYYY-MM-DD format")
                
        if target_date_end:
            try:
                datetime.strptime(target_date_end, "%Y-%m-%d")
            except ValueError:
                raise ValueError("target_date_end must be in YYYY-MM-DD format")
                
        # Status validation
        if status and status not in ["in_progress", "completed", "cancelled"]:
            raise ValueError("Invalid status. Must be one of: in_progress, completed, cancelled")
            
            
            
        return await get_goals(
            user_id=user_id,
            goal_id=goal_id,
            title=title,
            status=status,
            start_date_begin=start_date_begin,
            start_date_end=start_date_end,
            target_date_begin=target_date_begin,
            target_date_end=target_date_end
        )
    except ValueError as ve:
        error_response = {
            "error_type": "validation_error",
            "message": str(ve),
            "suggestions": [
                "Check if the provided dates are in YYYY-MM-DD format",
                "Ensure status is one of: in_progress, completed, cancelled"
            ],
            "valid_values": {
                "status": ["in_progress", "completed", "cancelled"],
                "date_format": "YYYY-MM-DD"
            }
        }
        logger.error(f"Validation error in get_goals_tool: {str(ve)}")
        return error_response
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
                "filters_used": [k for k, v in locals().items() if k in ['goal_id', 'title', 'status', 'start_date', 'target_date'] and v is not None]
            }
        }
        logger.error(f"Database error in get_goals_tool: {str(de)}")
        return error_response
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
                "parameters_provided": [k for k, v in locals().items() if k in ['user_id', 'goal_id', 'title', 'status', 'start_date', 'target_date'] and v is not None]
            }
        }
        logger.error(f"Unexpected error in get_goals_tool: {str(e)}")
        return error_response


# ========== HABIT TOOLS ==========

@mcp.tool()
async def insert_habit_tool(user_id: str,
                           title: str,
                           description: str,
                           status: str = 'in_progress',
                           start_date: Optional[str] = None,
                           target_date: Optional[str] = None,
                           frequency_type: str = 'day',
                           frequency_value: int = 1) -> Dict[str, Any]:
    """
    Create a new habit in the database.

    IMPORTANT RULES:
    1. You MUST provide user_id, title, and description
    2. Status must be one of: 'in_progress', 'completed', 'cancelled'
    3. Dates must be in YYYY-MM-DD format
    4. If start_date not provided, current date will be used
    5. Frequency type must be one of: 'day', 'week', 'month', 'year'
    6. Frequency value must be a positive integer

    Examples:
    1. Create a basic habit:
       {
           'user_id': '123',
           'title': 'Exercise Daily',
           'description': 'Do 30 minutes of exercise every day'
       }

    2. Create habit with all fields:
       {
           'user_id': '123',
           'title': 'Read Books',
           'description': 'Read for 1 hour every day',
           'status': 'in_progress',
           'start_date': '2024-03-26',
           'target_date': '2024-12-31',
           'frequency_type': 'day',
           'frequency_value': 1
       }

    Parameters:
    - user_id: str (Required) - The user's ID who owns the habit
    - title: str (Required) - Habit title
    - description: str (Required) - Habit description
    - status: str (Optional) - One of: 'in_progress', 'completed', 'cancelled'
    - start_date: str (Optional) - Start date in YYYY-MM-DD format
    - target_date: str (Optional) - Target completion date in YYYY-MM-DD format
    - frequency_type: str (Optional) - One of: 'day', 'week', 'month', 'year'
    - frequency_value: int (Optional) - Frequency value (positive integer)

    Returns:
    - Dictionary containing:
        * success: bool - Whether creation was successful
        * habit_id: str - ID of the newly created habit
        * message: str - Success or error message
    """
    try:
        # Basic validation at tool level
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not title or not title.strip():
            raise ValueError("title is required")
        if not description or not description.strip():
            raise ValueError("description is required")
        if status not in ['in_progress', 'completed', 'cancelled']:
            raise ValueError("status must be one of: in_progress, completed, cancelled")
        if frequency_type not in ['day', 'week', 'month', 'year']:
            raise ValueError("frequency_type must be one of: day, week, month, year")
        if frequency_value < 1:
            raise ValueError("frequency_value must be a positive integer")

        # Convert string dates to datetime if provided
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else datetime.now()
        target = datetime.strptime(target_date, "%Y-%m-%d") if target_date else None

        habit_id = await insert_habit(
            user_id=user_id,
            title=title,
            description=description,
            status=status,
            start_date=start,
            target_date=target,
            frequency_type=frequency_type,
            frequency_value=frequency_value
        )

        return {
            "success": True,
            "habit_id": habit_id,
            "message": f"Successfully created habit {habit_id}"
        }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure user_id, title, and description are provided",
                "Check if status is one of: in_progress, completed, cancelled",
                "Ensure dates are in YYYY-MM-DD format",
                "Check frequency_type is one of: day, week, month, year",
                "Ensure frequency_value is a positive integer"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create habit",
            "error": str(e)
        }


@mcp.tool()
async def get_habits_tool(user_id: str,
                         habit_id: Optional[str] = None,
                         title: Optional[str] = None,
                         status: Optional[str] = None,
                         start_date_begin: Optional[str] = None,
                         start_date_end: Optional[str] = None,
                         target_date_begin: Optional[str] = None,
                         target_date_end: Optional[str] = None,
                         frequency_type: Optional[str] = None) -> Any:
    """
    Retrieve habits from the database based on various search criteria.

    Use this tool when you need to:
    1. Get all habits for a specific user
    2. Find a specific habit by ID
    3. Search habits by title, status, frequency
    4. Filter habits by date range

    Examples:
    - Get all habits: provide only user_id
    - Find specific habit: provide user_id and habit_id
    - Search by status: provide user_id and status (e.g."cancelled", "in_progress", "completed")
    - "This year" habits: use start_date_begin="2024-01-01" + start_date_end="2024-12-31" (habits started during 2024)
    - "This month" habits: use start_date_begin="2024-01-01" + start_date_end="2024-01-31" (habits started during January)
    - "Show me my habits": provide only user_id (NO date filters needed)
    - "Daily habits": use frequency_type="day"

    SMART SEARCHING STRATEGY:
    - When user mentions a habit by description (e.g., "cancel my habit about exercise"), FIRST get all habits with user_id only
    - Then look through the results to find the habit that matches the description
    - Use fuzzy matching - "exercise" should match "Exercise Daily"
    - Don't use exact title search unless user provides the exact title

    IMPORTANT DATE CONTEXT:
    - Current year is 2024
    - When user says "this year", use 2024 dates
    - When user says "this month", use current month dates
    - Always use YYYY-MM-DD format for dates

    Parameters:
    - user_id: str (Required) - The ID of the user whose habits to retrieve
    - habit_id: str (Optional) - Specific habit ID to find
    - title: str (Optional) - Search by habit title
    - status: str (Optional) - Filter by status (in_progress, completed, cancelled)
    - start_date_begin: str (Optional) - Filter habits that started on or after this date (YYYY-MM-DD)
    - start_date_end: str (Optional) - Filter habits that started on or before this date (YYYY-MM-DD)
    - target_date_begin: str (Optional) - Filter habits that end on or after this date (YYYY-MM-DD)
    - target_date_end: str (Optional) - Filter habits that end on or before this date (YYYY-MM-DD)
    - frequency_type: str (Optional) - Filter by frequency type (day, week, month, year)

    DATE RANGE LOGIC:
    - Use start_date_begin + start_date_end for start date ranges
    - Use target_date_begin + target_date_end for target date ranges
    - "This year" → start_date_begin="2024-01-01" + start_date_end="2024-12-31"
    - "This month" → start_date_begin="2024-01-01" + start_date_end="2024-01-31"

    Returns:
    - List[Dict[str, Any]] - List of habits matching the criteria (on success)
      Each habit contains: habit_id, user_id, title, description, status, start_date, target_date, frequency_type, frequency_value, created_at, last_updated
    - Dict[str, Any] - Error object (on failure)
      Contains: success=False, error_type, message, details, suggestions
    """
    try:
        # Basic validation at tool level
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        # Date format validation if provided
        for date_param, date_value in [
            ("start_date_begin", start_date_begin),
            ("start_date_end", start_date_end),
            ("target_date_begin", target_date_begin),
            ("target_date_end", target_date_end)
        ]:
            if date_value:
                try:
                    datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{date_param} must be in YYYY-MM-DD format")

        # Status validation
        if status and status not in ["in_progress", "completed", "cancelled"]:
            raise ValueError("Invalid status. Must be one of: in_progress, completed, cancelled")

        # Frequency type validation
        if frequency_type and frequency_type not in ["day", "week", "month", "year"]:
            raise ValueError("Invalid frequency_type. Must be one of: day, week, month, year")

        return await get_habits(
            user_id=user_id,
            habit_id=habit_id,
            title=title,
            status=status,
            start_date_begin=start_date_begin,
            start_date_end=start_date_end,
            target_date_begin=target_date_begin,
            target_date_end=target_date_end,
            frequency_type=frequency_type
        )

    except ValueError as ve:
        error_response = {
            "error_type": "validation_error",
            "message": str(ve),
            "suggestions": [
                "Check if the provided dates are in YYYY-MM-DD format",
                "Ensure status is one of: in_progress, completed, cancelled",
                "Ensure frequency_type is one of: day, week, month, year"
            ],
            "valid_values": {
                "status": ["in_progress", "completed", "cancelled"],
                "frequency_type": ["day", "week", "month", "year"],
                "date_format": "YYYY-MM-DD"
            }
        }
        logger.error(f"Validation error in get_habits_tool: {str(ve)}")
        return error_response

    except Exception as e:
        error_response = {
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving habits",
            "details": str(e),
            "suggestions": [
                "Try the operation again",
                "Check if all required services are running",
                "Verify input parameters"
            ]
        }
        logger.error(f"Unexpected error in get_habits_tool: {str(e)}")
        return error_response


@mcp.tool()
async def update_habit_tool(user_id: str,
                           habit_id: str,
                           updates: Dict[str, str]) -> Dict[str, Any]:
    """
    Update multiple properties of a single habit. This tool enforces safe updates of habits.

    IMPORTANT RULES:
    1. You MUST provide both user_id and habit_id - updates are only allowed one habit at a time
    2. NEVER attempt to delete habits - instead, set status to 'cancelled' and update target_date
    3. You can update multiple properties at once using the updates dictionary
    4. For dates, use YYYY-MM-DD format (e.g., '2024-03-26')

    AVAILABLE COLUMNS TO UPDATE:
    - 'title' - Habit title (any string)
    - 'description' - Habit description (any string)
    - 'status' - One of: 'in_progress', 'completed', 'cancelled'
    - 'start_date' - Start date in YYYY-MM-DD format
    - 'target_date' - Target completion date in YYYY-MM-DD format
    - 'frequency_type' - One of: 'day', 'week', 'month', 'year'
    - 'frequency_value' - Positive integer for frequency

    Examples:
    1. To cancel a habit:
       updates = {
           'status': 'cancelled',
           'target_date': '2024-03-26'
       }

    2. To update habit frequency:
       updates = {
           'frequency_type': 'week',
           'frequency_value': '3'
       }

    3. To update title and status:
       updates = {
           'title': 'New habit title',
           'status': 'completed'
       }

    Parameters:
    - user_id: str (Required) - The user's ID who owns the habit
    - habit_id: str (Required) - The specific habit to update
    - updates: Dict[str, str] (Required) - Dictionary of updates to make

    Returns:
    - Dictionary containing:
        * success: bool - Whether update was successful
        * message: str - Description of what happened
        * updated_habit_id: str - ID of the updated habit
    """
    try:
        # Basic validation at tool level
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not habit_id or not habit_id.strip():
            raise ValueError("habit_id is required")
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")

        # Validate update keys and values
        allowed_columns = ['title', 'description', 'status', 'start_date', 'target_date', 'frequency_type', 'frequency_value']
        for column, value in updates.items():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")

            # Validate specific fields
            if column == 'status' and value not in ['in_progress', 'completed', 'cancelled']:
                raise ValueError("status must be one of: in_progress, completed, cancelled")
            if column == 'frequency_type' and value not in ['day', 'week', 'month', 'year']:
                raise ValueError("frequency_type must be one of: day, week, month, year")
            if column == 'frequency_value':
                try:
                    freq_val = int(value)
                    if freq_val < 1:
                        raise ValueError("frequency_value must be a positive integer")
                except ValueError:
                    raise ValueError("frequency_value must be a positive integer")
            if column in ['start_date', 'target_date']:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{column} must be in YYYY-MM-DD format")

        result = await update_habits(
            user_id=user_id,
            habit_id=habit_id,
            updates=updates
        )

        if isinstance(result, dict) and result.get("success"):
            return result
        else:
            return {
                "success": False,
                "message": f"Failed to update habit {habit_id}",
                "details": str(result)
            }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure both user_id and habit_id are provided",
                "Check if updates dictionary contains valid columns",
                "For status updates, use: in_progress, completed, cancelled",
                "For date updates, use format: YYYY-MM-DD",
                "For frequency_type, use: day, week, month, year",
                "For frequency_value, use positive integers"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to update habit",
            "error": str(e)
        }


# ========== MILESTONE TOOLS ==========

@mcp.tool()
async def insert_milestone_tool(goal_id: str,
                               description: str,
                               user_id: str,
                               status: str = 'pending',
                               target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new milestone within a specific goal.

    IMPORTANT RULES:
    1. You MUST provide goal_id, description, and user_id
    2. Milestones are sub-tasks/checkpoints within a goal
    3. Status must be one of: 'pending', 'in_progress', 'completed'
    4. Dates must be in YYYY-MM-DD format
    5. If target_date not provided, milestone has no deadline

    Examples:
    1. Create a basic milestone:
       {
           'goal_id': '5',
           'description': 'Complete research phase',
           'user_id': '123'
       }

    2. Create milestone with deadline:
       {
           'goal_id': '5',
           'description': 'Finish prototype',
           'user_id': '123',
           'status': 'in_progress',
           'target_date': '2024-12-31'
       }

    Parameters:
    - goal_id: str (Required) - The goal this milestone belongs to
    - description: str (Required) - Milestone description
    - user_id: str (Required) - The user who owns this milestone
    - status: str (Optional) - One of: 'pending', 'in_progress', 'completed'
    - target_date: str (Optional) - Target completion date in YYYY-MM-DD format

    Returns:
    - Dictionary containing:
        * success: bool - Whether creation was successful
        * milestone_id: str - ID of the newly created milestone
        * message: str - Success or error message
    """
    try:
        # Basic validation at tool level
        if not goal_id or not str(goal_id).strip():
            raise ValueError("goal_id is required")
        if not description or not description.strip():
            raise ValueError("description is required")
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if status not in ['pending', 'in_progress', 'completed']:
            raise ValueError("status must be one of: pending, in_progress, completed")

        # Convert string date to datetime if provided
        target = datetime.strptime(target_date, "%Y-%m-%d") if target_date else None

        milestone_id = await insert_milestone(
            goal_id=goal_id,
            description=description,
            user_id=user_id,
            status=status,
            target_date=target
        )

        return {
            "success": True,
            "milestone_id": milestone_id,
            "message": f"Successfully created milestone {milestone_id} for goal {goal_id}"
        }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure goal_id, description, and user_id are provided",
                "Check if status is one of: pending, in_progress, completed",
                "Ensure target_date is in YYYY-MM-DD format"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create milestone",
            "error": str(e)
        }


@mcp.tool()
async def get_milestones_tool(goal_id: Optional[str] = None,
                             milestone_id: Optional[str] = None,
                             description: Optional[str] = None,
                             status: Optional[str] = None,
                             target_date_begin: Optional[str] = None,
                             target_date_end: Optional[str] = None) -> Any:
    """
    Retrieve milestones from the database based on various search criteria.

    Use this tool when you need to:
    1. Get all milestones for a specific goal
    2. Find a specific milestone by ID
    3. Search milestones by description or status
    4. Filter milestones by due date range
    5. Get overdue milestones

    Examples:
    - Get all milestones for a goal: provide goal_id only
    - Find specific milestone: provide milestone_id
    - Search by description: provide description (e.g. "research", "prototype")
    - Get pending milestones: provide status="pending"
    - Get overdue milestones: provide target_date_end="2024-09-14" (past date)
    - Get milestones due this week: provide target_date_begin="2024-09-14" + target_date_end="2024-09-21"

    SMART SEARCHING STRATEGY:
    - When user mentions a milestone by description (e.g., "complete my research milestone"), FIRST get all milestones for the goal
    - Then look through the results to find the milestone that matches the description
    - Use fuzzy matching - "research" should match "Complete research phase"
    - Milestones are always linked to goals, so goal context is important

    IMPORTANT DATE CONTEXT:
    - Current year is 2024
    - When user says "this week", use current week dates
    - When user says "overdue", use target_date_end with past date
    - Always use YYYY-MM-DD format for dates

    Parameters:
    - goal_id: str (Optional) - Get milestones for a specific goal
    - milestone_id: str (Optional) - Specific milestone ID to find
    - description: str (Optional) - Search by milestone description
    - status: str (Optional) - Filter by status (pending, in_progress, completed)
    - target_date_begin: str (Optional) - Filter milestones due on or after this date (YYYY-MM-DD)
    - target_date_end: str (Optional) - Filter milestones due on or before this date (YYYY-MM-DD)

    DATE RANGE LOGIC:
    - Use target_date_begin + target_date_end for due date ranges
    - "This week" → target_date_begin="2024-09-14" + target_date_end="2024-09-21"
    - "Overdue" → target_date_end="2024-09-13" (yesterday)

    Returns:
    - List[Dict[str, Any]] - List of milestones matching the criteria (on success)
      Each milestone contains: milestone_id, goal_id, description, status, target_date, completed_at, created_at, last_updated, goal_title, user_id
    - Dict[str, Any] - Error object (on failure)
      Contains: success=False, error_type, message, details, suggestions
    """
    try:
        # Date format validation if provided
        for date_param, date_value in [
            ("target_date_begin", target_date_begin),
            ("target_date_end", target_date_end)
        ]:
            if date_value:
                try:
                    datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{date_param} must be in YYYY-MM-DD format")

        # Status validation
        if status and status not in ["pending", "in_progress", "completed"]:
            raise ValueError("Invalid status. Must be one of: pending, in_progress, completed")

        return await get_milestones(
            goal_id=goal_id,
            milestone_id=milestone_id,
            description=description,
            status=status,
            target_date_begin=target_date_begin,
            target_date_end=target_date_end
        )

    except ValueError as ve:
        error_response = {
            "error_type": "validation_error",
            "message": str(ve),
            "suggestions": [
                "Check if the provided dates are in YYYY-MM-DD format",
                "Ensure status is one of: pending, in_progress, completed"
            ],
            "valid_values": {
                "status": ["pending", "in_progress", "completed"],
                "date_format": "YYYY-MM-DD"
            }
        }
        logger.error(f"Validation error in get_milestones_tool: {str(ve)}")
        return error_response

    except Exception as e:
        error_response = {
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving milestones",
            "details": str(e),
            "suggestions": [
                "Try the operation again",
                "Check if all required services are running",
                "Verify input parameters"
            ]
        }
        logger.error(f"Unexpected error in get_milestones_tool: {str(e)}")
        return error_response


@mcp.tool()
async def update_milestone_tool(milestone_id: str,
                               updates: Dict[str, str]) -> Dict[str, Any]:
    """
    Update multiple properties of a single milestone. This tool enforces safe updates of milestones.

    IMPORTANT RULES:
    1. You MUST provide milestone_id - updates are only allowed one milestone at a time
    2. NEVER attempt to delete milestones - instead, set status to 'completed' or ask user to contact support
    3. You can update multiple properties at once using the updates dictionary
    4. For dates, use YYYY-MM-DD format (e.g., '2024-03-26')
    5. Status 'completed' automatically sets completed_at timestamp

    AVAILABLE COLUMNS TO UPDATE:
    - 'description' - Milestone description (any string)
    - 'status' - One of: 'pending', 'in_progress', 'completed'
    - 'target_date' - Target completion date in YYYY-MM-DD format
    - 'completed_at' - Completion timestamp (automatically set when status becomes 'completed')

    Examples:
    1. To complete a milestone:
       updates = {
           'status': 'completed'
       }

    2. To update description and extend deadline:
       updates = {
           'description': 'Updated milestone description',
           'target_date': '2024-12-31'
       }

    3. To start working on a milestone:
       updates = {
           'status': 'in_progress'
       }

    Parameters:
    - milestone_id: str (Required) - The specific milestone to update
    - updates: Dict[str, str] (Required) - Dictionary of updates to make

    Returns:
    - Dictionary containing:
        * success: bool - Whether update was successful
        * message: str - Description of what happened
        * updated_milestone_id: str - ID of the updated milestone
    """
    try:
        # Basic validation at tool level
        if not milestone_id or not str(milestone_id).strip():
            raise ValueError("milestone_id is required")
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")

        # Validate update keys and values
        allowed_columns = ['description', 'status', 'target_date', 'completed_at']
        for column, value in updates.items():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")

            # Validate specific fields
            if column == 'status' and value not in ['pending', 'in_progress', 'completed']:
                raise ValueError("status must be one of: pending, in_progress, completed")
            if column == 'target_date':
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError("target_date must be in YYYY-MM-DD format")

        result = await update_milestones(
            milestone_id=milestone_id,
            updates=updates
        )

        if isinstance(result, dict) and result.get("success"):
            return result
        else:
            return {
                "success": False,
                "message": f"Failed to update milestone {milestone_id}",
                "details": str(result)
            }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure milestone_id is provided",
                "Check if updates dictionary contains valid columns",
                "For status updates, use: pending, in_progress, completed",
                "For date updates, use format: YYYY-MM-DD"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to update milestone",
            "error": str(e)
        }


# ========== PROGRESS LOG TOOLS ==========

@mcp.tool()
async def insert_progress_log_tool(user_id: str,
                                  content: str,
                                  log_type: str,
                                  related_goal_id: Optional[str] = None,
                                  related_habit_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a new progress log for tracking goal or habit progress.

    IMPORTANT RULES:
    1. You MUST provide user_id, content, and log_type
    2. Progress logs can be linked to goals, habits, or both
    3. log_type should describe the nature of the progress entry
    4. Content should be descriptive and useful for tracking progress

    COMMON LOG TYPES:
    - daily_progress: Regular daily updates
    - milestone_reached: When achieving milestones  
    - challenge_faced: When encountering obstacles
    - breakthrough: Major progress moments
    - reflection: Weekly/monthly reflections
    - habit_completion: When completing habit instances
    - goal_update: Updates on goal progress
    - other: For custom log types

    Examples:
    1. Daily goal progress:
       {
           'user_id': '123',
           'content': 'Completed 3 Python tutorials today, learned about dictionaries',
           'log_type': 'daily_progress',
           'related_goal_id': '5'
       }

    2. Habit completion:
       {
           'user_id': '123',
           'content': 'Exercised for 30 minutes - jogging in the park',
           'log_type': 'habit_completion',
           'related_habit_id': '2'
       }

    3. Milestone achievement:
       {
           'user_id': '123',
           'content': 'Successfully built my first Python web app!',
           'log_type': 'milestone_reached',
           'related_goal_id': '5'
       }

    Parameters:
    - user_id: str (Required) - The user creating this progress log
    - content: str (Required) - Progress description/content
    - log_type: str (Required) - Type of progress log
    - related_goal_id: str (Optional) - Goal this progress relates to
    - related_habit_id: str (Optional) - Habit this progress relates to

    Returns:
    - Dictionary containing:
        * success: bool - Whether creation was successful
        * log_id: str - ID of the newly created progress log
        * message: str - Success or error message
    """
    try:
        # Basic validation at tool level
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not content or not content.strip():
            raise ValueError("content is required")
        if not log_type or not log_type.strip():
            raise ValueError("log_type is required")

        log_id = await insert_progress_log(
            user_id=user_id,
            content=content,
            log_type=log_type,
            related_goal_id=related_goal_id,
            related_habit_id=related_habit_id
        )

        return {
            "success": True,
            "log_id": log_id,
            "message": f"Successfully created progress log {log_id}"
        }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure user_id, content, and log_type are provided",
                "Consider linking to a goal or habit for better tracking",
                "Use descriptive content that captures your progress"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to create progress log",
            "error": str(e)
        }


@mcp.tool()
async def get_progress_logs_tool(user_id: str,
                                log_id: Optional[str] = None,
                                related_goal_id: Optional[str] = None,
                                related_habit_id: Optional[str] = None,
                                log_type: Optional[str] = None,
                                content_search: Optional[str] = None,
                                date_begin: Optional[str] = None,
                                date_end: Optional[str] = None) -> Any:
    """
    Retrieve progress logs from the database based on various search criteria.

    Use this tool when you need to:
    1. Get all progress logs for a specific user
    2. View progress for a specific goal or habit
    3. Search progress logs by content or type
    4. Filter progress logs by date range
    5. Find specific progress entries

    Examples:
    - Get all user progress: provide user_id only
    - Get progress for specific goal: provide user_id and related_goal_id
    - Get daily progress entries: provide user_id and log_type="daily_progress"
    - Search progress content: provide user_id and content_search="python"
    - Get recent progress: provide user_id and date_begin="2024-09-01"
    - Get milestones achieved: provide user_id and log_type="milestone_reached"

    SEARCH STRATEGIES:
    - Use content_search to find logs containing specific words
    - Use log_type to filter by progress type
    - Use date ranges to get progress from specific time periods
    - Combine filters for more specific searches

    IMPORTANT DATE CONTEXT:
    - Current year is 2024
    - When user says "this week", use current week dates
    - When user says "recent", use date_begin with past week
    - Always use YYYY-MM-DD format for dates

    Parameters:
    - user_id: str (Required) - The user whose progress logs to retrieve
    - log_id: str (Optional) - Specific progress log ID to find
    - related_goal_id: str (Optional) - Get progress for a specific goal
    - related_habit_id: str (Optional) - Get progress for a specific habit
    - log_type: str (Optional) - Filter by progress type
    - content_search: str (Optional) - Search within progress content
    - date_begin: str (Optional) - Filter logs created on or after this date (YYYY-MM-DD)
    - date_end: str (Optional) - Filter logs created on or before this date (YYYY-MM-DD)

    Returns:
    - List[Dict[str, Any]] - List of progress logs matching the criteria (on success)
      Each log contains: log_id, user_id, content, log_type, related_goal_id, related_habit_id, created_at, last_updated, goal_title, habit_title
    - Dict[str, Any] - Error object (on failure)
      Contains: success=False, error_type, message, details, suggestions
    """
    try:
        # Basic validation at tool level
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")

        # Date format validation if provided
        for date_param, date_value in [
            ("date_begin", date_begin),
            ("date_end", date_end)
        ]:
            if date_value:
                try:
                    datetime.strptime(date_value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{date_param} must be in YYYY-MM-DD format")

        return await get_progress_logs(
            user_id=user_id,
            log_id=log_id,
            related_goal_id=related_goal_id,
            related_habit_id=related_habit_id,
            log_type=log_type,
            content_search=content_search,
            date_begin=date_begin,
            date_end=date_end
        )

    except ValueError as ve:
        error_response = {
            "error_type": "validation_error",
            "message": str(ve),
            "suggestions": [
                "Check if the provided dates are in YYYY-MM-DD format",
                "Ensure user_id is provided",
                "Verify search parameters are valid"
            ],
            "valid_values": {
                "date_format": "YYYY-MM-DD",
                "common_log_types": ["daily_progress", "milestone_reached", "challenge_faced", "breakthrough", "reflection", "habit_completion", "goal_update"]
            }
        }
        logger.error(f"Validation error in get_progress_logs_tool: {str(ve)}")
        return error_response

    except Exception as e:
        error_response = {
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving progress logs",
            "details": str(e),
            "suggestions": [
                "Try the operation again",
                "Check if all required services are running",
                "Verify input parameters"
            ]
        }
        logger.error(f"Unexpected error in get_progress_logs_tool: {str(e)}")
        return error_response


@mcp.tool()
async def update_progress_log_tool(log_id: str,
                                  updates: Dict[str, str]) -> Dict[str, Any]:
    """
    Update properties of a single progress log. This tool enforces safe updates of progress logs.

    IMPORTANT RULES:
    1. You MUST provide log_id - updates are only allowed one progress log at a time
    2. NEVER attempt to delete progress logs - they are valuable historical data
    3. You can update content, log_type, and relationships
    4. Be careful when changing relationships as it affects progress tracking

    AVAILABLE COLUMNS TO UPDATE:
    - 'content' - Progress log content (any string)
    - 'log_type' - Type of progress log (string)
    - 'related_goal_id' - Goal this progress relates to (string, can be set to null)
    - 'related_habit_id' - Habit this progress relates to (string, can be set to null)

    Examples:
    1. To update progress content:
       updates = {
           'content': 'Updated: Completed 5 Python tutorials today, learned about classes and objects'
       }

    2. To change progress type:
       updates = {
           'log_type': 'breakthrough',
           'content': 'Major breakthrough: Finally understood object-oriented programming!'
       }

    3. To link/unlink from goal:
       updates = {
           'related_goal_id': '7'  # or None to unlink
       }

    Parameters:
    - log_id: str (Required) - The specific progress log to update
    - updates: Dict[str, str] (Required) - Dictionary of updates to make

    Returns:
    - Dictionary containing:
        * success: bool - Whether update was successful
        * message: str - Description of what happened
        * updated_log_id: str - ID of the updated progress log
    """
    try:
        # Basic validation at tool level
        if not log_id or not str(log_id).strip():
            raise ValueError("log_id is required")
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")

        # Validate update keys
        allowed_columns = ['content', 'log_type', 'related_goal_id', 'related_habit_id']
        for column in updates.keys():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")

        result = await update_progress_log(
            log_id=log_id,
            updates=updates
        )

        if isinstance(result, dict) and result.get("success"):
            return result
        else:
            return {
                "success": False,
                "message": f"Failed to update progress log {log_id}",
                "details": str(result)
            }

    except ValueError as ve:
        return {
            "success": False,
            "message": str(ve),
            "suggestions": [
                "Ensure log_id is provided",
                "Check if updates dictionary contains valid columns",
                "Verify update values are appropriate",
                "Use null or empty string to remove relationships"
            ]
        }

    except Exception as e:
        return {
            "success": False,
            "message": "Failed to update progress log",
            "error": str(e)
        }

    
# Function to run the server
def run_server():
    mcp.run(transport='stdio')

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')



