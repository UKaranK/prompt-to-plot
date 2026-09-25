from backend.semantic.tools import semantic_lookup as core_semantic_lookup
from backend.data.database import Database
from backend.llm.gemini import LLMClient
import json

def semantic_lookup(search_term: str) -> str:
    """Maps business terms to semantic model fields deterministically."""
    return core_semantic_lookup(search_term)

def query_generate(intent: str, semantic_mapping: str, error_context: str = "") -> str:
    """
    Generates SQL based on the user's intent and semantic information.
    Uses the LLM to write DuckDB compatible SQL.
    """
    client = LLMClient()
    prompt = f"""
    You are a SQL generation assistant for DuckDB.
    User Intent: {intent}
    Semantic Mapping: {semantic_mapping}
    
    Rules:
    - Generate ONLY a valid DuckDB SQL SELECT query. 
    - Do not include markdown formatting (like ```sql).
    - Do not include any explanations.
    """
    if error_context:
        prompt += f"\nYour previous attempt failed with this error: {error_context}\nPlease fix the SQL."
        
    response = client.generate_response(prompt)
    
    # Strip markdown if the LLM stubbornly adds it
    sql = response.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()

def data_retrieve(sql_query: str) -> dict:
    """Executes validated SQL against DuckDB deterministically."""
    db = Database()
    try:
        df = db.execute_query(sql_query)
        # Convert Pandas DataFrame to a clean list of dictionaries for the state
        records = df.to_dict(orient='records')
        return {"status": "success", "data": records}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

def viz_select(data_records: list, intent: str = "") -> dict:
    """
    Determines the appropriate visualization deterministically based on data shape.
    """
    from backend.agent.visualization import select_visualization
    return select_visualization({"intent": intent}, data_records)

def insight_generate(intent: str, data_summary: str) -> dict:
    """Generates a structured, data-grounded insight."""
    from backend.agent.insight import generate_structured_insight
    return generate_structured_insight(intent, data_summary)
