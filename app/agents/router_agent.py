
# goalgetter/app/agents/router_agent.py

# --- Import Libraries ---
import asyncio
import os
import logging
from typing import Optional, List, Dict, Any, Literal, Annotated
from dotenv import load_dotenv
from pydantic import BaseModel, Field

#Shared Services
from app.shared_services.llm import call_llm_api

#Models
from app.models.pydantic_models import GoalGetterState, RouterOutput, UserIntent
#Prompts
from app.prompts.routing_agent_prompt import get_routing_agent_prompt

# Load environment variables
load_dotenv()

#logger
logger = logging.getLogger(__name__)


# Add the router_node function for direct import
async def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Receives user_message and routes to the best Next agent."""
    # --- Print State Entering Node ---
    print("\n=== State Entering Router Node ===")
    print(state)
    print("=================================\n")
    # --- End Print ---

    print("=== Router Node Start Execution ===")

    # Convert state dict to QuizState if it's not already
    current_state = state if isinstance(state, GoalGetterState) else GoalGetterState(**state)

    # Increment router attempts
    current_state.router_attempts += 1
    print(f"Attempts: {current_state.router_attempts}")

    # Get user input from the prompt
    user_input = current_state.message
    print(f"User Input: {user_input}")

    try:
        # Get the system prompt with user input and conversation history
        system_prompt = get_routing_agent_prompt(
           current_state=current_state
     
        )
        
        # Call LLM with the prompt & structured output
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input if user_input else ""}
        ]
        
        response = call_llm_api(
            messages=messages,
            #model="gpt-4o-mini-2024-07-18",
            temperature=0.7,
            response_format=RouterOutput
        )

        print(f"Raw LLM Response: {response}")

        # Ensure response is a Handoff object
        if not isinstance(response, RouterOutput):
            print(f"Debug - Unexpected response type: {type(response)}")
            raise TypeError("LLM response was not the expected RouterOutput object.")

        # Update node_history with the parsed LLM response object
        current_state.node_history.append({
            "node_name": "router",
            "response": response
        })

        # Log state after router node (before returning changes)
        logger.info(f"State before processing response: {current_state}")

        print("=== Router Node End Execution (Success) ===")

        # Store router output in agent outputs (this is the only thing router agent should update)
        current_state.agent_outputs.router_output = {
            "next_agents": response.next_agents,
            "reasoning": response.reasoning,
            "confidence": response.confidence,
            "intent": response.intent,
            "success": response.success,
            "error": None,
            "message_to_user": response.message_to_user
        }
        
        # --- Print State Exiting Node (Success) ---
        print("\n=== State Exiting Router Node (Success) ===")
        print(current_state.dict())
        print("=========================================\n")

        # Return the updated state
        return current_state.dict()
    
    except Exception as e:
        error_msg = f"Error in router node: {str(e)}"
        print(f"Debug - {error_msg}")

        # Update node_history with error message
        current_state.node_history.append({
            "node_name": "router",
            "response": f"Error: {error_msg}"
        })

        logger.info(f"State after error in router node: {current_state}")
        print("=== Router Node End Execution (Error) ===")

        # Store error in agent outputs (router agent only updates router_output)
        current_state.agent_outputs.router_output = {
            "next_agent": None,
            "next_agents": [],
            "confidence": 0.0,
            "intent": UserIntent.UNKNOWN,
            "success": False,
            "error": error_msg,
            "message_to_user": None
        }
        
        # --- Print State Exiting Node (Error) ---
        print("\n=== State Exiting router Node (Error) ===")
        print(current_state.dict())
        print("=======================================\n")

        # Return the updated state
        return current_state.dict()
