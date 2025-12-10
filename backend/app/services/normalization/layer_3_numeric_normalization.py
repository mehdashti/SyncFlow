"""
Layer 3: Numeric Normalization

Handles numeric parsing and validation:
- Parse "10,000" → 10000
- Handle scientific notation
- Validate numeric ranges
- Null-safe parsing
"""

from typing import Any
from decimal import Decimal, InvalidOperation
from loguru import logger


class NumericNormalizationLayer:
    """
    Layer 3: Numeric Normalization
    Parses and validates numeric values
    """

    @staticmethod
    def normalize_numeric(value: Any) -> int | float | Decimal | None:
        """
        Normalize a numeric value

        Args:
            value: Value to normalize

        Returns:
            Normalized number or None
        """
        if value is None:
            return None

        # Already a number
        if isinstance(value, (int, float, Decimal)):
            return value

        # Parse from string
        if isinstance(value, str):
            value = value.strip()

            # Empty string → None
            if not value:
                return None

            try:
                # Remove thousand separators (commas)
                # Examples: "1,000" → "1000", "1,234,567.89" → "1234567.89"
                value = value.replace(',', '')

                # Remove currency symbols if present
                value = value.replace('$', '').replace('€', '').replace('£', '').strip()

                # Handle parentheses as negative (accounting format)
                if value.startswith('(') and value.endswith(')'):
                    value = '-' + value[1:-1]

                # Try parsing
                if '.' in value or 'e' in value.lower():
                    # Float or scientific notation
                    num = float(value)
                    # Return int if it's a whole number
                    if num.is_integer():
                        return int(num)
                    return num
                else:
                    # Integer
                    return int(value)

            except (ValueError, InvalidOperation) as e:
                logger.warning(f"Cannot parse numeric value '{value}': {e}")
                return None

        # Unknown type
        logger.warning(f"Unknown numeric type: {type(value)}")
        return None

    @staticmethod
    def validate_range(
        value: int | float | Decimal | None,
        min_value: int | float | None = None,
        max_value: int | float | None = None
    ) -> bool:
        """
        Validate numeric value is within range

        Args:
            value: Value to validate
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # NULL is valid

        if min_value is not None and value < min_value:
            return False

        if max_value is not None and value > max_value:
            return False

        return True

    def normalize_row(
        self,
        row: dict[str, Any],
        numeric_fields: set[str] | None = None
    ) -> dict[str, Any]:
        """
        Normalize numeric fields in a row

        Args:
            row: Row with mixed types
            numeric_fields: Set of field names that are numeric (optional)

        Returns:
            Row with normalized numerics
        """
        if numeric_fields is None:
            # Auto-detect: normalize all values that look numeric
            numeric_fields = set()

        normalized = {}

        for field_name, field_value in row.items():
            if field_name in numeric_fields or isinstance(field_value, (int, float, Decimal)):
                normalized[field_name] = self.normalize_numeric(field_value)
            elif isinstance(field_value, str) and field_value.strip().replace(',', '').replace('.', '').replace('-', '').isdigit():
                # Auto-detect: string looks like a number
                normalized[field_name] = self.normalize_numeric(field_value)
            else:
                normalized[field_name] = field_value

        return normalized

    def normalize_batch(
        self,
        rows: list[dict[str, Any]],
        numeric_fields: set[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Normalize a batch of rows

        Args:
            rows: List of rows
            numeric_fields: Set of field names that are numeric (optional)

        Returns:
            List of normalized rows
        """
        return [self.normalize_row(row, numeric_fields) for row in rows]
