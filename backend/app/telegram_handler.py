from fastapi import FastAPI, Request, Response
from telegram import Update, Bot
import os
import uuid
import json
from dotenv import load_dotenv
from app.agents.router_agent import router_node
from app.agents.tutor_agent import tutor_node
from app.models.pydantic_models import MwalimuBotState
from app.shared_services.save_load_conversation import save_conversation, load_conversation
from app.graph.graph import build_graph

# Initialize FastAPI app
app = FastAPI()

# Initialize Telegram bot with token
TELEGRAM_TOKEN = "8104473553:AAF-lQpLvIyZ2QQC5_ECyEFiSHm_x90C7wE"

# Create bot instance
bot = Bot(token=TELEGRAM_TOKEN)

# Instantiate the graph at the top level
mw_graph = build_graph()
mw_graph = mw_graph.compile()

def serialize_state(state_dict, chat_id):
    """Serialize state to make it JSON-compatible and ensure user_id is set"""
    if isinstance(state_dict, dict):
        serialized = {}
        for key, value in state_dict.items():
            if key == 'node_history':
                # Handle node_history specially
                serialized[key] = []
                for node in value:
                    if isinstance(node, dict) and 'response' in node:
                        # Convert Handoff object to dict representation
                        node_copy = node.copy()
                        if hasattr(node['response'], 'handoff_agents'):
                            node_copy['response'] = {
                                'handoff_agents': [
                                    {
                                        'agent_name': agent.agent_name,
                                        'message_to_agent': agent.message_to_agent,
                                        'agent_specific_parameters': agent.agent_specific_parameters.dict() 
                                        if hasattr(agent.agent_specific_parameters, 'dict') 
                                        else agent.agent_specific_parameters
                                    }
                                    for agent in node['response'].handoff_agents
                                ]
                            }
                        serialized[key].append(node_copy)
                    else:
                        serialized[key].append(node)
            else:
                serialized[key] = value
        
        # Ensure critical fields are set
        serialized['user_id'] = chat_id
        serialized['phone_number'] = chat_id
        serialized['platform'] = 'telegram'
        serialized['chat_id'] = chat_id
        serialized['conv_id'] = chat_id  # Set conv_id same as chat_id for upserts
        
        return serialized
    return state_dict

async def start(update: Update) -> None:
    """Handle /start command"""
    chat_id = str(update.message.chat_id)
    user = update.message.from_user
    
    # Initialize new state for the user
    initial_state = MwalimuBotState(
        user_id=chat_id,
        phone_number=chat_id,
        user_input="/start",
        conversation_history=[{"role": "human", "content": "/start"}],
        current_subject=None,
        current_grade=2,
        rag_context=None,
        node_history=[],
        ready_for_tutoring=False,
        ready_for_quiz=False,
        first_node="router_agent",
        current_step="router_agent",
        response_to_user_attempts=0,
        tavily_results=None,
        tavily_attempts=0,
        message_to_user=None,
        message_to_student=None,
        chat_id=chat_id,
        platform="telegram",
        user_name=user.first_name if user.first_name else "Student"
    )
    
    # Save initial state
    save_conversation(serialize_state(initial_state.model_dump(), chat_id))
    
    welcome_message = (
        f"👋 Hello {initial_state.user_name}! Karibu sana! I am MwalimuBot, your personal tutor. "
        "I'm here to help you learn and practice various subjects.\n\n"
        "What would you like to learn today?"
    )
    await update.message.reply_text(welcome_message)

async def handle_exit(update: Update) -> None:
    """Handle /exit command"""
    chat_id = str(update.message.chat_id)
    save_conversation(serialize_state(None, chat_id))
    await update.message.reply_text("Kwaheri! Thank you for using MwalimuBot! Have a great day!")

async def handle_message(update: Update) -> None:
    """Handle incoming messages"""
    if update.message is None:
        return

    user_message = update.message.text
    chat_id = str(update.message.chat_id)
    user = update.message.from_user
    
    # Try to load existing conversation
    existing_state = load_conversation(chat_id)
    
    if existing_state:
        # Ensure all required fields are present
        existing_state.update({
            'user_input': user_message,
            'first_node': 'router_agent',
            'user_id': chat_id,
            'phone_number': chat_id,
            'conversation_history': existing_state.get('conversation_history', []) + [{"role": "human", "content": user_message}],
            'current_subject': existing_state.get('current_subject'),
            'current_grade': existing_state.get('current_grade', 2),
            'rag_context': existing_state.get('rag_context'),
            'node_history': existing_state.get('node_history', []),
            'ready_for_tutoring': existing_state.get('ready_for_tutoring', False),
            'ready_for_quiz': existing_state.get('ready_for_quiz', False),
            'handoff_agents': existing_state.get('handoff_agents', []),
            'handoff_agents_params': existing_state.get('handoff_agents_params', []),
            'router_attempts': existing_state.get('router_attempts', 0),
            'tutor_attempts': existing_state.get('tutor_attempts', 0),
            'error_message': None,
            'current_step': 'router_agent',
            'response_to_user_attempts': existing_state.get('response_to_user_attempts', 0),
            'tavily_results': existing_state.get('tavily_results'),
            'tavily_attempts': existing_state.get('tavily_attempts', 0),
            'message_to_student': None,
            'chat_id': chat_id,
            'platform': 'telegram',
            'user_name': user.first_name if user.first_name else "Student"
        })
        # Create state object with all fields
        state = MwalimuBotState(**existing_state)
        print(f"Loaded existing conversation for user {chat_id}")
    else:
        # Initialize new state with all required fields
        state = MwalimuBotState(
            user_id=chat_id,
            phone_number=chat_id,
            user_input=user_message,
            conversation_history=[{"role": "human", "content": user_message}],
            current_subject=None,
            current_grade=2,
            rag_context=None,
            node_history=[],
            ready_for_tutoring=False,
            ready_for_quiz=False,
            first_node="router_agent",
            current_step="router_agent",
            response_to_user_attempts=0,
            tavily_results=None,
            tavily_attempts=0,
            message_to_user=None,
            message_to_student=None,
            chat_id=chat_id,
            platform="telegram",
            user_name=user.first_name if user.first_name else "Student||uuid"
        )
        print(f"Created new conversation for user {chat_id}")
    
    try:
        # Use the graph to manage the flow
        final_state = await mw_graph.ainvoke(state.model_dump())
        # Extract the response
        response = final_state.get("message_to_student") or final_state.get("message_to_user")
        if not response:
            response = "I'm thinking about your message..."
        # Add bot's response to conversation history before saving
        final_state["conversation_history"].append({
            "role": "assistant",
            "content": response
        })
        save_conversation(serialize_state(final_state, chat_id))
        await update.message.reply_text(response)
    except Exception as e:
        error_message = "I encountered an error processing your request. Please try again."
        await update.message.reply_text(error_message)
        print(f"Error processing message: {str(e)}")

@app.post("/telegram-webhook")
async def telegram_webhook(request: Request) -> Response:
    """Handle incoming Telegram webhook requests"""
    try:
        # Get the update data
        data = await request.json()
        update = Update.de_json(data, bot)
        
        if update.message:
            if update.message.text == '/start':
                await start(update)
            elif update.message.text == '/exit':
                await handle_exit(update)
            else:
                await handle_message(update)
                
        return Response(status_code=200)
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return Response(status_code=500) 