"""
Layer 4: Date/Time Normalization

Handles date and time parsing:
- Support multiple date formats
- Handle Oracle DATE objects
- Convert to ISO 8601 format
- Handle timezone conversion
"""

from typing import Any
from datetime import datetime, date
from dateutil import parser as dateutil_parser
from loguru import logger


class DateTimeNormalizationLayer:
    """
    Layer 4: Date/Time Normalization
    Parses and normalizes date/time values to ISO 8601
    """

    # Common date formats to try
    DATE_FORMATS = [
        "%Y-%m-%d",  # ISO date: 2025-12-08
        "%Y/%m/%d",  # Slash format: 2025/12/08
        "%d-%m-%Y",  # European: 08-12-2025
        "%d/%m/%Y",  # European slash: 08/12/2025
        "%m-%d-%Y",  # US format: 12-08-2025
        "%m/%d/%Y",  # US slash: 12/08/2025
        "%Y%m%d",    # Compact: 20251208
        "%d.%m.%Y",  # Dot format: 08.12.2025
    ]

    DATETIME_FORMATS = [
        "%Y-%m-%d %H:%M:%S",  # ISO datetime
        "%Y-%m-%dT%H:%M:%S",  # ISO with T
        "%Y-%m-%d %H:%M:%S.%f",  # With microseconds
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with T and microseconds
        "%d-%m-%Y %H:%M:%S",  # European datetime
        "%m-%d-%Y %H:%M:%S",  # US datetime
    ]

    @staticmethod
    def normalize_datetime(value: Any) -> str | None:
        """
        Normalize a date/time value to ISO 8601 string

        Args:
            value: Date/time value (datetime, date, or string)

        Returns:
            ISO 8601 string or None
        """
        if value is None:
            return None

        try:
            # Already a datetime object
            if isinstance(value, datetime):
                return value.isoformat()

            # Already a date object (convert to datetime at midnight)
            if isinstance(value, date):
                return datetime(value.year, value.month, value.day).isoformat()

            # Parse from string
            if isinstance(value, str):
                value = value.strip()

                # Empty string → None
                if not value:
                    return None

                # Try common formats first (faster)
                for fmt in DateTimeNormalizationLayer.DATETIME_FORMATS:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue

                for fmt in DateTimeNormalizationLayer.DATE_FORMATS:
                    try:
                        dt = datetime.strptime(value, fmt)
                        return dt.isoformat()
                    except ValueError:
                        continue

                # Fallback: use dateutil parser (more flexible but slower)
                try:
                    dt = dateutil_parser.parse(value)
                    return dt.isoformat()
                except Exception:
                    pass

                # Cannot parse - return original string
                logger.warning(f"Cannot parse date/time value: '{value}'")
                return value

            # Unknown type - convert to string
            logger.warning(f"Unknown date/time type: {type(value)}")
            return str(value)

        except Exception as e:
            logger.error(f"DateTime normalization failed for value='{value}': {e}")
            # Return original as string
            return str(value) if value is not None else None

    @staticmethod
    def normalize_date_only(value: Any) -> str | None:
        """
        Normalize to date only (YYYY-MM-DD)

        Args:
            value: Date value

        Returns:
            ISO date string or None
        """
        dt_str = DateTimeNormalizationLayer.normalize_datetime(value)
        if dt_str is None:
            return None

        try:
            # Extract date part from ISO datetime
            if 'T' in dt_str:
                return dt_str.split('T')[0]
            elif ' ' in dt_str:
                return dt_str.split(' ')[0]
            return dt_str
        except Exception:
            return dt_str

    def normalize_row(
        self,
        row: dict[str, Any],
        datetime_fields: set[str] | None = None,
        date_fields: set[str] | None = None
    ) -> dict[str, Any]:
        """
        Normalize date/time fields in a row

        Args:
            row: Row with mixed types
            datetime_fields: Set of field names that are datetime (optional)
            date_fields: Set of field names that are date only (optional)

        Returns:
            Row with normalized date/time values
        """
        if datetime_fields is None:
            datetime_fields = set()
        if date_fields is None:
            date_fields = set()

        normalized = {}

        for field_name, field_value in row.items():
            if field_name in datetime_fields:
                normalized[field_name] = self.normalize_datetime(field_value)
            elif field_name in date_fields:
                normalized[field_name] = self.normalize_date_only(field_value)
            elif isinstance(field_value, (datetime, date)):
                # Auto-detect
                normalized[field_name] = self.normalize_datetime(field_value)
            else:
                normalized[field_name] = field_value

        return normalized

    def normalize_batch(
        self,
        rows: list[dict[str, Any]],
        datetime_fields: set[str] | None = None,
        date_fields: set[str] | None = None
    ) -> list[dict[str, Any]]:
        """
        Normalize a batch of rows

        Args:
            rows: List of rows
            datetime_fields: Set of field names that are datetime (optional)
            date_fields: Set of field names that are date only (optional)

        Returns:
            List of normalized rows
        """
        return [self.normalize_row(row, datetime_fields, date_fields) for row in rows]
