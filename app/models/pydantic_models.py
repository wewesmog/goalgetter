from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, date
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ARCHIVED = "archived"

class MilestoneStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class HabitFrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class LogType(str, Enum):
    GOAL_CREATED = "goal_created"
    GOAL_UPDATED = "goal_updated"
    MILESTONE_COMPLETED = "milestone_completed"
    HABIT_COMPLETED = "habit_completed"
    REFLECTION = "reflection"
    MOOD_UPDATE = "mood_update"
    OBSTACLE = "obstacle"
    ACHIEVEMENT = "achievement"

class ConversationType(str, Enum):
    GOAL_PLANNING = "goal_planning"
    PROGRESS_UPDATE = "progress_update"
    HABIT_TRACKING = "habit_tracking"
    EMOTIONAL_SUPPORT = "emotional_support"
    REFLECTION = "reflection"
    GENERAL_CHAT = "general_chat"

class UserIntent(str, Enum):
    CREATE_GOAL = "create_goal"
    UPDATE_GOAL = "update_goal"
    TRACK_PROGRESS = "track_progress"
    CREATE_HABIT = "create_habit"
    LOG_HABIT = "log_habit"
    GET_SUPPORT = "get_support"
    REFLECT = "reflect"
    VIEW_PROGRESS = "view_progress"
    UNKNOWN = "unknown"

# ============================================================================
# BASE DATA MODELS
# ============================================================================

class GoalGetterRequest(BaseModel):
    user_id: int = Field(..., description="Telegram user ID")
    user_name: Optional[str] = Field(None, description="User's name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp of the request")
    message: str = Field(..., description="User's message")

class User(BaseModel):
    user_id: int = Field(..., description="Telegram user ID")
    first_name: Optional[str] = Field(None, description="User's first name")
    timezone: Optional[str] = Field(None, description="User's timezone")
    created_at: datetime = Field(default_factory=datetime.now)

class Goal(BaseModel):
    goal_id: Optional[int] = Field(None, description="Auto-generated goal ID")
    user_id: int = Field(..., description="User who owns this goal")
    title: str = Field(..., description="Goal title")
    description: Optional[str] = Field(None, description="Goal description")
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)
    start_date: Optional[date] = Field(None, description="Goal start date")
    target_date: Optional[date] = Field(None, description="Goal target date")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

class Milestone(BaseModel):
    milestone_id: Optional[int] = Field(None, description="Auto-generated milestone ID")
    goal_id: int = Field(..., description="Parent goal ID")
    description: str = Field(..., description="Milestone description")
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    target_date: Optional[date] = Field(None, description="Milestone target date")
    completed_at: Optional[datetime] = Field(None, description="When milestone was completed")

class Habit(BaseModel):
    habit_id: Optional[int] = Field(None, description="Auto-generated habit ID")
    user_id: int = Field(..., description="User who owns this habit")
    description: str = Field(..., description="Habit description")
    frequency_type: HabitFrequencyType = Field(..., description="How often to do the habit")
    frequency_value: int = Field(..., description="Frequency value (e.g., 3 for 3 times per week)")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

class ProgressLog(BaseModel):
    log_id: Optional[int] = Field(None, description="Auto-generated log ID")
    user_id: int = Field(..., description="User who owns this log")
    related_goal_id: Optional[int] = Field(None, description="Related goal if applicable")
    related_habit_id: Optional[int] = Field(None, description="Related habit if applicable")
    log_type: LogType = Field(..., description="Type of progress log")
    content: str = Field(..., description="Log content")
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

class UserSummary(BaseModel):
    user_id: int = Field(..., description="User ID")
    summary: str = Field(..., description="AI-generated user personality summary")
    last_updated: datetime = Field(default_factory=datetime.now)

class Conversation(BaseModel):
    conversation_id: Optional[int] = Field(None, description="Auto-generated conversation ID")
    user_id: int = Field(..., description="User ID")
    conversation_type: ConversationType = Field(..., description="Type of conversation")
    conversation_data: Dict[str, Any] = Field(default_factory=dict, description="Conversation data")
    state: Dict[str, Any] = Field(default_factory=dict, description="Conversation state")
    created_at: datetime = Field(default_factory=datetime.now)



# ============================================================================
# AGENT INPUTS/OUTPUTS (PART OF MAIN STATE)
# ============================================================================


class Handoff(BaseModel):
    """Handoff data"""
    agent: str = Field(..., description="Agent or tool to handoff to")
    reasoning: str = Field(..., description="Reasoning for the handoff")
    agent_specific: Optional[str] = Field(None, description="Message to user")

