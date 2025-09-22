# Database helper functions
from typing import Optional, List, Dict, Any
# from fastapi import Depends
# from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio
import psycopg2
from psycopg2 import DatabaseError
from app.shared_services.db import get_postgres_connection
from app.shared_services.logger_setup import setup_logger

logger = setup_logger()



async def get_goals(user_id: str,
              goal_id: str = None, 
              title: str = None, 
              status: str = None,  
              start_date_begin: str = None,
              start_date_end: str = None,
              target_date_begin: str = None,
              target_date_end: str = None,
              limit: int = 10,
              offset: int = 0):
    """
    Get goals from the database based on filters.

    Args:
        user_id: str - Required. The user's ID
        goal_id: str - Optional. Specific goal ID to find
        title: str - Optional. Search by goal title
        status: str - Optional. Filter by status (in_progress, completed, cancelled)
        start_date: str - Optional. Filter by start date (YYYY-MM-DD)
        target_date: str - Optional. Filter by end date (YYYY-MM-DD)
        limit: int - Optional. Max number of goals to return (default: 10)
        offset: int - Optional. Number of goals to skip (default: 0)

    Returns:
        List of goals, each containing:
        - goal_id: str - Unique identifier
        - user_id: str - Owner's ID
        - title: str - Goal title
        - description: str - Goal description
        - status: str - Current status (in_progress, completed, cancelled)
        - start_date: str - Start date (YYYY-MM-DD)
        - target_date: str - End date (YYYY-MM-DD)

    Raises:
        DatabaseError: When database operations fail
        Exception: For unexpected errors
    """
    try:
        conditions = []
        params = []
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        if goal_id:
            conditions.append("goal_id = %s")
            params.append(goal_id)
        if title:
            conditions.append("title = %s")
            params.append(title)
        if status:
            conditions.append("status = %s")
            params.append(status)
        if start_date_begin:
            conditions.append("start_date >= %s")
            params.append(start_date_begin)
        if start_date_end:
            conditions.append("start_date <= %s")
            params.append(start_date_end)
        if target_date_begin:
            conditions.append("target_date >= %s")
            params.append(target_date_begin)
        if target_date_end:
            conditions.append("target_date <= %s")
            params.append(target_date_end)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        query = f"""
            SELECT * FROM goals 
            WHERE {where_clause}
            ORDER BY start_date ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                goals = cursor.fetchall()
            if not goals:
                logger.info(f"No goals found for query parameters: {params}")
                return "No goals found matching the criteria."
            return goals
        finally:
            conn.close()
                
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in get_goals: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        # Return error object instead of raising exception
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to retrieve goals from database",
            "details": f"Database operation failed: {str(pe)}",
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
            
    except Exception as e:
        logger.error(f"Unexpected error in get_goals: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        # Return error object instead of raising exception
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving goals",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }

#Helper Functions for the tools
async def update_goals(user_id: str,
                    goal_id: str,
                    updates: Dict[str, str]):
    """
    Update multiple columns for a specific goal.

    Args:
        user_id: str - Required. The user's ID
        goal_id: str - Required. The specific goal ID to update
        updates: Dict[str, str] - Dictionary of column names and their new values.
            Available columns:
            - goal_id: str - Goal's unique identifier
            - title: str - Goal title
            - description: str - Goal description
            - status: str - One of: 'in_progress', 'completed', 'cancelled'
            - start_date: str - Start date in YYYY-MM-DD format
            - target_date: str - End date in YYYY-MM-DD format
        db: Session - Database session

    Returns:
        bool: True if update successful, False if goal not found

    Raises:
        ValueError: If required fields missing or invalid values provided
        DatabaseError: When database operations fail
        Exception: For unexpected errors
    """
    # Validate column name to prevent SQL injection
    ALLOWED_COLUMNS = {
        'goal_id': str,
        'title': str,
        'description': str,
        'status': ['in_progress', 'completed', 'cancelled'],
        'start_date': 'date',
        'target_date': 'date',
    }
    
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not goal_id or not goal_id.strip():
            raise ValueError("goal_id is required")

        # Validate and build SET clause
        set_clauses = []
        params = []  # Will contain [update_values..., user_id, goal_id]
        
        for column, value in updates.items():
            if column not in ALLOWED_COLUMNS:
                raise ValueError(f"Cannot update column: {column}. Allowed columns: {list(ALLOWED_COLUMNS.keys())}")
            
            if column == 'status' and value not in ALLOWED_COLUMNS['status']:
                raise ValueError(f"Invalid status. Must be one of: {ALLOWED_COLUMNS['status']}")
            
            if column in ['start_date', 'target_date']:
                try:
                    datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"{column} must be in YYYY-MM-DD format")
            
            set_clauses.append(f"{column} = %s")
            params.append(value)
        
        # Add WHERE clause parameters
        params.extend([user_id, goal_id])
        
        # Build safe parameterized query
        set_clause = ", ".join(set_clauses)
        query = f"""
            UPDATE goals 
            SET {set_clause}
            WHERE user_id = %s             -- Second-to-last parameter: user_id
            AND goal_id = %s               -- Last parameter: goal_id
            RETURNING goal_id
        """
        
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                updated_rows = cursor.fetchall()
                if not updated_rows:
                    logger.info(f"No goals found to update for user_id: {user_id}, goal_id: {goal_id}")
                    return False
                # Commit the transaction
                conn.commit()
                logger.info(f"Successfully updated {len(updated_rows)} goals")
                return True
        except psycopg2.Error as pe:
            # Rollback on error
            conn.rollback()
            logger.error(f"PostgreSQL error in update_goals: {str(pe)}")
            logger.error(f"Failed query: {query}")
            logger.error(f"Query parameters: {params}")
            return {
                "success": False,
                "error_type": "database_error",
                "message": "Failed to update goal in database",
                "details": f"Database operation failed: {str(pe)}",
                "suggestions": [
                    "Check if the goal exists",
                    "Verify the goal_id is correct",
                    "Ensure database connection is working"
                ]
            }
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error in update_goals: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error", 
            "message": "An unexpected error occurred while updating goal",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def insert_goal(user_id: str,
                   title: str,
                   description: str,
                   status: str = 'in_progress',
                   start_date: datetime = datetime.now(),
                   end_date: datetime = None):
    """
    Insert a new goal into the database.

    Args:
        user_id: str - Required. The user's ID
        title: str - Required. Goal title
        description: str - Required. Goal description
        status: str - Optional. Goal status (default: 'in_progress')
            Must be one of: 'in_progress', 'completed', 'cancelled'
        start_date: datetime - Optional. Start date (default: current date)
        end_date: datetime - Optional. End date
        db: Session - Database session

    Returns:
        str: goal_id - The unique identifier of the newly created goal

    Database Columns Created:
        - goal_id: str - Automatically generated unique identifier
        - user_id: str - Owner's ID (from args)
        - title: str - Goal title (from args)
        - description: str - Goal description (from args)
        - status: str - Goal status (from args or default)
        - start_date: datetime - Start date (from args or default)
        - end_date: datetime - End date (from args)

    Raises:
        ValueError: If required fields missing or invalid values provided
        DatabaseError: When database operations fail
        Exception: For unexpected errors
    """
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not title or not title.strip():
            raise ValueError("title is required")
        if not description or not description.strip():
            raise ValueError("description is required")
        
        # Status validation
        valid_statuses = ['in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        # Build query
        query = """
            INSERT INTO goals (user_id, title, description, status, start_date, target_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING goal_id
        """
        params = [user_id, title, description, status, start_date, end_date]
        
        # Execute query
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                response = cursor.fetchone()
            if not response:
                raise DatabaseError("Failed to create goal - no ID returned")
            goal_id = response[0]
            # Commit the transaction
            conn.commit()
            logger.info(f"Successfully created goal {goal_id} for user {user_id}")
            return goal_id
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            conn.close()
                
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in insert_goal: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to create goal in database",
            "details": f"Database operation failed: {str(pe)}",
            "suggestions": [
                "Check if the goals table exists",
                "Verify database connection settings",
                "Ensure all required fields are provided"
            ]
        }
            
    except Exception as e:
        logger.error(f"Unexpected error in insert_goal: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while creating goal",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }



# =========HABITS=========

async def insert_habit(user_id: str,
                   title: str,
                   description: str,
                   status: str = 'in_progress',
                   start_date: datetime = datetime.now(),
                   target_date: datetime = None,
                   frequency_type: str = 'day',
                   frequency_value: int = 1):
    """
    Insert a new habit into the database.
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
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

  
        
        # Build query
        query = """
            INSERT INTO habits (user_id, title, description, status, start_date, target_date, frequency_type, frequency_value)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING habit_id
        """
        params = [user_id, title, description, status, start_date, target_date, frequency_type, frequency_value]
        
        # Execute query
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                response = cursor.fetchone()
                if not response:
                    raise DatabaseError("Failed to create habit - no ID returned")
                habit_id = response[0]
                # Commit the transaction
                conn.commit()
                logger.info(f"Successfully created habit {habit_id} for user {user_id}")
                return habit_id
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in insert_habit: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to create habit in database",
            "details": f"Database operation failed: {str(pe)}",
            "suggestions": [
                "Check if the habits table exists",
                "Verify database connection settings",
                "Ensure all required fields are provided"
            ]
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in insert_habit: {str(ve)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "validation_error", 
            "message": "Invalid data provided for habit creation",
            "details": str(ve),
            "suggestions": [
                "Check if all required fields are provided",
                "Verify data types and formats"
            ]
        }
            
    except Exception as e:
        logger.error(f"Unexpected error in insert_habit: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while creating habit",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def get_habits(user_id: str,
                    habit_id: str = None, 
                    title: str = None, 
                    status: str = None,  
                    start_date_begin: str = None,
                    start_date_end: str = None,
                    target_date_begin: str = None,
                    target_date_end: str = None,
                    frequency_type: str = None,
                    limit: int = 10,
                    offset: int = 0):
    """
    Retrieve habits from the database based on search criteria.
    
    Args:
        user_id: The user's ID (required)
        habit_id: Specific habit ID to find (optional)
        title: Search by habit title (optional)
        status: Filter by status (optional)
        start_date_begin: Filter habits starting on or after this date (optional)
        start_date_end: Filter habits starting on or before this date (optional)
        target_date_begin: Filter habits ending on or after this date (optional)
        target_date_end: Filter habits ending on or before this date (optional)
        frequency_type: Filter by frequency type (optional)
        limit: Maximum number of results (default 10)
        offset: Number of results to skip (default 0)
    
    Returns:
        List of habits or error message
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not user_id or not user_id.strip():
            return "No habits found matching the criteria."
            
        # Build base query
        query = """
            SELECT habit_id, user_id, title, description, status, start_date, target_date, 
                   frequency_type, frequency_value, created_at, last_updated
            FROM habits 
            WHERE user_id = %s
        """
        params = [user_id]
        conditions = []
        
        # Add optional filters
        if habit_id:
            conditions.append("habit_id = %s")
            params.append(habit_id)
            
        if title:
            conditions.append("title ILIKE %s")
            params.append(f"%{title}%")
            
        if status:
            conditions.append("status = %s")
            params.append(status)
            
        if start_date_begin:
            conditions.append("start_date >= %s")
            params.append(start_date_begin)
            
        if start_date_end:
            conditions.append("start_date <= %s")
            params.append(start_date_end)
            
        if target_date_begin:
            conditions.append("target_date >= %s")
            params.append(target_date_begin)
            
        if target_date_end:
            conditions.append("target_date <= %s")
            params.append(target_date_end)
            
        if frequency_type:
            conditions.append("frequency_type = %s")
            params.append(frequency_type)
        
        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        # Add ordering and pagination
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute query
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            cursor.close()
            conn.close()
            return "No habits found matching the criteria."
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        habits = []
        for row in rows:
            habit = dict(zip(columns, row))
            # Convert datetime objects to strings for JSON serialization
            for key, value in habit.items():
                if isinstance(value, datetime):
                    habit[key] = value.isoformat()
            habits.append(habit)
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(habits)} habits for user {user_id}")
        return habits
        
    except DatabaseError as de:
        logger.error(f"Database error in get_habits: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to retrieve habits from database",
            "details": str(de),
            "user_id": user_id,
            "filters_used": []
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in get_habits: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid parameters provided",
            "details": str(ve),
            "suggestions": [
                "Check if user_id is provided",
                "Verify date formats (YYYY-MM-DD)",
                "Ensure status values are valid"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_habits: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving habits",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def update_habits(user_id: str, habit_id: str, updates: Dict[str, Any]):
    """
    Update multiple properties of a single habit. This function enforces safe updates.
    
    Args:
        user_id: The user's ID who owns the habit (required)
        habit_id: The specific habit to update (required) 
        updates: Dictionary of updates to make (required)
        
    Available columns to update:
        - title: Habit title (string)
        - description: Habit description (string)
        - status: One of 'in_progress', 'completed', 'cancelled'
        - start_date: Start date in YYYY-MM-DD format
        - target_date: Target completion date in YYYY-MM-DD format
        - frequency_type: One of 'day', 'week', 'month', 'year'
        - frequency_value: Integer value for frequency
        
    Returns:
        Dictionary with success status and details
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
            
        if not habit_id or not habit_id.strip():
            raise ValueError("habit_id is required")
            
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")
            
        # Define allowed columns and their validation
        allowed_columns = {
            'title': str,
            'description': str, 
            'status': str,
            'start_date': str,
            'target_date': str,
            'frequency_type': str,
            'frequency_value': int
        }
        
        # Validate updates
        validated_updates = {}
        for column, value in updates.items():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")
                
            # Validate status values
            if column == 'status' and value not in ['in_progress', 'completed', 'cancelled']:
                raise ValueError("status must be one of: in_progress, completed, cancelled")
                
            # Validate frequency_type values
            if column == 'frequency_type' and value not in ['day', 'week', 'month', 'year']:
                raise ValueError("frequency_type must be one of: day, week, month, year")
                
            # Validate frequency_value
            if column == 'frequency_value' and (not isinstance(value, int) or value < 1):
                raise ValueError("frequency_value must be a positive integer")
                
            validated_updates[column] = value
            
        if not validated_updates:
            raise ValueError("No valid updates provided")
            
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for column, value in validated_updates.items():
            set_clauses.append(f"{column} = %s")
            params.append(value)
            
        # Add last_updated timestamp
        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        
        # Add WHERE conditions
        params.extend([user_id, habit_id])
        
        query = f"""
            UPDATE habits 
            SET {', '.join(set_clauses)}
            WHERE user_id = %s AND habit_id = %s
            RETURNING habit_id, title, status, last_updated
        """
        
        logger.info(f"Executing update query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute update
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        updated_row = cursor.fetchone()
        if not updated_row:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error_type": "not_found",
                "message": f"No habit found with ID {habit_id} for user {user_id}",
                "user_id": user_id,
                "habit_id": habit_id
            }
            
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully updated habit {habit_id} for user {user_id}")
        
        return {
            "success": True,
            "message": f"Habit {habit_id} updated successfully",
            "updated_habit_id": str(updated_row[0]),
            "updated_fields": list(validated_updates.keys()),
            "updates_applied": validated_updates
        }
        
    except DatabaseError as de:
        logger.error(f"Database error in update_habits: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error", 
            "message": "Failed to update habit in database",
            "details": str(de),
            "user_id": user_id,
            "habit_id": habit_id,
            "suggestions": [
                "Check if the habit exists",
                "Verify database connection settings",
                "Ensure all field values are valid"
            ]
        }
        
    except ValueError as ve:
        logger.error(f"ValueError in update_habits: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid data provided for habit update",
            "details": str(ve),
            "suggestions": [
                "Check if all required fields are provided",
                "Verify data types and formats",
                "Ensure status values are valid"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in update_habits: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while updating habit",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments", 
                "Check if the service is running properly"
            ]
        }


# =========MILESTONES=========

async def insert_milestone(goal_id: str,
                          description: str,
                          user_id: str,
                          status: str = 'pending',
                          target_date: datetime = None):
    """
    Insert a new milestone into the database.
    
    Args:
        goal_id: str (Required) - The goal this milestone belongs to
        description: str (Required) - Milestone description  
        user_id: str (Required) - The user who owns this milestone
        status: str (Optional) - One of: 'pending', 'in_progress', 'completed'
        target_date: datetime (Optional) - Target completion date
        
    Returns:
        str: milestone_id - The unique identifier of the newly created milestone
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not goal_id or not str(goal_id).strip():
            raise ValueError("goal_id is required")
        if not description or not description.strip():
            raise ValueError("description is required")
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if status not in ['pending', 'in_progress', 'completed']:
            raise ValueError("status must be one of: pending, in_progress, completed")

        # Build query
        query = """
            INSERT INTO milestones (goal_id, description, user_id, status, target_date)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING milestone_id
        """
        params = [goal_id, description, user_id, status, target_date]
        
        # Execute query
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                response = cursor.fetchone()
                if not response:
                    raise DatabaseError("Failed to create milestone - no ID returned")
                milestone_id = response[0]
                # Commit the transaction
                conn.commit()
                logger.info(f"Successfully created milestone {milestone_id} for goal {goal_id}")
                return milestone_id
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in insert_milestone: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to create milestone in database",
            "details": f"Database operation failed: {str(pe)}",
            "suggestions": [
                "Check if the goal exists",
                "Verify database connection settings",
                "Ensure all required fields are provided"
            ]
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in insert_milestone: {str(ve)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "validation_error", 
            "message": "Invalid data provided for milestone creation",
            "details": str(ve),
            "suggestions": [
                "Check if goal_id, description, and user_id are provided",
                "Verify status is one of: pending, in_progress, completed"
            ]
        }
            
    except Exception as e:
        logger.error(f"Unexpected error in insert_milestone: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while creating milestone",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def get_milestones(goal_id: str = None,
                        milestone_id: str = None, 
                        description: str = None, 
                        status: str = None,  
                        target_date_begin: str = None,
                        target_date_end: str = None,
                        limit: int = 10,
                        offset: int = 0):
    """
    Retrieve milestones from the database based on search criteria.
    
    Args:
        goal_id: The goal ID to get milestones for (optional)
        milestone_id: Specific milestone ID to find (optional)
        description: Search by milestone description (optional)
        status: Filter by status (optional)
        target_date_begin: Filter milestones due on or after this date (optional)
        target_date_end: Filter milestones due on or before this date (optional)
        limit: Maximum number of results (default 10)
        offset: Number of results to skip (default 0)
    
    Returns:
        List of milestones or error message
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Build base query with goal information
        query = """
            SELECT m.milestone_id, m.goal_id, m.description, m.status, m.target_date, 
                   m.completed_at, m.created_at, m.last_updated,
                   g.title as goal_title, g.user_id
            FROM milestones m
            JOIN goals g ON m.goal_id = g.goal_id
            WHERE 1=1
        """
        params = []
        conditions = []
        
        # Add optional filters
        if goal_id:
            conditions.append("m.goal_id = %s")
            params.append(goal_id)
            
        if milestone_id:
            conditions.append("m.milestone_id = %s")
            params.append(milestone_id)
            
        if description:
            conditions.append("m.description ILIKE %s")
            params.append(f"%{description}%")
            
        if status:
            conditions.append("m.status = %s")
            params.append(status)
            
        if target_date_begin:
            conditions.append("m.target_date >= %s")
            params.append(target_date_begin)
            
        if target_date_end:
            conditions.append("m.target_date <= %s")
            params.append(target_date_end)
        
        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        # Add ordering and pagination
        query += " ORDER BY m.target_date ASC, m.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute query
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            cursor.close()
            conn.close()
            return "No milestones found matching the criteria."
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        milestones = []
        for row in rows:
            milestone = dict(zip(columns, row))
            # Convert datetime objects to strings for JSON serialization
            for key, value in milestone.items():
                if isinstance(value, datetime):
                    milestone[key] = value.isoformat()
            milestones.append(milestone)
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(milestones)} milestones")
        return milestones
        
    except DatabaseError as de:
        logger.error(f"Database error in get_milestones: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to retrieve milestones from database",
            "details": str(de),
            "filters_used": []
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in get_milestones: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid parameters provided",
            "details": str(ve),
            "suggestions": [
                "Verify date formats (YYYY-MM-DD)",
                "Ensure status values are valid"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_milestones: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving milestones",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def update_milestones(milestone_id: str, updates: Dict[str, Any]):
    """
    Update multiple properties of a single milestone. This function enforces safe updates.
    
    Args:
        milestone_id: The specific milestone to update (required) 
        updates: Dictionary of updates to make (required)
        
    Available columns to update:
        - description: Milestone description (string)
        - status: One of 'pending', 'in_progress', 'completed'
        - target_date: Target completion date in YYYY-MM-DD format
        - completed_at: Completion timestamp (automatically set when status becomes 'completed')
        
    Returns:
        Dictionary with success status and details
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not milestone_id or not str(milestone_id).strip():
            raise ValueError("milestone_id is required")
            
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")
            
        # Define allowed columns and their validation
        allowed_columns = {
            'description': str,
            'status': str,
            'target_date': str,
            'completed_at': str
        }
        
        # Validate updates
        validated_updates = {}
        for column, value in updates.items():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")
                
            # Validate status values
            if column == 'status' and value not in ['pending', 'in_progress', 'completed']:
                raise ValueError("status must be one of: pending, in_progress, completed")
                
            validated_updates[column] = value
            
        if not validated_updates:
            raise ValueError("No valid updates provided")
            
        # Auto-set completed_at when status becomes 'completed'
        if 'status' in validated_updates and validated_updates['status'] == 'completed':
            validated_updates['completed_at'] = datetime.now().isoformat()
            
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for column, value in validated_updates.items():
            set_clauses.append(f"{column} = %s")
            params.append(value)
            
        # Add last_updated timestamp
        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        
        # Add WHERE condition
        params.append(milestone_id)
        
        query = f"""
            UPDATE milestones 
            SET {', '.join(set_clauses)}
            WHERE milestone_id = %s
            RETURNING milestone_id, description, status, last_updated
        """
        
        logger.info(f"Executing update query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute update
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        updated_row = cursor.fetchone()
        if not updated_row:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error_type": "not_found",
                "message": f"No milestone found with ID {milestone_id}",
                "milestone_id": milestone_id
            }
            
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully updated milestone {milestone_id}")
        
        return {
            "success": True,
            "message": f"Milestone {milestone_id} updated successfully",
            "updated_milestone_id": str(updated_row[0]),
            "updated_fields": list(validated_updates.keys()),
            "updates_applied": validated_updates
        }
        
    except DatabaseError as de:
        logger.error(f"Database error in update_milestones: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error", 
            "message": "Failed to update milestone in database",
            "details": str(de),
            "milestone_id": milestone_id,
            "suggestions": [
                "Check if the milestone exists",
                "Verify database connection settings",
                "Ensure all field values are valid"
            ]
        }
        
    except ValueError as ve:
        logger.error(f"ValueError in update_milestones: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid data provided for milestone update",
            "details": str(ve),
            "suggestions": [
                "Check if milestone_id is provided",
                "Verify data types and formats",
                "Ensure status values are valid"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in update_milestones: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while updating milestone",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments", 
                "Check if the service is running properly"
            ]
        }


# =========PROGRESS LOGS=========

async def insert_progress_log(user_id: str,
                             content: str,
                             log_type: str,
                             related_goal_id: str = None,
                             related_habit_id: str = None):
    """
    Insert a new progress log into the database.
    
    Args:
        user_id: str (Required) - The user creating this progress log
        content: str (Required) - Progress description/content
        log_type: str (Required) - Type of progress log (e.g., daily_progress, milestone_reached, challenge_faced, breakthrough, reflection)
        related_goal_id: str (Optional) - Goal this progress relates to
        related_habit_id: str (Optional) - Habit this progress relates to
        
    Returns:
        str: log_id - The unique identifier of the newly created progress log
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required")
        if not content or not content.strip():
            raise ValueError("content is required")
        if not log_type or not log_type.strip():
            raise ValueError("log_type is required")
        
        # Validate log_type values (common ones)
        valid_log_types = ['daily_progress', 'milestone_reached', 'challenge_faced', 'breakthrough', 'reflection', 'habit_completion', 'goal_update', 'other']
        if log_type not in valid_log_types:
            # Allow other log types but log a warning
            logger.warning(f"Uncommon log_type used: {log_type}. Consider using: {valid_log_types}")

        # At least one relationship should be specified for better tracking
        if not related_goal_id and not related_habit_id:
            logger.warning("Progress log created without goal or habit relationship")

        # Build query
        query = """
            INSERT INTO progress_logs (user_id, content, log_type, related_goal_id, related_habit_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING log_id
        """
        params = [user_id, content, log_type, related_goal_id, related_habit_id]
        
        # Execute query
        conn = get_postgres_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                response = cursor.fetchone()
                if not response:
                    raise DatabaseError("Failed to create progress log - no ID returned")
                log_id = response[0]
                # Commit the transaction
                conn.commit()
                logger.info(f"Successfully created progress log {log_id} for user {user_id}")
                return log_id
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in insert_progress_log: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to create progress log in database",
            "details": f"Database operation failed: {str(pe)}",
            "suggestions": [
                "Check if the goal/habit exists (if specified)",
                "Verify database connection settings",
                "Ensure all required fields are provided"
            ]
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in insert_progress_log: {str(ve)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "validation_error", 
            "message": "Invalid data provided for progress log creation",
            "details": str(ve),
            "suggestions": [
                "Check if user_id, content, and log_type are provided",
                "Verify log_type is appropriate",
                "Consider linking to a goal or habit for better tracking"
            ]
        }
            
    except Exception as e:
        logger.error(f"Unexpected error in insert_progress_log: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while creating progress log",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def get_progress_logs(user_id: str = None,
                           log_id: str = None,
                           related_goal_id: str = None,
                           related_habit_id: str = None,
                           log_type: str = None,
                           content_search: str = None,
                           date_begin: str = None,
                           date_end: str = None,
                           limit: int = 20,
                           offset: int = 0):
    """
    Retrieve progress logs from the database based on search criteria.
    
    Args:
        user_id: The user ID to get logs for (optional, but recommended)
        log_id: Specific log ID to find (optional)
        related_goal_id: Get logs for a specific goal (optional)
        related_habit_id: Get logs for a specific habit (optional)
        log_type: Filter by log type (optional)
        content_search: Search within log content (optional)
        date_begin: Filter logs created on or after this date (optional)
        date_end: Filter logs created on or before this date (optional)
        limit: Maximum number of results (default 20)
        offset: Number of results to skip (default 0)
    
    Returns:
        List of progress logs or error message
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Build base query with joins to get goal/habit info
        query = """
            SELECT p.log_id, p.user_id, p.content, p.log_type, p.related_goal_id, p.related_habit_id,
                   p.created_at, p.last_updated,
                   g.title as goal_title, h.title as habit_title
            FROM progress_logs p
            LEFT JOIN goals g ON p.related_goal_id = g.goal_id
            LEFT JOIN habits h ON p.related_habit_id = h.habit_id
            WHERE 1=1
        """
        params = []
        conditions = []
        
        # Add optional filters
        if user_id:
            conditions.append("p.user_id = %s")
            params.append(user_id)
            
        if log_id:
            conditions.append("p.log_id = %s")
            params.append(log_id)
            
        if related_goal_id:
            conditions.append("p.related_goal_id = %s")
            params.append(related_goal_id)
            
        if related_habit_id:
            conditions.append("p.related_habit_id = %s")
            params.append(related_habit_id)
            
        if log_type:
            conditions.append("p.log_type = %s")
            params.append(log_type)
            
        if content_search:
            conditions.append("p.content ILIKE %s")
            params.append(f"%{content_search}%")
            
        if date_begin:
            conditions.append("p.created_at >= %s")
            params.append(date_begin)
            
        if date_end:
            conditions.append("p.created_at <= %s")
            params.append(date_end)
        
        # Add conditions to query
        if conditions:
            query += " AND " + " AND ".join(conditions)
            
        # Add ordering and pagination
        query += " ORDER BY p.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        logger.info(f"Executing query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute query
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        if not rows:
            cursor.close()
            conn.close()
            return "No progress logs found matching the criteria."
        
        # Convert to list of dictionaries
        columns = [desc[0] for desc in cursor.description]
        progress_logs = []
        for row in rows:
            log = dict(zip(columns, row))
            # Convert datetime objects to strings for JSON serialization
            for key, value in log.items():
                if isinstance(value, datetime):
                    log[key] = value.isoformat()
            progress_logs.append(log)
        
        cursor.close()
        conn.close()
        
        logger.info(f"Retrieved {len(progress_logs)} progress logs")
        return progress_logs
        
    except DatabaseError as de:
        logger.error(f"Database error in get_progress_logs: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error",
            "message": "Failed to retrieve progress logs from database",
            "details": str(de),
            "filters_used": []
        }
            
    except ValueError as ve:
        logger.error(f"ValueError in get_progress_logs: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid parameters provided",
            "details": str(ve),
            "suggestions": [
                "Verify date formats (YYYY-MM-DD)",
                "Check parameter types and values"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_progress_logs: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while retrieving progress logs",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments",
                "Check if the service is running properly"
            ]
        }


async def update_progress_log(log_id: str, updates: Dict[str, Any]):
    """
    Update properties of a single progress log. This function enforces safe updates.
    
    Args:
        log_id: The specific progress log to update (required) 
        updates: Dictionary of updates to make (required)
        
    Available columns to update:
        - content: Progress log content (string)
        - log_type: Type of progress log (string)
        - related_goal_id: Goal this progress relates to (string, can be set to null)
        - related_habit_id: Habit this progress relates to (string, can be set to null)
        
    Returns:
        Dictionary with success status and details
    """
    # Initialize variables for error logging
    query = None
    params = None
    
    try:
        # Input validation
        if not log_id or not str(log_id).strip():
            raise ValueError("log_id is required")
            
        if not updates or not isinstance(updates, dict):
            raise ValueError("updates dictionary is required")
            
        # Define allowed columns and their validation
        allowed_columns = {
            'content': str,
            'log_type': str,
            'related_goal_id': str,  # Can be None
            'related_habit_id': str  # Can be None
        }
        
        # Validate updates
        validated_updates = {}
        for column, value in updates.items():
            if column not in allowed_columns:
                raise ValueError(f"Column '{column}' is not allowed for updates")
                
            # Allow None for relationship columns
            if column in ['related_goal_id', 'related_habit_id'] and value is None:
                validated_updates[column] = None
            elif value is not None:
                validated_updates[column] = value
            
        if not validated_updates:
            raise ValueError("No valid updates provided")
            
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for column, value in validated_updates.items():
            set_clauses.append(f"{column} = %s")
            params.append(value)
            
        # Add last_updated timestamp
        set_clauses.append("last_updated = CURRENT_TIMESTAMP")
        
        # Add WHERE condition
        params.append(log_id)
        
        query = f"""
            UPDATE progress_logs 
            SET {', '.join(set_clauses)}
            WHERE log_id = %s
            RETURNING log_id, content, log_type, last_updated
        """
        
        logger.info(f"Executing update query: {query}")
        logger.info(f"With parameters: {params}")
        
        # Execute update
        conn = get_postgres_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        updated_row = cursor.fetchone()
        if not updated_row:
            cursor.close()
            conn.close()
            return {
                "success": False,
                "error_type": "not_found",
                "message": f"No progress log found with ID {log_id}",
                "log_id": log_id
            }
            
        # Commit the transaction
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Successfully updated progress log {log_id}")
        
        return {
            "success": True,
            "message": f"Progress log {log_id} updated successfully",
            "updated_log_id": str(updated_row[0]),
            "updated_fields": list(validated_updates.keys()),
            "updates_applied": validated_updates
        }
        
    except DatabaseError as de:
        logger.error(f"Database error in update_progress_log: {str(de)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "database_error", 
            "message": "Failed to update progress log in database",
            "details": str(de),
            "log_id": log_id,
            "suggestions": [
                "Check if the progress log exists",
                "Verify database connection settings",
                "Ensure all field values are valid"
            ]
        }
        
    except ValueError as ve:
        logger.error(f"ValueError in update_progress_log: {str(ve)}")
        return {
            "success": False,
            "error_type": "validation_error",
            "message": "Invalid data provided for progress log update",
            "details": str(ve),
            "suggestions": [
                "Check if log_id is provided",
                "Verify data types and formats",
                "Ensure log_type values are appropriate"
            ]
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in update_progress_log: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        return {
            "success": False,
            "error_type": "unexpected_error",
            "message": "An unexpected error occurred while updating progress log",
            "details": str(e),
            "suggestions": [
                "Try again in a few moments", 
                "Check if the service is running properly"
            ]
        }


#test function to insert a habit
async def test_insert_habit():
    """
    Test function to insert a habit
     """
    # await insert_habit(user_id="123", title="Test Habit", description="Test Description", status="in_progress", start_date=datetime.now(), target_date=datetime.now(), frequency_type="day", frequency_value=1)
    # print("Habit inserted successfully")

    # await get_habits(user_id="123")
    # print("Habits retrieved successfully")

    await update_habits(user_id="123", habit_id="4", updates={"status": "completed"})
    print("Habit updated successfully")

if __name__ == "__main__":
    asyncio.run(test_insert_habit())
   



