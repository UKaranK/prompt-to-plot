import pytest
from backend.agent.visualization import select_visualization

def test_kpi_selection():
    data = [{"total_revenue": 1000}]
    intent = {"intent": "What is total revenue?"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "kpi"
    assert viz["plotly_json"] is not None

def test_bar_chart_selection():
    data = [
        {"region": "North", "revenue": 1000},
        {"region": "South", "revenue": 2000}
    ]
    intent = {"intent": "Rank by region"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "bar"
    assert viz["plotly_json"] is not None
    assert "data" in viz["plotly_json"]

def test_line_chart_selection():
    data = [
        {"month": "Jan", "revenue": 1000},
        {"month": "Feb", "revenue": 1500}
    ]
    intent = {"intent": "Show trend over time"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "line"
    assert viz["plotly_json"] is not None

def test_scatter_selection():
    data = [
        {"marketing_spend": 100, "revenue": 500, "region": "North"},
        {"marketing_spend": 200, "revenue": 1000, "region": "South"}
    ]
    intent = {"intent": "What is the relationship between spend and revenue"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "scatter"
    assert viz["plotly_json"] is not None

def test_table_fallback():
    data = [
        {"col1": 1, "col2": 2, "col3": 3, "col4": 4},
        {"col1": 5, "col2": 6, "col3": 7, "col4": 8}
    ]
    intent = {"intent": "Give me everything"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "table"
    assert "columns" in viz

def test_empty_data_returns_empty_chart():
    """Test that empty query results return the empty chart type with a message."""
    viz = select_visualization({"intent": "anything"}, [])
    assert viz["chart_type"] == "empty"
    assert "message" in viz
    assert viz["plotly_json"] is None

def test_donut_chart_selection():
    """Test that part-to-whole intent triggers a donut chart."""
    data = [
        {"region": "North", "revenue": 1000},
        {"region": "South", "revenue": 2000}
    ]
    intent = {"intent": "Show revenue breakdown by region"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "donut"
    assert viz["plotly_json"] is not None

def test_multi_kpi_selection():
    """Test that a single row with multiple numeric columns renders as multi-KPI."""
    data = [{"total_revenue": 5000, "total_units": 200}]
    intent = {"intent": "Show overall KPIs"}
    viz = select_visualization(intent, data)
    assert viz["chart_type"] == "multi_kpi"
    assert viz["plotly_json"] is not None
