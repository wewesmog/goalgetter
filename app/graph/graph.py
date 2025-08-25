"""
Graph Builder Module for No Frameworks
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, START, END

from app.models.pydantic_models import GoalGetterState

#Nodes
from app.agents.router_agent import router_node


# """ 
# Graph will use a routing node to determine the first Node.
# Subsequent nodes will be determined by the handoff parameters.
# Always Ends with respond_to_user node.
# """
# def first_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Routing node to determine the first Node.
#     1. If Node_history is empty, start with welcome node.
#     2. If Node_history is not empty, check the last 'response_to_user' node in the node_history.
#     3. In the last 'response_to_user' node, check the agent_after_response field.
#       "check if the agent_after_response is a valid agent name i.e "question_generator" or "respond_to_user" or "quiz_validation"
#       if it is, return the agent_after_response node.
#       if it is not, go to step 4 which is to check the current_step field.
#     4. In the current_step field, check if it is "welcome" or "question_generator" or "quiz_validation"
#       if it is "welcome", return the welcome node.
#       if it is "question_generator", return the question_generator node.
#       if it is "quiz_validation", return the quiz_validation node.
#       if it is not, return the welcome node.
#       The routing node will be used to determine the 'first_node' field in the state.
    
    
#     """
#     current_state = state if isinstance(state, MwalimuBotState) else MwalimuBotState(**state)
#     state.first_node = ""
#     if not current_state.node_history:
#         state.first_node = "routing_agent"
#     else:
#         # Get the last Respond_to_user node
#         for node in reversed(current_state.node_history):
#             if node["node_name"] == "respond_to_user":
#                 if node["agent_after_response"] in ["routing_agent", "tutor_agent"]:
#                     state.first_node = node["agent_after_response"]
#                 else:
#                     state.first_node = "routing_agent"
#         # If no respond_to_user node is found, check the current_step field.
#         if current_state.current_step == "routing_agent":
#             state.first_node = "routing_agent"
#         elif current_state.current_step == "tutor_agent":
#             state.first_node = "tutor_agent"
#         elif current_state.current_step == "tavily_agent":
#             state.first_node = "tavily_agent"
#         else:
#             state.first_node = "tutor_agent"
#     return state




# def routing_from_first_node(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Routing decision node to determine the next node."""
#     current_state = state if isinstance(state, MwalimuBotState) else MwalimuBotState(**state)
#     handoff_agents = current_state.handoff_agents
#     return current_state.first_node

# def routing_after_routing_agent(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Routing decision node to determine the next node."""
#     current_state = state if isinstance(state, MwalimuBotState) else MwalimuBotState(**state)
#     handoff_agents = current_state.handoff_agents
#     if handoff_agents:
#         return handoff_agents[0]
#     else:
#         return "end"
    
# def routing_after_tutor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
#     """Routing decision node to determine the next node."""
#     current_state = state if isinstance(state, MwalimuBotState) else MwalimuBotState(**state)
#     handoff_agents = current_state.handoff_agents
#     if handoff_agents:
#         return handoff_agents[0]
#     else:
#         return "end"
    

    
    

def build_graph(state: Dict[str, Any] = None) -> StateGraph:
    """Build the GoalGetter workflow graph."""
    #--- Start with the welcome node ---
    workflow = StateGraph(GoalGetterState)
    workflow.add_node("routing_agent", router_node)

    #--- Add edges ---
    workflow.add_edge(START, "routing_agent")
    workflow.add_edge("routing_agent", END)

    return workflow
