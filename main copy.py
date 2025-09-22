# main.py - Simplified for human-in-the-loop conversation handling

from fastapi import FastAPI, HTTPException, Form, Request, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
import logging
import os
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse
import uvicorn
#from app.telegram_handler import app as telegram_app
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import Pydantic Models
from app.models.pydantic_models import (
    GoalGetterState,
    GoalGetterRequest
)

# Import DB Functions
from app.shared_services.get_conversation_history import populate_state

# Import Graph Builder
from app.graph.graph import build_graph

# Build and compile the graph once when the application starts
workflow = build_graph()
graph = workflow.compile()
logger.info("LangGraph built and compiled successfully.")

# FastAPI App Instance
app = FastAPI(
    title="GoalGetter API", 
    description="AI Goal, Habit and Progress Tracker - A LangGraph-powered chatbot for goal setting and habit tracking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/")
async def read_root():
    return {"message": "GoalGetter API is running!"}

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify the API is working"""
    return {"message": "API is working!", "status": "success"}

@app.post("/chat/")
async def chat_endpoint(request: GoalGetterRequest):
    """
    Handles chat interactions with human-in-the-loop state management.
    """
    # Debug logging
    logger.info("Chat endpoint received!")
    
    try:
        loaded_state = None

        print(f"User ID: {request.user_id}")
        print(f"User Message: {request.message}")

        # 1. Handle existing conversation or create new one
        user_id = request.user_id

        # 2. Populate the state
        loaded_state = populate_state(str(user_id), request.message)
        if not loaded_state:
            raise HTTPException(status_code=500, detail="Failed to populate state")

  

        # 3. Run the graph with the state
        final_state = await graph.ainvoke(loaded_state.model_dump())
        final_state = GoalGetterState.model_validate(final_state)
        logger.info(f"Graph execution completed for {user_id}")

        # Print the final state
        logger.info(f"Final state: {final_state}")
        
        # Return response
        #response_message = final_state.response if final_state.response else "Processing complete."
        response_message = final_state
        return {"message": response_message}

        # # 4. Save the final state
        # state_to_save = final_state.model_dump()
        # state_to_save["phone_number"] = phone_number  # Ensure phone_number is in the state
        # save_conversation(state_to_save)
        # logger.info(f"Saved state for conversation {phone_number}")

        # 5. Prepare response
        # response_message = None
        # if final_state.message_to_student:
        #     response_message = final_state.message_to_student
        #     logger.info(f"Sending message to student: {response_message}")
        # elif final_state.response_to_user:
        #     response_message = final_state.response_to_user
        #     logger.info(f"Sending response to user: {response_message}")
        # else:
        #     response_message = "Processing complete."
        #     logger.info("No specific message found, sending default response")

        # Create Twilio response
        # twilio_response = MessagingResponse()
        # twilio_response.message(str(response_message))
        # logger.info(f"Created Twilio response with message: {str(response_message)}")
        
        # return Response(
        #     content=str(twilio_response),
        #     media_type="application/xml"
        # )

    except Exception as e:
        logger.error(f"Error processing conversation {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}"
        )

# @app.post("/chat/json")
# async def chat_json_endpoint(request: ChatRequest):
#     """
#     Handles chat interactions with JSON input instead of form data.
#     """
#     logger.info("JSON endpoint called!")
    
#     try:
#         phone_number = request.From
#         message_body = request.Body
        
#         logger.info(f"From: {phone_number}")
#         logger.info(f"Message: {message_body}")
        
#         loaded_state = None

#         # Try to load existing conversation if ID was provided
#         if phone_number:
#             loaded_state_data = load_conversation(phone_number)
#             if loaded_state_data:
#                 loaded_state = MwalimuBotState.model_validate(loaded_state_data)
#                 loaded_state.error_message = None
#                 loaded_state.handoff_agents_params = []
#                 loaded_state.handoff_agents = []
#                 loaded_state.user_input = message_body
#                 loaded_state.conversation_history.append({
#                     "role": "human", 
#                     "content": message_body
#                 })
#                 logger.info(f"Loaded and updated existing state for conversation {phone_number}")

#         # Create new state if none exists
#         if not loaded_state:
#             loaded_state = MwalimuBotState(
#                 user_id=phone_number,
#                 phone_number=phone_number,
#                 user_input=message_body,
#                 conversation_history=[{"role": "human", "content": message_body}],
#                 current_subject=None,
#                 current_grade = 2,
#                 rag_context = None,
#                 node_history=[],
#                 ready_for_tutoring= False,
#                 ready_for_quiz = False,
#                 first_node="routing_agent",
#                 current_step=None,
#                 response_to_user_attempts=0,
#                 tavily_results=None,
#                 tavily_attempts=0
#             )
#             logger.info(f"Created new state for conversation {phone_number}")

#         # Run the graph with the state
#         final_state = await graph.ainvoke(loaded_state.model_dump())
#         final_state = MwalimuBotState.model_validate(final_state)
#         logger.info(f"Graph execution completed for {phone_number}")

#         # Save the final state
#         state_to_save = final_state.model_dump()
#         state_to_save["phone_number"] = phone_number
#         save_conversation(state_to_save)
#         logger.info(f"Saved state for conversation {phone_number}")

#         # Prepare response
#         response_message = None
#         if final_state.message_to_student:
#             response_message = final_state.message_to_student
#         elif final_state.response_to_user:
#             response_message = final_state.response_to_user
#         else:
#             response_message = "Processing complete."

#         return {
#             "message": str(response_message)
#         }

#     except Exception as e:
#         logger.error(f"Error processing conversation: {str(e)}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail="An error occurred while processing your request"
#         )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)