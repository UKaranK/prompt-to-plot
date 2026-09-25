from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

from backend.security.hooks import sanitize_prompt, validate_sql, validate_tool_output, SecurityViolation
from backend.agent.tools import (
    semantic_lookup, 
    query_generate, 
    data_retrieve, 
    viz_select, 
    insight_generate
)
from backend.llm.gemini import LLMClient

# 1. Define the Typed State
class AgentState(TypedDict, total=False):
    user_prompt: str
    intent: str
    dimensions: List[str]
    measures: List[str]
    filters: List[str]
    semantic_mapping: str
    generated_sql: str
    sql_validation: str
    sql_retries: int
    query_result: List[Dict[str, Any]]
    visualization: Dict[str, Any]
    insights: str
    errors: str
    status: str

# 2. Define the Nodes
def validate_input_node(state: AgentState):
    try:
        clean_prompt = sanitize_prompt(state.get("user_prompt", ""))
        return {"user_prompt": clean_prompt, "status": "input_validated"}
    except SecurityViolation as e:
        return {"errors": str(e), "status": "failed"}

def understand_intent_node(state: AgentState):
    # Simple extraction for MVP to populate dimensions/measures to search
    client = LLMClient()
    prompt = f"Extract the key business entities (dimensions and measures) from this request: '{state['user_prompt']}'. Return a comma-separated list of terms."
    terms = client.generate_response(prompt)
    return {"intent": state["user_prompt"], "dimensions": [terms], "status": "intent_understood"}

def lookup_semantics_node(state: AgentState):
    terms_str = " ".join(state.get("dimensions", []))
    mapping = semantic_lookup(terms_str)
    return {"semantic_mapping": mapping, "status": "semantics_found"}

def generate_sql_node(state: AgentState):
    sql = query_generate(
        intent=state.get("intent", ""), 
        semantic_mapping=state.get("semantic_mapping", ""),
        error_context=state.get("sql_validation", "") if state.get("sql_retries", 0) > 0 else ""
    )
    return {"generated_sql": sql, "status": "sql_generated"}

def validate_and_retrieve_node(state: AgentState):
    sql = state.get("generated_sql", "")
    retries = state.get("sql_retries", 0)
    
    try:
        # Pre-tool hook
        valid_sql = validate_sql(sql)
        
        # Tool execution
        result = data_retrieve(valid_sql)
        if result["status"] == "error":
            raise Exception(result["message"])
            
        # Post-tool hook
        data = result["data"]
        safe_data = validate_tool_output(data)
        
        return {
            "sql_validation": "VALID",
            "query_result": safe_data,
            "status": "data_retrieved",
            "errors": ""
        }
    except Exception as e:
        new_retries = retries + 1
        return {
            "sql_validation": str(e),
            "sql_retries": new_retries,
            "status": "sql_error",
            "errors": str(e)
        }

def select_visualization_node(state: AgentState):
    viz = viz_select(state.get("query_result", []), state.get("intent", ""))
    return {"visualization": viz, "status": "viz_selected"}

def generate_insight_node(state: AgentState):
    # Pass a summary of data to prevent blowing up LLM context if it's large
    data_str = str(state.get("query_result", []))[:2000]
    insight = insight_generate(state.get("intent", ""), data_str)
    return {"insights": insight, "status": "insight_generated"}

# 3. Define Conditional Edges
def should_retry(state: AgentState):
    """Controls the self-correction loop for SQL generation."""
    if state.get("status") == "sql_error":
        if state.get("sql_retries", 0) < 3:
            return "retry"
        return "fail"
    return "continue"

def check_errors(state: AgentState):
    """Halts the graph early if a security hook failed."""
    if state.get("errors"):
        return "fail"
    return "continue"

# 4. Build the LangGraph Workflow
workflow = StateGraph(AgentState)

workflow.add_node("validate_input", validate_input_node)
workflow.add_node("understand_intent", understand_intent_node)
workflow.add_node("lookup_semantics", lookup_semantics_node)
workflow.add_node("generate_sql", generate_sql_node)
workflow.add_node("validate_and_retrieve", validate_and_retrieve_node)
workflow.add_node("select_visualization", select_visualization_node)
workflow.add_node("generate_insight", generate_insight_node)

workflow.set_entry_point("validate_input")

# Route based on input validation
workflow.add_conditional_edges("validate_input", check_errors, {"continue": "understand_intent", "fail": END})
workflow.add_edge("understand_intent", "lookup_semantics")
workflow.add_edge("lookup_semantics", "generate_sql")
workflow.add_edge("generate_sql", "validate_and_retrieve")

# The Retry Loop Edge
workflow.add_conditional_edges(
    "validate_and_retrieve",
    should_retry,
    {
        "continue": "select_visualization",
        "retry": "generate_sql",
        "fail": END
    }
)

workflow.add_edge("select_visualization", "generate_insight")
workflow.add_edge("generate_insight", END)

# Compile into an executable agent
agent_app = workflow.compile()
