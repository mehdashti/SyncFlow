"""
Data Hash (DATA_HASH) Generator

Generates BLAKE3 hash from ALL data fields to detect changes.
Used for: Delta detection, skip unchanged records.

Technology: BLAKE3 (fast cryptographic hash, 64-character hex string)
"""

import blake3
import json
from typing import Any
from loguru import logger


class DataHashGenerator:
    """
    Generates DATA_HASH from all data fields using BLAKE3.

    Example:
        Input: {"item_number": "PART-12345", "description": "Widget", "price": 10.5}
        Canonical string: "description=Widget|item_number=PART-12345|price=10.5"
        (alphabetically sorted)
        DATA_HASH: BLAKE3(canonical_string) → 64-character hex
    """

    @staticmethod
    def generate_data_hash(
        row: dict[str, Any],
        exclude_fields: set[str] | None = None
    ) -> str:
        """
        Generate Data Hash (DATA_HASH) using BLAKE3

        Args:
            row: Data row
            exclude_fields: Set of field names to exclude from hash
                           (e.g., audit fields like created_at, updated_at)

        Returns:
            BLAKE3 hash (64-character hex string)
        """
        if exclude_fields is None:
            exclude_fields = {
                # Commonly excluded fields
                "created_at", "updated_at", "created_at_utc", "updated_at_utc",
                "uid", "id",  # Primary keys
                "erp_key_hash", "erp_data_hash", "erp_rowversion",  # Identity fields
            }

        # Filter and normalize data
        data_to_hash = {}

        for field, value in row.items():
            # Skip excluded fields
            if field in exclude_fields:
                continue

            # Normalize value for consistent hashing
            normalized_value = DataHashGenerator._normalize_value(value)
            data_to_hash[field] = normalized_value

        # Sort fields alphabetically for consistent hashing
        sorted_fields = sorted(data_to_hash.keys())

        # Create canonical string
        key_values = []
        for field in sorted_fields:
            value = data_to_hash[field]
            if value is not None:  # Skip NULL values
                key_values.append(f"{field}={value}")

        canonical = "|".join(key_values)

        # Generate BLAKE3 hash
        data_hash = blake3.blake3(canonical.encode('utf-8')).hexdigest()

        logger.debug(f"DATA_HASH (BLAKE3) generated from {len(sorted_fields)} fields: {data_hash[:16]}...")

        return data_hash

    @staticmethod
    def _normalize_value(value: Any) -> str | None:
        """
        Normalize value for consistent hashing

        Args:
            value: Value to normalize

        Returns:
            Normalized string representation or None
        """
        if value is None:
            return None

        # Numbers: convert to string with fixed precision
        if isinstance(value, float):
            # Round to 6 decimal places to avoid floating point issues
            return f"{value:.6f}".rstrip('0').rstrip('.')

        if isinstance(value, int):
            return str(value)

        # Booleans
        if isinstance(value, bool):
            return "true" if value else "false"

        # Strings: trim and normalize
        if isinstance(value, str):
            return value.strip()

        # Lists/Dicts: convert to JSON
        if isinstance(value, (list, dict)):
            return json.dumps(value, sort_keys=True, separators=(',', ':'))

        # Default: convert to string
        return str(value)

    @staticmethod
    def generate_data_hash_batch(
        rows: list[dict[str, Any]],
        exclude_fields: set[str] | None = None
    ) -> list[tuple[dict[str, Any], str]]:
        """
        Generate DATA_HASH for a batch of rows

        Args:
            rows: List of data rows
            exclude_fields: Set of field names to exclude

        Returns:
            List of tuples: (row, data_hash)
        """
        results = []
        errors = 0

        for i, row in enumerate(rows):
            try:
                data_hash = DataHashGenerator.generate_data_hash(row, exclude_fields)
                results.append((row, data_hash))
            except Exception as e:
                logger.error(f"Row {i} DATA_HASH generation failed: {e}")
                errors += 1

        if errors > 0:
            logger.warning(f"DATA_HASH batch: {errors}/{len(rows)} rows failed")

        return results

    @staticmethod
    def compare_data_hashes(hash1: str, hash2: str) -> bool:
        """
        Compare two data hashes

        Args:
            hash1: First hash
            hash2: Second hash

        Returns:
            True if hashes match, False otherwise
        """
        return hash1 == hash2

    @staticmethod
    def has_data_changed(
        current_row: dict[str, Any],
        stored_data_hash: str,
        exclude_fields: set[str] | None = None
    ) -> bool:
        """
        Check if data has changed by comparing hashes

        Args:
            current_row: Current data row
            stored_data_hash: Previously stored DATA_HASH
            exclude_fields: Fields to exclude from comparison

        Returns:
            True if data changed, False if unchanged
        """
        current_hash = DataHashGenerator.generate_data_hash(current_row, exclude_fields)
        return current_hash != stored_data_hash


# Convenience functions

def generate_data_hash(
    row: dict[str, Any],
    exclude_fields: set[str] | None = None
) -> str:
    """
    Convenience function to generate DATA_HASH using BLAKE3

    Args:
        row: Data row
        exclude_fields: Optional set of fields to exclude

    Returns:
        DATA_HASH (64-character hex string)
    """
    return DataHashGenerator.generate_data_hash(row, exclude_fields)


def generate_data_hash_batch(
    rows: list[dict[str, Any]],
    exclude_fields: set[str] | None = None
) -> list[tuple[dict[str, Any], str]]:
    """
    Convenience function to generate DATA_HASH for batch

    Args:
        rows: List of data rows
        exclude_fields: Optional set of fields to exclude

    Returns:
        List of (row, data_hash) tuples
    """
    return DataHashGenerator.generate_data_hash_batch(rows, exclude_fields)


def has_data_changed(
    current_row: dict[str, Any],
    stored_data_hash: str,
    exclude_fields: set[str] | None = None
) -> bool:
    """
    Convenience function to check if data changed

    Args:
        current_row: Current data row
        stored_data_hash: Previously stored DATA_HASH
        exclude_fields: Optional set of fields to exclude

    Returns:
        True if data changed, False if unchanged
    """
    return DataHashGenerator.has_data_changed(current_row, stored_data_hash, exclude_fields)
