import pandas as pd
import plotly.express as px
from typing import Dict, Any, List
import json

def select_visualization(intent_data: Dict[str, Any], data_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Deterministically selects the best visualization based on the data shape,
    and uses Plotly to generate the chart representation.
    """
    if not data_records:
        return {"chart_type": "table", "plotly_json": None, "columns": []}

    df = pd.DataFrame(data_records)
    keys = list(df.columns)
    num_cols = len(keys)
    num_rows = len(df)
    
    intent = intent_data.get("intent", "").lower()
    
    fig = None
    chart_type = "table"

    # 1. Single KPI
    if num_rows == 1 and num_cols == 1:
        chart_type = "kpi"
        import plotly.graph_objects as go
        val = df.iloc[0, 0]
        fig = go.Figure(go.Indicator(
            mode = "number",
            value = val,
            title = {"text": keys[0]}
        ))

    # 2. Ranking or Category Comparison (2 columns)
    elif num_cols == 2:
        col1, col2 = keys[0], keys[1]
        
        # Check if one is a time dimension
        time_keywords = ['date', 'time', 'month', 'year', 'day']
        is_time = any(t in col1.lower() for t in time_keywords) or any(t in col2.lower() for t in time_keywords)
        
        if is_time or "trend" in intent:
            chart_type = "line"
            x_col = col1 if any(t in col1.lower() for t in time_keywords) else col2
            y_col = col2 if x_col == col1 else col1
            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
        else:
            chart_type = "bar"
            # Attempt to guess numeric column for y-axis
            numeric_cols = df.select_dtypes(include='number').columns
            if len(numeric_cols) > 0:
                y_col = numeric_cols[0]
                x_col = col1 if y_col == col2 else col2
            else:
                x_col, y_col = col1, col2
            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")

    # 3. Relationship (Scatter) (3+ columns)
    elif num_cols >= 3 and ("relationship" in intent or "scatter" in intent):
        chart_type = "scatter"
        numeric_cols = df.select_dtypes(include='number').columns
        if len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            color_col = keys[0] if keys[0] not in [x_col, y_col] else keys[2]
            fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=f"Scatter of {y_col} vs {x_col}")
        else:
            chart_type = "table"

    # Default fallback is Table (no Plotly figure)
    
    result = {
        "chart_type": chart_type,
        "columns": keys,
        "plotly_json": json.loads(fig.to_json()) if fig else None
    }
    
    return result
