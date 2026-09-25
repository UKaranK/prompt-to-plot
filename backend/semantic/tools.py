import json
from backend.semantic.model import semantic_model

def semantic_lookup(search_term: str) -> str:
    """
    Looks up a business term in the semantic model to find relevant tables, columns, and allowed aggregations.
    Returns a string containing the matching schema metadata (JSON formatted for LLM consumption).
    
    Args:
        search_term: The business term to search for (e.g., "sales", "client", "month").
    """
    # Split the search_term by commas or spaces into individual terms
    terms = [t.strip().lower() for t in search_term.replace(',', ' ').split() if t.strip()]
    
    schema = semantic_model.get_full_schema()
    matches = []
    
    # Iterate through tables and columns to find matching terms in names, descriptions, or synonyms
    for table_name, table_info in schema.get("tables", {}).items():
        for col_name, col_info in table_info.get("columns", {}).items():
            
            is_match = False
            
            for term in terms:
                # 1. Check if search term is in column name
                if term in col_name.lower():
                    is_match = True
                    
                # 2. Check if search term is in synonyms
                synonyms = [s.lower() for s in col_info.get("synonyms", [])]
                if term in synonyms:
                    is_match = True
                    
                # 3. Check if search term is in description
                if term in col_info.get("description", "").lower():
                    is_match = True
                
            if is_match:
                match_data = {
                    "table": table_name,
                    "column": col_name,
                    "role": col_info.get("role"),
                    "type": col_info.get("type"),
                    "description": col_info.get("description"),
                }
                
                # Measures will have specific allowed math operations
                if "allowed_aggregations" in col_info:
                    match_data["allowed_aggregations"] = col_info["allowed_aggregations"]
                    
                matches.append(match_data)
                
    if not matches:
        return f"No semantic matches found for '{search_term}'. Try using different business terminology."
        
    # We return a JSON string so the Agent can easily parse it
    return json.dumps({"search_term": search_term, "matches": matches}, indent=2)
