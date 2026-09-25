import re
import logging

logger = logging.getLogger(__name__)

class SecurityViolation(Exception):
    """Raised when a security hook blocks a potentially malicious action."""
    pass

def sanitize_prompt(prompt: str) -> str:
    """
    PRE-MODEL HOOK
    Detects common prompt injection patterns before they reach the LLM.
    """
    if not prompt or not prompt.strip():
        raise SecurityViolation("Prompt cannot be empty.")

    prompt_lower = prompt.lower()
    
    # List of known malicious intent patterns
    injection_patterns = [
        "ignore previous",
        "disregard previous",
        "system prompt",
        "you are a",
        "forget all",
        "bypass",
        "sudo"
    ]
    
    for pattern in injection_patterns:
        if pattern in prompt_lower:
            logger.warning(f"Prompt injection detected using pattern: '{pattern}'")
            raise SecurityViolation("Malicious input detected. Request blocked.")
            
    return prompt

def validate_sql(sql: str) -> str:
    """
    PRE-TOOL HOOK
    Validates SQL queries before they hit the database.
    Only allows SELECT statements and strictly blocks destructive keywords.
    """
    sql_clean = sql.strip()
    sql_upper = sql_clean.upper()

    if not sql_upper.startswith("SELECT"):
        raise SecurityViolation("Only SELECT queries are allowed. Query must start with SELECT.")

    # A comprehensive list of operations that alter schema or data
    forbidden_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE",
        "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "MERGE"
    ]
    
    for keyword in forbidden_keywords:
        # Regex \b matches word boundaries, so a column named "drop_off" is perfectly safe.
        if re.search(rf"\b{keyword}\b", sql_upper):
            logger.warning(f"Blocked destructive SQL attempt: {sql_clean}")
            raise SecurityViolation(f"Query contains forbidden keyword: '{keyword}'. Only read operations are permitted.")
            
    return sql_clean

def validate_tool_output(data: list, max_rows: int = 100) -> list:
    """
    POST-TOOL HOOK
    Ensures returned data is properly structured and doesn't exceed the LLM's context window.
    """
    if not isinstance(data, list):
        raise ValueError("Data must be a list of records.")
        
    if len(data) > max_rows:
        logger.warning(f"Query returned {len(data)} rows. Truncating to {max_rows} to protect agent context window.")
        return data[:max_rows]
        
    return data
