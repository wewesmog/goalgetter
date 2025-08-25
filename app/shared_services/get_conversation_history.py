import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from .db import get_postgres_connection
from .logger_setup import setup_logger
from psycopg2.extras import RealDictCursor
from app.models.pydantic_models import GoalGetterState, User


logger = setup_logger()

def get_conversation_history(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Extract and log conversation history from state column ordered by latest first
    """
    conn = get_postgres_connection()
    try:
        #Get past conversations in JSON format
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    state->'conversation_historycon' as conversation_history
                FROM conversations 
                WHERE user_id = %s 
                AND session_id = %s 
                ORDER BY log_timestamp DESC
                LIMIT %s;
            """, (user_id, session_id, limit))
            
            conversation_history = cur.fetchall()
            

            # get goals

            
            if not conversation_history:
                logger.info(f"No conversations found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "conversations": []
                }
            
            # Extract conversations and sort by timestamp
            conversations = []
            for result in conversation_history:
                if result['conversation_history']:
                    conversations.extend(result['conversation_history'])
            
            # Sort by timestamp within conversation_history
            sorted_conversations = sorted(
                conversations,
                key=lambda x: datetime.fromisoformat(x['timestamp']),
                reverse=True  # Newest first
            )
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_messages": len(sorted_conversations),
                    "query_limit": limit
                },
                "conversations": sorted_conversations
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "conversations": []
        }
        logger.error(f"Error retrieving conversation history: {e}")
        return error_response
    finally:
        conn.close()


def get_goals(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Get goals from the database
    """
    conn = get_postgres_connection()
    try:
        #Get past goals in JSON format
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    goal_id,
                    user_id,
                    title,
                    description,
                    status,
                    start_date,
                    target_date,
                    created_at,
                    last_updated
                FROM goals 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                LIMIT %s;
            """, (user_id, limit))
            
            goals = cur.fetchall()
            

            # get goals

            
            if not goals:
                logger.info(f"No goals found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "goals": []
                }
            
            # Extract goals into list of dicts
            goals_list = []
            for result in goals:
                if result['title']:
                    goals_list.append({
                        'goal_id': result['goal_id'],
                        'user_id': result['user_id'],
                        'title': result['title'],
                        'description': result['description'],
                        'status': result['status'],
                        'start_date': result['start_date'].isoformat() if result['start_date'] else None,
                        'target_date': result['target_date'].isoformat() if result['target_date'] else None,
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'last_updated': result['last_updated'].isoformat() if result['last_updated'] else None
                    })
            
            # Sort by start_date (handle None values)
            sorted_goals = sorted(
                goals_list,
                key=lambda x: datetime.fromisoformat(x['start_date']) if x['start_date'] else datetime.min,
                reverse=True  # Newest first
            )
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_goals": len(sorted_goals),
                    "query_limit": limit
                },
                "goals": sorted_goals
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "goals": []
        }
        logger.error(f"Error retrieving goals: {e}")
        return error_response
    finally:
        conn.close()


def get_habits(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Get habits from the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    habit_id,
                    user_id,
                    description,
                    frequency_type,
                    frequency_value,
                    created_at,
                    last_updated
                FROM habits 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                LIMIT %s;
            """, (user_id, limit))
            
            habits = cur.fetchall()
            
            if not habits:
                logger.info(f"No habits found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "habits": []
                }
            
            # Extract habits into list of dicts
            habits_list = []
            for result in habits:
                if result['description']:
                    habits_list.append({
                        'habit_id': result['habit_id'],
                        'user_id': result['user_id'],
                        'description': result['description'],
                        'frequency_type': result['frequency_type'],
                        'frequency_value': result['frequency_value'],
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'last_updated': result['last_updated'].isoformat() if result['last_updated'] else None
                    })
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_habits": len(habits_list),
                    "query_limit": limit
                },
                "habits": habits_list
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "habits": []
        }
        logger.error(f"Error retrieving habits: {e}")
        return error_response
    finally:
        conn.close()


def get_milestones(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Get milestones from the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    m.milestone_id,
                    m.goal_id,
                    m.description,
                    m.status,
                    m.target_date,
                    m.completed_at,
                    m.created_at,
                    m.last_updated,
                    g.title as goal_title
                FROM milestones m
                JOIN goals g ON m.goal_id = g.goal_id
                WHERE g.user_id = %s 
                ORDER BY m.created_at DESC
                LIMIT %s;
            """, (user_id, limit))
            
            milestones = cur.fetchall()
            
            if not milestones:
                logger.info(f"No milestones found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "milestones": []
                }
            
            # Extract milestones into list of dicts
            milestones_list = []
            for result in milestones:
                if result['description']:
                    milestones_list.append({
                        'milestone_id': result['milestone_id'],
                        'goal_id': result['goal_id'],
                        'goal_title': result['goal_title'],
                        'description': result['description'],
                        'status': result['status'],
                        'target_date': result['target_date'].isoformat() if result['target_date'] else None,
                        'completed_at': result['completed_at'].isoformat() if result['completed_at'] else None,
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'last_updated': result['last_updated'].isoformat() if result['last_updated'] else None
                    })
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_milestones": len(milestones_list),
                    "query_limit": limit
                },
                "milestones": milestones_list
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "milestones": []
        }
        logger.error(f"Error retrieving milestones: {e}")
        return error_response
    finally:
        conn.close()


