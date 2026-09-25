from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from backend.config import settings
from backend.agent.graph import agent_app
from backend.agent.context import AgentJournal

app = FastAPI(
    title="Prompt to Plot API",
    description="Backend for the Prompt to Plot agentic BI system.",
    version="0.1.0"
)

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    prompt: str

@app.post("/query")
async def run_query(request: QueryRequest):
    """Executes the full LangGraph agent workflow for a given prompt."""
    try:
        initial_state = {
            "user_prompt": request.prompt,
            "sql_retries": 0,
            "errors": ""
        }
        
        final_merged_state = initial_state.copy()
        
        # Execute the agent and stream updates to build final state
        for s in agent_app.stream(initial_state):
            node_name = list(s.keys())[0]
            state_data = s[node_name]
            final_merged_state.update(state_data)
            
        # Log trace securely
        journal = AgentJournal()
        journal.save_trace(final_merged_state)
        
        return {
            "status": final_merged_state.get("status", "unknown"),
            "visualization": final_merged_state.get("visualization", {}),
            "insights": final_merged_state.get("insights", {}),
            "generated_sql": final_merged_state.get("generated_sql", ""),
            "errors": final_merged_state.get("errors", "")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "Prompt to Plot"}

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
