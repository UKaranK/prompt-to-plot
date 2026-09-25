import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict

# Ensure a logs/traces directory exists
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "traces")
os.makedirs(LOGS_DIR, exist_ok=True)

class AgentJournal:
    """
    Acts as a flight data recorder for the LangGraph agent.
    Captures state transitions and saves a structured JSON trace.
    """
    def __init__(self):
        self.trace_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        
    def sanitize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cleans the state before logging.
        Strips out massive data arrays and ensures no secrets leak.
        """
        clean_state = state.copy()
        
        # NEVER log the raw data to the journal, only metadata
        if "query_result" in clean_state and isinstance(clean_state["query_result"], list):
            clean_state["query_result_metadata"] = {
                "rows_returned": len(clean_state["query_result"])
            }
            del clean_state["query_result"] # Remove actual data payload
            
        # Ensure no accidental env vars or keys get dumped
        clean_state.pop("api_key", None)
        
        return clean_state

    def save_trace(self, final_state: Dict[str, Any]) -> str:
        """
        Writes the final sanitized state to a JSON file.
        """
        safe_state = self.sanitize_state(final_state)
        
        trace = {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "execution_journal": safe_state
        }
        
        filepath = os.path.join(LOGS_DIR, f"trace_{self.trace_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=4)
            
        return filepath
