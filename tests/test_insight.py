import pytest
from backend.agent.insight import verify_grounding

def test_grounded_insight():
    """Test that an insight quoting exact numbers from the data passes."""
    data = '[{"region": "North", "revenue": 520}]'
    fact = "Region North generated 520 in revenue."
    assert verify_grounding(fact, data) is True

def test_ungrounded_insight_calculation():
    """Test that if the LLM calculates a total not in the data, it fails."""
    data = '[{"region": "North", "revenue": 520}, {"region": "South", "revenue": 100}]'
    # 620 is a calculation (520+100), not explicitly in the data
    fact = "The total revenue across regions is 620."
    assert verify_grounding(fact, data) is False

def test_ungrounded_insight_percentage():
    """Test that if the LLM calculates a percentage, it fails."""
    data = '[{"region": "North", "revenue": 500}, {"region": "South", "revenue": 500}]'
    # 50 is a percentage not present in the raw data string
    fact = "North accounts for 50 percent of the revenue."
    assert verify_grounding(fact, data) is False

def test_grounded_insight_with_commas():
    """Test that our regex handles basic comma stripping."""
    data = '[{"region": "North", "revenue": 520000}]'
    # The LLM output a comma, but our code strips it to verify against the raw data
    fact = "Region North generated 520,000 in revenue."
    assert verify_grounding(fact, data) is True
