import re
import json
import logging
from backend.llm.gemini import LLMClient

logger = logging.getLogger(__name__)

class UngroundedInsightError(Exception):
    """Raised when an insight contains hallucinations or ungrounded data."""
    pass

def verify_grounding(generated_text: str, source_data: str) -> bool:
    """
    Deterministically checks if every numeric value in the generated text 
    actually exists in the source data.
    """
    if not generated_text:
        return True
        
    # Remove commas to normalize large numbers (e.g., 1,000 -> 1000)
    clean_text = generated_text.replace(",", "")
    clean_source = source_data.replace(",", "")
    
    # Extract all standalone numbers (integers or decimals)
    numbers_in_text = re.findall(r'\b\d+\.?\d*\b', clean_text)
    
    for num in numbers_in_text:
        # We must use regex to ensure the exact number exists as a standalone token in the source data.
        # Otherwise, "50" (hallucinated percent) would pass if the data contained "500".
        if not re.search(rf'\b{re.escape(num)}\b', clean_source):
            logger.warning(f"Ungrounded number detected: {num}")
            return False
            
    return True

def generate_structured_insight(intent: str, data_summary: str) -> dict:
    client = LLMClient()
    
    prompt = f"""
    You are a precise data analyst. Based on the user's intent and the data provided, 
    generate a 3-part structured analysis.
    
    CRITICAL RULES:
    1. DO NOT invent, calculate, or hallucinate any numbers.
    2. DO NOT calculate percentages, sums, or averages if they are not explicitly present in the Data Summary.
    3. ONLY use numbers that appear exactly in the Data Summary.
    
    User Intent: {intent}
    Data Summary: {data_summary}
    
    Return EXACTLY a JSON object with this format (no markdown, no backticks, no markdown blocks):
    {{
        "fact": "What the data directly shows.",
        "insight": "What can reasonably be interpreted from that data.",
        "action": "A possible next step based on the observed pattern."
    }}
    """
    
    try:
        response = client.generate_response(prompt)
        
        # Strip markdown if the LLM stubbornly wraps the JSON
        clean_resp = response.strip()
        if clean_resp.startswith("```json"):
            clean_resp = clean_resp[7:]
        elif clean_resp.startswith("```"):
            clean_resp = clean_resp[3:]
        if clean_resp.endswith("```"):
            clean_resp = clean_resp[:-3]
            
        result = json.loads(clean_resp.strip())
        
        # We apply the grounding check on the FACT and INSIGHT.
        # Action is exempt as it usually doesn't contain numbers from the data, but if it does, it's safer to check it too.
        combined_text = f"{result.get('fact', '')} {result.get('insight', '')}"
        if not verify_grounding(combined_text, data_summary):
            raise UngroundedInsightError("The insight contains ungrounded numeric values or illicit calculations.")
            
        return result
        
    except UngroundedInsightError as e:
        logger.error(str(e))
        return {
            "fact": "The data returned valid results, but the automated insight was flagged for containing ungrounded numbers.",
            "insight": "The LLM attempted to calculate or hallucinate data that wasn't strictly returned by DuckDB.",
            "action": "Review the raw data visually in the chart or table."
        }
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse insight JSON: {e}")
        return {
            "fact": "Data retrieved successfully.",
            "insight": "Unable to generate formatted insight.",
            "action": "Review the raw data visually."
        }
    except Exception as e:
        logger.error(f"Insight Generation Error: {e}")
        return {
            "fact": "An error occurred.",
            "insight": "API failed.",
            "action": "Try again later."
        }
