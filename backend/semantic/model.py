import json
import os
import logging

logger = logging.getLogger(__name__)

class SemanticModel:
    """
    Loads and holds the semantic schema defining business terms, dimensions, 
    and measures mapped to the underlying database tables.
    """
    def __init__(self):
        # Locate the schema.json file relative to this script
        current_dir = os.path.dirname(__file__)
        self.schema_path = os.path.join(current_dir, "schema.json")
        self.schema = self._load_schema()

    def _load_schema(self) -> dict:
        if not os.path.exists(self.schema_path):
            logger.error(f"Semantic schema not found at {self.schema_path}")
            return {}
        try:
            with open(self.schema_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse semantic schema JSON: {e}")
            return {}

    def get_full_schema(self) -> dict:
        """Returns the entire semantic schema."""
        return self.schema

# A global instance to be imported by the tools module
semantic_model = SemanticModel()