def get_progress_logs(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Get progress logs from the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    pl.log_id,
                    pl.related_goal_id,
                    pl.related_habit_id,
                    pl.log_type,
                    pl.content,
                    pl.created_at,
                    pl.last_updated,
                    g.title as goal_title,
                    h.description as habit_description
                FROM progress_logs pl
                LEFT JOIN goals g ON pl.related_goal_id = g.goal_id
                LEFT JOIN habits h ON pl.related_habit_id = h.habit_id
                WHERE pl.user_id = %s 
                ORDER BY pl.created_at DESC
                LIMIT %s;
            """, (user_id, limit))
            
            progress_logs = cur.fetchall()
            
            if not progress_logs:
                logger.info(f"No progress logs found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "progress_logs": []
                }
            
            # Extract progress logs into list of dicts
            logs_list = []
            for result in progress_logs:
                if result['content']:
                    logs_list.append({
                        'log_id': result['log_id'],
                        'user_id': int(user_id),
                        'related_goal_id': result['related_goal_id'],
                        'related_habit_id': result['related_habit_id'],
                        'log_type': result['log_type'],
                        'content': result['content'],
                        'created_at': result['created_at'].isoformat() if result['created_at'] else None,
                        'last_updated': result['last_updated'].isoformat() if result['last_updated'] else None
                    })
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_logs": len(logs_list),
                    "query_limit": limit
                },
                "progress_logs": logs_list
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "progress_logs": []
        }
        logger.error(f"Error retrieving progress logs: {e}")
        return error_response
    finally:
        conn.close()


def get_user_summary(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get user summary from the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    user_id,
                    summary,
                    last_updated
                FROM user_summaries 
                WHERE user_id = %s;
            """, (user_id,))
            
            user_summary = cur.fetchone()
            
            if not user_summary:
                logger.info(f"No user summary found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    "user_summary": None
                }
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                },
                "user_summary": {
                    'user_id': user_summary['user_id'],
                    'summary': user_summary['summary'],
                    'last_updated': user_summary['last_updated'].isoformat() if user_summary['last_updated'] else None
                }
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "user_summary": None
        }
        logger.error(f"Error retrieving user summary: {e}")
        return error_response
    finally:
        conn.close()


def get_conversations(
    user_id: str, 
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 10000,
) -> Dict[str, Any]:
    """
    Get conversations from the database (different from conversation history)
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    conversation_id,
                    user_id,
                    conversation_type,
                    conversation_data,
                    created_at
                FROM conversations 
                WHERE user_id = %s 
                ORDER BY created_at DESC
                LIMIT %s;
            """, (user_id, limit))
            
            conversations = cur.fetchall()
            
            if not conversations:
                logger.info(f"No conversations found for user_id: {user_id}")
                return {
                    "status": "no_data",
                    "metadata": {
                        "user_id": user_id,
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "query_limit": limit
                    },
                    "conversations": []
                }
            
            # Extract conversations into list of dicts
            conversations_list = []
            for result in conversations:
                conversations_list.append({
                    'conversation_id': result['conversation_id'],
                    'user_id': result['user_id'],
                    'conversation_type': result['conversation_type'],
                    'conversation_data': result['conversation_data'],
                    'created_at': result['created_at'].isoformat() if result['created_at'] else None
                })
            
            output = {
                "status": "success",
                "metadata": {
                    "user_id": user_id,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_conversations": len(conversations_list),
                    "query_limit": limit
                },
                "conversations": conversations_list
            }
            
        return output
            
    except Exception as e:
        error_response = {
            "status": "error",
            "metadata": {
                "user_id": user_id,
                "session_id": session_id,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            },
            "conversations": []
        }
        logger.error(f"Error retrieving conversations: {e}")
        return error_response
    finally:
        conn.close()

