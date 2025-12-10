"""
Rowversion Handler

Handles Oracle/ERP rowversion for fast delta detection.
Rowversion can be: timestamp, version number, or hash.
"""

from typing import Any
from datetime import datetime
from dateutil import parser as dateutil_parser
from loguru import logger


class RowversionHandler:
    """
    Handles rowversion extraction and comparison.

    Rowversion types:
    1. Timestamp: "2025-12-08 10:30:00.123456"
    2. Version number: 12345
    3. Hash/String: "abc123def456"
    """

    @staticmethod
    def extract_rowversion(row: dict[str, Any], rowversion_field: str = "rowversion") -> str | None:
        """
        Extract rowversion from row

        Args:
            row: Data row
            rowversion_field: Name of rowversion field

        Returns:
            Rowversion as string, or None if not found
        """
        if rowversion_field not in row:
            return None

        value = row[rowversion_field]
        if value is None:
            return None

        # Convert to string
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return value.strip()
        else:
            return str(value)

    @staticmethod
    def compare_rowversions(rv1: str | None, rv2: str | None) -> int:
        """
        Compare two rowversions

        Args:
            rv1: First rowversion
            rv2: Second rowversion

        Returns:
            -1 if rv1 < rv2
             0 if rv1 == rv2
             1 if rv1 > rv2
            None if comparison not possible
        """
        if rv1 is None and rv2 is None:
            return 0
        if rv1 is None:
            return -1
        if rv2 is None:
            return 1

        # Try as timestamps
        try:
            dt1 = RowversionHandler._parse_datetime(rv1)
            dt2 = RowversionHandler._parse_datetime(rv2)
            if dt1 and dt2:
                if dt1 < dt2:
                    return -1
                elif dt1 > dt2:
                    return 1
                else:
                    return 0
        except Exception:
            pass

        # Try as numbers
        try:
            num1 = float(rv1)
            num2 = float(rv2)
            if num1 < num2:
                return -1
            elif num1 > num2:
                return 1
            else:
                return 0
        except ValueError:
            pass

        # Fallback: string comparison
        if rv1 < rv2:
            return -1
        elif rv1 > rv2:
            return 1
        else:
            return 0

    @staticmethod
    def _parse_datetime(value: str) -> datetime | None:
        """
        Try to parse rowversion as datetime

        Args:
            value: Rowversion string

        Returns:
            datetime object or None
        """
        try:
            # Try ISO format first
            if 'T' in value or ' ' in value:
                return dateutil_parser.parse(value)
        except Exception:
            pass

        return None

    @staticmethod
    def is_newer(current_rv: str | None, stored_rv: str | None) -> bool:
        """
        Check if current rowversion is newer than stored

        Args:
            current_rv: Current rowversion
            stored_rv: Stored rowversion

        Returns:
            True if current is newer, False otherwise
        """
        comparison = RowversionHandler.compare_rowversions(current_rv, stored_rv)
        return comparison > 0

    @staticmethod
    def is_equal(rv1: str | None, rv2: str | None) -> bool:
        """
        Check if two rowversions are equal

        Args:
            rv1: First rowversion
            rv2: Second rowversion

        Returns:
            True if equal, False otherwise
        """
        comparison = RowversionHandler.compare_rowversions(rv1, rv2)
        return comparison == 0

    @staticmethod
    def validate_rowversion(rowversion: str | None) -> bool:
        """
        Validate rowversion format

        Args:
            rowversion: Rowversion to validate

        Returns:
            True if valid, False otherwise
        """
        if rowversion is None:
            return False

        if not isinstance(rowversion, str):
            return False

        if not rowversion.strip():
            return False

        return True

    @staticmethod
    def extract_rowversion_batch(
        rows: list[dict[str, Any]],
        rowversion_field: str = "rowversion"
    ) -> list[tuple[dict[str, Any], str | None]]:
        """
        Extract rowversion from batch of rows

        Args:
            rows: List of data rows
            rowversion_field: Name of rowversion field

        Returns:
            List of tuples: (row, rowversion)
        """
        results = []

        for row in rows:
            rowversion = RowversionHandler.extract_rowversion(row, rowversion_field)
            results.append((row, rowversion))

        return results


# Convenience functions

def extract_rowversion(row: dict[str, Any], rowversion_field: str = "rowversion") -> str | None:
    """
    Convenience function to extract rowversion

    Args:
        row: Data row
        rowversion_field: Name of rowversion field

    Returns:
        Rowversion as string or None
    """
    handler = RowversionHandler()
    return handler.extract_rowversion(row, rowversion_field)


def is_newer(current_rv: str | None, stored_rv: str | None) -> bool:
    """
    Convenience function to check if rowversion is newer

    Args:
        current_rv: Current rowversion
        stored_rv: Stored rowversion

    Returns:
        True if current is newer
    """
    handler = RowversionHandler()
    return handler.is_newer(current_rv, stored_rv)


def compare_rowversions(rv1: str | None, rv2: str | None) -> int:
    """
    Convenience function to compare rowversions

    Args:
        rv1: First rowversion
        rv2: Second rowversion

    Returns:
        -1, 0, or 1
    """
    handler = RowversionHandler()
    return handler.compare_rowversions(rv1, rv2)
