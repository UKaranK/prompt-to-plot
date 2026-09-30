from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
from backend.config import settings
from backend.agent.graph import agent_app
from backend.agent.context import AgentJournal

app = FastAPI(
    title="Prompt to Plot API",
    description="Backend for the Prompt to Plot agentic BI system.",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    prompt: str
    session_id: str = None  # Optional: client can pass a session_id to resume a crashed session


@app.post("/query")
async def run_query(request: QueryRequest):
    """Executes the full LangGraph agent workflow for a given prompt."""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        journal = AgentJournal(session_id=session_id)

        # Session recovery: rehydrate from last checkpoint if available
        recovered_state = journal.rehydrate_state()
        if recovered_state:
            initial_state = recovered_state
            initial_state["_session_id"] = session_id
        else:
            initial_state = {
                "_session_id": session_id,
                "user_prompt": request.prompt,
                "sql_retries": 0,
                "errors": ""
            }

        final_merged_state = initial_state.copy()

        for s in agent_app.stream(initial_state):
            node_name = list(s.keys())[0]
            state_data = s[node_name]
            final_merged_state.update(state_data)
            # Write checkpoint after every node for session recovery
            journal.checkpoint(final_merged_state)

        # Save human-readable trace via AgentTrace (carried in state)
        trace = final_merged_state.get("trace")
        if trace:
            trace.save(final_merged_state)

        # Clear checkpoint on successful completion
        journal.clear_checkpoint()

        return {
            "status": final_merged_state.get("status", "unknown"),
            "visualization": final_merged_state.get("visualization", {}),
            "insights": final_merged_state.get("insights", {}),
            "generated_sql": final_merged_state.get("generated_sql", ""),
            "errors": final_merged_state.get("errors", ""),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Prompt to Plot"}


# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