def get_user(user_id: str) -> Optional[User]:
    """
    Get user from the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    user_id, 
                    first_name, 
                    timezone, 
                    created_at 
                FROM users 
                WHERE user_id = %s
            """, (user_id,))
            
            user_data = cur.fetchone()
            
            if not user_data:
                logger.info(f"No user found for user_id: {user_id}")
                return None
            
            # Convert datetime to string for Pydantic validation
            user_dict = {
                'user_id': user_data['user_id'],
                'first_name': user_data['first_name'],
                'timezone': user_data['timezone'] if user_data['timezone'] else None,
                'created_at': user_data['created_at'].isoformat() if user_data['created_at'] else None
            }
            
            return User.model_validate(user_dict)
            
    except Exception as e:
        logger.error(f"Error retrieving user: {e}")
        return None
    finally:
        conn.close()

def create_user(user_id: str) -> Optional[User]:
    """
    Create user in the database
    """
    conn = get_postgres_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # First check if user already exists
            cur.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
            existing_user = cur.fetchone()
            
            if existing_user:
                logger.info(f"User {user_id} already exists, returning existing user")
                return get_user(user_id)
            
            # Create new user
            cur.execute("""
                INSERT INTO users (user_id, first_name, timezone, created_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, None, "UTC", datetime.now()))
            conn.commit()
            return get_user(user_id)
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None
    finally:
        conn.close()

def populate_state(user_id: str, message: str = "") -> GoalGetterState:
    """
    Populate GoalGetterState with user data from database
    """
    # Check if user exists
    user_exists = get_user(user_id)
    if not user_exists:
        # Create user
        created_user = create_user(user_id)
        if not created_user:
            logger.error(f"Failed to create user: {user_id}")
            return None
        user_exists = created_user
    
    # Get all user data from database
    conversations_result = get_conversations(user_id=user_id, limit=10000)
    goals_result = get_goals(user_id=user_id, limit=10000)
    habits_result = get_habits(user_id=user_id, limit=10000)
    milestones_result = get_milestones(user_id=user_id, limit=10000)
    progress_logs_result = get_progress_logs(user_id=user_id, limit=10000)
    user_summary_result = get_user_summary(user_id=user_id)
    
    # Convert database results to Pydantic models
    from app.models.pydantic_models import Goal, Habit, Milestone, ProgressLog, UserSummary, Conversation
    
    # Convert goals
    goals_list = []
    if goals_result["status"] == "success" and goals_result["goals"]:
        for goal_data in goals_result["goals"]:
            try:
                goal = Goal.model_validate(goal_data)
                goals_list.append(goal)
            except Exception as e:
                logger.error(f"Error validating goal: {e}")
    
    # Convert habits
    habits_list = []
    if habits_result["status"] == "success" and habits_result["habits"]:
        for habit_data in habits_result["habits"]:
            try:
                habit = Habit.model_validate(habit_data)
                habits_list.append(habit)
            except Exception as e:
                logger.error(f"Error validating habit: {e}")
    
    # Convert milestones
    milestones_list = []
    if milestones_result["status"] == "success" and milestones_result["milestones"]:
        for milestone_data in milestones_result["milestones"]:
            try:
                milestone = Milestone.model_validate(milestone_data)
                milestones_list.append(milestone)
            except Exception as e:
                logger.error(f"Error validating milestone: {e}")
    
    # Convert progress logs
    progress_logs_list = []
    if progress_logs_result["status"] == "success" and progress_logs_result["progress_logs"]:
        for log_data in progress_logs_result["progress_logs"]:
            try:
                progress_log = ProgressLog.model_validate(log_data)
                progress_logs_list.append(progress_log)
            except Exception as e:
                logger.error(f"Error validating progress log: {e}")
    
    # Convert user summary
    user_summary_obj = None
    if user_summary_result["status"] == "success" and user_summary_result["user_summary"]:
        try:
            user_summary_obj = UserSummary.model_validate(user_summary_result["user_summary"])
        except Exception as e:
            logger.error(f"Error validating user summary: {e}")
    
    # Convert conversations
    conversations_list = []
    if conversations_result["status"] == "success" and conversations_result["conversations"]:
        for conv_data in conversations_result["conversations"]:
            try:
                conversation = Conversation.model_validate(conv_data)
                conversations_list.append(conversation)
            except Exception as e:
                logger.error(f"Error validating conversation: {e}")
    
    # Create and return populated state
    state = GoalGetterState(
        user_id=int(user_id),
        user=user_exists,
        message=message,
        goals=goals_list,
        habits=habits_list,
        milestones=milestones_list,
        progress_logs=progress_logs_list,
        user_summary=user_summary_obj,
        conversations=conversations_list
    )
    
    logger.info(f"Successfully populated state for user {user_id}")
    return state