class RouterOutput(BaseModel):
    """Output for the router agent"""

    next_agents: List[str] = Field(default_factory=list, description="Next agent(s) to call")
    reasoning: str = Field(..., description="Reasoning for the next agent(s) to call")
    confidence: float = Field(default=0.0, description="Confidence in intent detection")
    intent: UserIntent = Field(..., description="Detected user intent")
    error: Optional[str] = Field(None, description="Error message if something went wrong")
    success: bool = Field(default=True, description="Whether the operation was successful")
    message_to_user: Optional[str] = Field(None, description="Message to user") 

class AgentInputs(BaseModel):
    """All agent inputs stored in main state"""
    router_input: Dict[str, Any] = Field(default_factory=dict, description="Router agent input data")
    goal_input: Dict[str, Any] = Field(default_factory=dict, description="Goal agent input data")
    habit_input: Dict[str, Any] = Field(default_factory=dict, description="Habit agent input data")
    memory_input: Dict[str, Any] = Field(default_factory=dict, description="Memory agent input data")
    progress_input: Dict[str, Any] = Field(default_factory=dict, description="Progress agent input data")

class AgentOutputs(BaseModel):
    """All agent outputs stored in main state"""
    router_output: Dict[str, Any] = Field(default_factory=dict, description="Router agent output data")
    goal_output: Dict[str, Any] = Field(default_factory=dict, description="Goal agent output data")
    habit_output: Dict[str, Any] = Field(default_factory=dict, description="Habit agent output data")
    memory_output: Dict[str, Any] = Field(default_factory=dict, description="Memory agent output data")
    progress_output: Dict[str, Any] = Field(default_factory=dict, description="Progress agent output data")

# ============================================================================
# MAIN STATE
# ============================================================================

class GoalGetterState(BaseModel):
    """Main state for GoalGetter LangGraph application"""
    
    # User information
    user_id: int = Field(..., description="Telegram user ID")
    user: Optional[User] = Field(None, description="User information")
    
    # Current conversation
    message: str = Field(..., description="Current user message")
    response: str = Field(default="", description="Agent response to user")

    # Attempts
    router_attempts: int = Field(default=0, description="Number of attempts to route user input")
    goal_attempts: int = Field(default=0, description="Number of attempts to create/update goals")
    habit_attempts: int = Field(default=0, description="Number of attempts to create/update habits")
    memory_attempts: int = Field(default=0, description="Number of attempts to generate memory")
    progress_attempts: int = Field(default=0, description="Number of attempts to log progress")

    # Node history
    node_history: List[Dict[str, Any]] = Field(default_factory=list, description="Node history")
    
    # Intent and routing (managed by router agent output)
    # intent, next_agent, confidence are stored in agent_outputs.router_output
    
    # Data from database
    goals: List[Goal] = Field(default_factory=list, description="User's goals")
    habits: List[Habit] = Field(default_factory=list, description="User's habits")
    milestones: List[Milestone] = Field(default_factory=list, description="User's milestones")
    progress_logs: List[ProgressLog] = Field(default_factory=list, description="User's progress logs")
    user_summary: Optional[UserSummary] = Field(None, description="User's personality summary")
    conversations: List[Conversation] = Field(default_factory=list, description="Recent conversations")
    

    
    # Context and memory
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    insights: List[str] = Field(default_factory=list, description="Insights generated")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for user")
    
    # Agent inputs/outputs (part of main state)
    agent_inputs: AgentInputs = Field(default_factory=AgentInputs, description="Inputs for each agent")
    agent_outputs: AgentOutputs = Field(default_factory=AgentOutputs, description="Outputs from each agent")
    
    # Session tracking
    session_start: datetime = Field(default_factory=datetime.now, description="When this session started")
    interaction_count: int = Field(default=0, description="Number of interactions in this session")
    
    # Error handling
    error: Optional[str] = Field(None, description="Error message if something went wrong")
    success: bool = Field(default=True, description="Whether the operation was successful")

# ============================================================================
# UTILITY MODELS
# ============================================================================

class DatabaseOperation(BaseModel):
    """Model for database operations"""
    operation_type: str = Field(..., description="Type of operation (create, update, delete)")
    table: str = Field(..., description="Database table name")
    data: Dict[str, Any] = Field(..., description="Data for the operation")
    success: bool = Field(default=True, description="Whether operation was successful")
    error: Optional[str] = Field(None, description="Error message if failed")

class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    success: bool = Field(..., description="Whether the agent operation was successful")
    response: str = Field(..., description="Agent's response to user")
    data_changes: Dict[str, Any] = Field(default_factory=dict, description="Data changes made")
    next_agent: Optional[str] = Field(None, description="Next agent to call")
    context_updates: Dict[str, Any] = Field(default_factory=dict, description="Context updates")

