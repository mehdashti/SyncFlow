"""
Layer 1: Type Coercion

Converts Oracle/ERP types to Python native types.
Handles: VARCHAR2, NUMBER, DATE, TIMESTAMP, RAW, etc.
"""

from typing import Any
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from loguru import logger


class TypeCoercionLayer:
    """
    Layer 1: Type Coercion
    Converts Oracle/ERP types to Python native types
    """

    @staticmethod
    def coerce_value(value: Any, oracle_type: str | None = None) -> Any:
        """
        Coerce a single value based on Oracle type

        Args:
            value: Raw value from Oracle
            oracle_type: Oracle type name (VARCHAR2, NUMBER, DATE, etc.)

        Returns:
            Python native type value
        """
        # Handle NULL values
        if value is None:
            return None

        # If no type specified, infer from Python type
        if oracle_type is None:
            if isinstance(value, str):
                oracle_type = "VARCHAR2"
            elif isinstance(value, (int, float)):
                oracle_type = "NUMBER"
            elif isinstance(value, (datetime, date)):
                oracle_type = "DATE"
            else:
                oracle_type = "VARCHAR2"  # Default fallback

        oracle_type = oracle_type.upper()

        try:
            # String types
            if oracle_type in ("VARCHAR2", "CHAR", "CLOB", "NVARCHAR2", "NCHAR", "NCLOB"):
                result = str(value).strip() if value else None
                return result if result else None  # Empty string → None

            # Numeric types
            elif oracle_type in ("NUMBER", "NUMERIC", "DECIMAL", "INTEGER", "INT", "FLOAT"):
                if isinstance(value, (int, float)):
                    # Check if it's an integer
                    if isinstance(value, int) or float(value).is_integer():
                        return int(value)
                    return float(value)

                # Parse from string
                if isinstance(value, str):
                    value = value.strip().replace(",", "")  # Remove commas
                    if not value:
                        return None

                    try:
                        # Try as integer first
                        if "." not in value and "e" not in value.lower():
                            return int(value)
                        # Otherwise float
                        return float(value)
                    except ValueError:
                        logger.warning(f"Cannot convert '{value}' to number, using Decimal")
                        return Decimal(value)

                return Decimal(str(value))

            # Date/Time types
            elif oracle_type in ("DATE", "TIMESTAMP", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP WITH LOCAL TIME ZONE"):
                if isinstance(value, datetime):
                    return value.isoformat()
                elif isinstance(value, date):
                    return value.isoformat()
                elif isinstance(value, str):
                    return value.strip()
                else:
                    return str(value)

            # Binary types
            elif oracle_type in ("RAW", "LONG RAW", "BLOB"):
                if isinstance(value, bytes):
                    return value.hex()
                return str(value)

            # Boolean types (non-standard in Oracle, but handle anyway)
            elif oracle_type in ("BOOLEAN",):
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    upper = value.upper().strip()
                    if upper in ("TRUE", "T", "YES", "Y", "1"):
                        return True
                    elif upper in ("FALSE", "F", "NO", "N", "0"):
                        return False
                return bool(value)

            # Unknown type - return as string
            else:
                logger.warning(f"Unknown Oracle type: {oracle_type}, converting to string")
                return str(value)

        except Exception as e:
            logger.error(f"Type coercion failed for value={value}, type={oracle_type}: {e}")
            # Fallback to string
            return str(value) if value is not None else None

    def normalize_row(
        self, row: dict[str, Any], metadata: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Normalize all fields in a row

        Args:
            row: Raw row from APISmith
            metadata: Dict of field_name -> oracle_type (optional)

        Returns:
            Normalized row with coerced types
        """
        if metadata is None:
            metadata = {}

        normalized = {}

        for field_name, field_value in row.items():
            oracle_type = metadata.get(field_name)
            normalized[field_name] = self.coerce_value(field_value, oracle_type)

        return normalized

    def normalize_batch(
        self, rows: list[dict[str, Any]], metadata: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Normalize a batch of rows

        Args:
            rows: List of raw rows from APISmith
            metadata: Dict of field_name -> oracle_type (optional)

        Returns:
            List of normalized rows
        """
        return [self.normalize_row(row, metadata) for row in rows]
