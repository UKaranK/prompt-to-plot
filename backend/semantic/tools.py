import json
from backend.semantic.model import semantic_model


def semantic_lookup(search_term: str) -> str:
    """
    Looks up a business term in the semantic model.
    Returns matched columns, relevant KPI definitions, and date filter SQL snippets.
    """
    terms = [t.strip().lower() for t in search_term.replace(',', ' ').split() if t.strip()]
    schema = semantic_model.get_full_schema()
    matches = []

    for table_name, table_info in schema.get("tables", {}).items():
        for col_name, col_info in table_info.get("columns", {}).items():
            is_match = any(
                term in col_name.lower()
                or term in [s.lower() for s in col_info.get("synonyms", [])]
                or term in col_info.get("description", "").lower()
                for term in terms
            )
            if is_match:
                match_data = {
                    "table": table_name,
                    "column": col_name,
                    "role": col_info.get("role"),
                    "type": col_info.get("type"),
                    "description": col_info.get("description"),
                    "annotation": "read-only"
                }
                if "allowed_aggregations" in col_info:
                    match_data["allowed_aggregations"] = col_info["allowed_aggregations"]
                matches.append(match_data)

    # Include relevant KPI definitions
    kpi_matches = []
    for kpi_name, kpi_info in schema.get("kpis", {}).items():
        if any(term in kpi_name or term in kpi_info.get("description", "").lower() for term in terms):
            kpi_matches.append({"kpi": kpi_name, **kpi_info})

    # Always include date filter hints so LLM can handle time-based queries
    date_filters = schema.get("date_filters", {})

    if not matches and not kpi_matches:
        return (
            f"No semantic matches found for '{search_term}'. "
            f"Available columns: date, region, account, product, revenue, units. "
            f"Try rephrasing using these terms."
        )

    return json.dumps({
        "search_term": search_term,
        "matches": matches,
        "kpi_definitions": kpi_matches,
        "date_filter_hints": date_filters
    }, indent=2)
