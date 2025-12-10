"""
Layer 5: Field Mapping

Applies field transformations and mappings:
- Map source fields to target fields
- Apply transformations (uppercase, lowercase, trim, etc.)
- Handle default values
- Validate required fields
"""

from typing import Any
from loguru import logger


class FieldMappingLayer:
    """
    Layer 5: Field Mapping
    Maps and transforms fields based on configuration
    """

    def __init__(self, mappings: list[dict[str, Any]] | None = None):
        """
        Initialize with field mappings

        Args:
            mappings: List of mapping configurations
                Example:
                [
                    {
                        "source_field": "part_no",
                        "target_field": "item_number",
                        "transformation": "uppercase",
                        "is_required": True
                    },
                    ...
                ]
        """
        self.mappings = mappings or []

        # Build lookup maps for faster access
        self._source_to_target: dict[str, str] = {}
        self._transformations: dict[str, str] = {}
        self._default_values: dict[str, Any] = {}
        self._required_fields: set[str] = set()

        for mapping in self.mappings:
            source = mapping.get("source_field")
            target = mapping.get("target_field")

            if source and target:
                self._source_to_target[source] = target

                if "transformation" in mapping and mapping["transformation"]:
                    self._transformations[source] = mapping["transformation"]

                if "default_value" in mapping and mapping["default_value"]:
                    self._default_values[source] = mapping["default_value"]

                if mapping.get("is_required", False):
                    self._required_fields.add(source)

    @staticmethod
    def apply_transformation(value: Any, transformation: str) -> Any:
        """
        Apply a transformation to a value

        Args:
            value: Value to transform
            transformation: Transformation name

        Returns:
            Transformed value
        """
        if value is None:
            return None

        try:
            if transformation == "uppercase":
                return str(value).upper()

            elif transformation == "lowercase":
                return str(value).lower()

            elif transformation == "trim":
                return str(value).strip()

            elif transformation == "title_case":
                return str(value).title()

            elif transformation == "capitalize":
                return str(value).capitalize()

            elif transformation == "strip_whitespace":
                # Remove ALL whitespace
                return ''.join(str(value).split())

            elif transformation == "remove_special_chars":
                # Keep only alphanumeric and spaces
                import re
                return re.sub(r'[^a-zA-Z0-9\s]', '', str(value))

            elif transformation == "none" or transformation == "":
                return value

            else:
                logger.warning(f"Unknown transformation: {transformation}")
                return value

        except Exception as e:
            logger.error(f"Transformation '{transformation}' failed for value '{value}': {e}")
            return value

    def map_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Map and transform fields in a row

        Args:
            row: Source row

        Returns:
            Mapped row with target field names
        """
        mapped = {}

        # Apply mappings
        for source_field, source_value in row.items():
            # Get target field name (or keep source name if no mapping)
            target_field = self._source_to_target.get(source_field, source_field)

            # Apply transformation if configured
            if source_field in self._transformations:
                transformation = self._transformations[source_field]
                source_value = self.apply_transformation(source_value, transformation)

            # Apply default value if NULL and default is configured
            if source_value is None and source_field in self._default_values:
                source_value = self._default_values[source_field]

            mapped[target_field] = source_value

        # Validate required fields
        for required_field in self._required_fields:
            target_field = self._source_to_target.get(required_field, required_field)
            if target_field not in mapped or mapped[target_field] is None:
                logger.warning(f"Required field '{required_field}' (mapped to '{target_field}') is missing or NULL")
                # Could raise exception here if strict validation needed

        return mapped

    def map_batch(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Map a batch of rows

        Args:
            rows: List of source rows

        Returns:
            List of mapped rows
        """
        return [self.map_row(row) for row in rows]

    def validate_row(self, row: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate a row against mapping requirements

        Args:
            row: Row to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        for required_field in self._required_fields:
            target_field = self._source_to_target.get(required_field, required_field)
            if target_field not in row or row[target_field] is None:
                errors.append(f"Required field '{required_field}' is missing or NULL")

        is_valid = len(errors) == 0
        return is_valid, errors
