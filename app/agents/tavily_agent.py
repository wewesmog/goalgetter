# mwalimubot/backedn/app/agents/tutor_agent.py

# --- Import Libraries ---
import asyncio
import os
import logging
from typing import Optional, List, Dict, Any, Literal, Annotated
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from tavily import TavilyClient


#Models
from app.models.pydantic_models import MwalimuBotState, Handoff, TutorParameters, RespondToUserParameters, TavilyParameters


# Load environment variables
load_dotenv()

# logger
logger = logging.getLogger(__name__)


# Add the tavily agent function
async def tavily_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Tavily Agent"""
    print("Tavily Agent called")
    print(f"Tavily Agent called with state: {state}")
    # Convert state dict to MwalimuBotState
    bot_state = MwalimuBotState.model_validate(state)
    
    # Initialize Tavily client
    client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

    # Search for information using Tavily
    try:
        response = client.search(
            query=bot_state.user_input,  # Use the actual user input
            include_raw_content=True,
            include_domains=["https://lms.kec.ac.ke/"],
            max_results=1,  # Default value
            score_threshold=0.7  # Default value
        )
        
        # Update state
        return {
            "tavily_results": response,
            "tavily_attempts": (bot_state.tavily_attempts or 0) + 1
        }
        
    except Exception as e:
        logger.error(f"Tavily search error: {str(e)}")
        return {
            "tavily_results": None,
            "tavily_attempts": (bot_state.tavily_attempts or 0) + 1,
            "error_message": f"Failed to get search results: {str(e)}"
        }

if __name__ == "__main__":
    # Test the tavily_agent with sample data
    test_state = {
        "user_input": "What is photosynthesis?",
        "tavily_attempts": 0,
        # Add other required MwalimuBotState fields here
    }
    asyncio.run(tavily_agent(test_state))

