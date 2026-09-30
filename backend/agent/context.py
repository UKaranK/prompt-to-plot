import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "traces")
STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs", "state")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(STATE_DIR, exist_ok=True)


def _sanitize(state: Dict[str, Any]) -> Dict[str, Any]:
    """Strips raw data payloads and secrets before persisting."""
    clean = state.copy()
    if "query_result" in clean and isinstance(clean["query_result"], list):
        clean["query_result_metadata"] = {"rows_returned": len(clean["query_result"])}
        del clean["query_result"]
    clean.pop("api_key", None)
    clean.pop("gemini_api_key", None)
    clean.pop("trace", None)
    return clean


class AgentJournal:
    """
    Machine-readable journal for durable execution and session recovery.
    Writes a checkpoint after every node so a crashed session can resume.
    """
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self._state_path = os.path.join(STATE_DIR, f"state_{self.session_id}.json")

    def checkpoint(self, state: Dict[str, Any]):
        """Writes current state to disk after every node step."""
        data = {
            "session_id": self.session_id,
            "checkpoint_time": datetime.now(timezone.utc).isoformat(),
            "state": _sanitize(state)
        }
        with open(self._state_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def rehydrate_state(self) -> Optional[Dict[str, Any]]:
        """
        Reads the last checkpoint from disk.
        Returns saved state if it exists, None if starting fresh.
        """
        if not os.path.exists(self._state_path):
            return None
        with open(self._state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("state")

    def clear_checkpoint(self):
        """Removes the state file once the session completes successfully."""
        if os.path.exists(self._state_path):
            os.remove(self._state_path)


class AgentTrace:
    """
    Human-readable trace for observability and debugging.
    Records every tool call, hook decision, retry, and timestamp throughout the run.
    Kept separate from AgentJournal — traces are for humans, journals are for machines.
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self._events: List[Dict[str, Any]] = []

    def log_event(
        self,
        step: str,
        tool_called: Optional[str] = None,
        tool_arguments: Optional[Dict] = None,
        tool_result: Optional[Any] = None,
        hook_decision: Optional[str] = None,
        retry_count: int = 0,
        status: str = "success",
        error: Optional[str] = None,
    ):
        """Records a single step event with full context."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "status": status,
            "retry_count": retry_count,
        }
        if tool_called:
            event["tool_called"] = tool_called
        if tool_arguments:
            event["tool_arguments"] = tool_arguments
        if tool_result is not None:
            event["tool_result"] = tool_result
        if hook_decision:
            event["hook_decision"] = hook_decision
        if error:
            event["error"] = error
        self._events.append(event)

    def save(self, final_state: Dict[str, Any]) -> str:
        """Writes the complete trace to a permanent JSON file."""
        trace = {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "final_status": final_state.get("status"),
            "sql_retries": final_state.get("sql_retries", 0),
            "generated_sql": final_state.get("generated_sql"),
            "errors": final_state.get("errors"),
            "events": self._events,
            "final_state_summary": _sanitize(final_state),
        }
        filepath = os.path.join(LOGS_DIR, f"trace_{self.session_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=4)
        return filepath
