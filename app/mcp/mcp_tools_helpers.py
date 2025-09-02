# Database helper functions
from typing import Optional, List, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import psycopg2
from psycopg2 import DatabaseError
from shared_services.db import get_db
from shared_services.logger_setup import setup_logger

logger = setup_logger()



async def get_goals(user_id: str,
                   db: Session = Depends(get_db),
              goal_id: str = None, 
              goal_name: str = None, 
              goal_status: str = None, 
              goal_priority: str = None, 
              goal_start_date: str = None, 
              goal_end_date: str = None,
              limit: int = 10,
              offset: int = 0):
    """
    Get goals from the database based on filters.

    Args:
        user_id: str - Required. The user's ID
        goal_id: str - Optional. Specific goal ID to find
        goal_name: str - Optional. Search by goal title
        goal_status: str - Optional. Filter by status (in_progress, completed, cancelled)
        goal_start_date: str - Optional. Filter by start date (YYYY-MM-DD)
        goal_end_date: str - Optional. Filter by end date (YYYY-MM-DD)
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
        - end_date: str - End date (YYYY-MM-DD)

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
        if goal_name:
            conditions.append("title = %s")
            params.append(goal_name)
        if goal_status:
            conditions.append("status = %s")
            params.append(goal_status)
        if goal_start_date:
            conditions.append("start_date = %s")
            params.append(goal_start_date)
        if goal_end_date:
            conditions.append("end_date = %s")
            params.append(goal_end_date)
        
        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        query = f"""
            SELECT * FROM goals 
            WHERE {where_clause}
            ORDER BY goal_start_date ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        async with db.cursor() as cursor:
            await cursor.execute(query, tuple(params))
            goals = await cursor.fetchall()
            if not goals:
                logger.info(f"No goals found for query parameters: {params}")
                return []
            return goals
                
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in get_goals: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        raise DatabaseError(f"Database operation failed: {str(pe)}")
            
    except Exception as e:
        logger.error(f"Unexpected error in get_goals: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        raise

#Helper Functions for the tools
async def update_goals(user_id: str,
                    goal_id: str,
                    updates: Dict[str, str],
                    db: Session = Depends(get_db)):
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
            - end_date: str - End date in YYYY-MM-DD format
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
        'end_date': 'date'
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
            
            if column in ['start_date', 'end_date']:
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
        
        try:
            async with db.cursor() as cursor:
                await cursor.execute(query, tuple(params))
                updated_rows = await cursor.fetchall()
                if not updated_rows:
                    logger.info(f"No goals found to update for user_id: {user_id}, goal_id: {goal_id}")
                    return False
                logger.info(f"Successfully updated {len(updated_rows)} goals")
                return True
                
        except psycopg2.Error as pe:
            logger.error(f"PostgreSQL error in update_goals: {str(pe)}")
            logger.error(f"Failed query: {query}")
            logger.error(f"Query parameters: {params}")
            raise DatabaseError(f"Database operation failed: {str(pe)}")
            
    except Exception as e:
        logger.error(f"Unexpected error in update_goals: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        raise


async def insert_goal(user_id: str,
                   title: str,
                   description: str,
                   status: str = 'in_progress',
                   start_date: datetime = datetime.now(),
                   end_date: datetime = None,
                   db: Session = Depends(get_db)):
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
            INSERT INTO goals (user_id, title, description, status, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING goal_id
        """
        params = [user_id, title, description, status, start_date, end_date]
        
        # Execute query
        async with db.cursor() as cursor:
            await cursor.execute(query, tuple(params))
            response = await cursor.fetchone()
            if not response:
                raise DatabaseError("Failed to create goal - no ID returned")
            goal_id = response[0]
            logger.info(f"Successfully created goal {goal_id} for user {user_id}")
            return goal_id
                
    except psycopg2.Error as pe:
        logger.error(f"PostgreSQL error in insert_goal: {str(pe)}")
        logger.error(f"Failed query: {query}")
        logger.error(f"Query parameters: {params}")
        raise DatabaseError(f"Database operation failed: {str(pe)}")
            
    except Exception as e:
        logger.error(f"Unexpected error in insert_goal: {str(e)}")
        logger.error(f"Query attempted: {query}")
        logger.error(f"Parameters: {params}")
        raise