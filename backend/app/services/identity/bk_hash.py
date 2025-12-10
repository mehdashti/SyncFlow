"""
Business Key Hash (BK_HASH) Generator

Generates xxHash128 hash from business key fields to uniquely identify records.
Used for: Record matching, upsert logic, parent-child resolution.

Technology: xxHash128 (fast, non-cryptographic, 32-character hex string)
"""

import xxhash
from typing import Any
from loguru import logger


class BKHashGenerator:
    """
    Generates BK_HASH (Business Key Hash) from business key fields.

    Uses xxHash128 for fast, non-cryptographic hashing.

    Example:
        Input: {"item_number": "PART-12345", "site_code": "SITE-A"}
        Business keys: ["item_number", "site_code"]
        Canonical string: "item_number=PART-12345|site_code=SITE-A"
        BK_HASH: xxHash128(canonical_string) → 32-character hex
    """

    @staticmethod
    def generate(
        record: dict[str, Any],
        business_key_fields: list[str],
        entity_name: str | None = None
    ) -> str:
        """
        Generate Business Key Hash (BK_HASH) using xxHash128

        Args:
            record: Data record
            business_key_fields: List of field names that form the business key
            entity_name: Optional entity name as prefix

        Returns:
            xxHash128 hash (32-character hex string)

        Raises:
            ValueError: If any business key field is missing or NULL
        """
        if not business_key_fields:
            raise ValueError("business_key_fields cannot be empty")

        # Extract business key values
        key_values = []
        for field in business_key_fields:
            if field not in record:
                raise ValueError(f"Business key field '{field}' not found in record")

            value = record[field]
            if value is None:
                raise ValueError(f"Business key field '{field}' is NULL")

            key_values.append(f"{field}={value}")

        # Sort for consistent ordering
        key_values.sort()

        # Create canonical string
        canonical = "|".join(key_values)
        if entity_name:
            canonical = f"{entity_name}|{canonical}"

        # Generate xxHash128 hash
        bk_hash = xxhash.xxh128(canonical.encode('utf-8')).hexdigest()

        logger.debug(f"BK_HASH (xxHash128) generated: {canonical} → {bk_hash}")

        return bk_hash

    @staticmethod
    def generate_batch(
        records: list[dict[str, Any]],
        business_key_fields: list[str],
        entity_name: str | None = None
    ) -> list[tuple[dict[str, Any], str]]:
        """
        Generate BK_HASH for a batch of records

        Args:
            records: List of data records
            business_key_fields: List of field names that form the business key
            entity_name: Optional entity name as prefix

        Returns:
            List of tuples: (record, bk_hash)
            Records with errors are excluded
        """
        results = []
        errors = 0

        for i, record in enumerate(records):
            try:
                bk_hash = BKHashGenerator.generate(
                    record, business_key_fields, entity_name
                )
                results.append((record, bk_hash))
            except ValueError as e:
                logger.warning(f"Record {i} BK_HASH generation failed: {e}")
                errors += 1

        if errors > 0:
            logger.warning(f"BK_HASH batch: {errors}/{len(records)} records failed")

        return results

    @staticmethod
    def validate(bk_hash: str) -> bool:
        """
        Validate BK_HASH format

        Args:
            bk_hash: Hash to validate

        Returns:
            True if valid xxHash128 hash (32-character hex), False otherwise
        """
        if not bk_hash:
            return False

        # xxHash128 produces 32-character hex string
        if len(bk_hash) != 32:
            return False

        # Check if hex
        try:
            int(bk_hash, 16)
            return True
        except ValueError:
            return False


# Backward compatibility alias
BusinessKeyHashGenerator = BKHashGenerator


# Convenience functions

def generate_bk_hash(
    row: dict[str, Any],
    business_key_fields: list[str],
    entity_name: str | None = None
) -> str:
    """
    Convenience function to generate BK_HASH using xxHash128

    Args:
        row: Data row
        business_key_fields: List of field names forming business key
        entity_name: Optional entity name as prefix

    Returns:
        BK_HASH (32-character hex string)
    """
    return BKHashGenerator.generate(row, business_key_fields, entity_name)


def generate_bk_hash_batch(
    rows: list[dict[str, Any]],
    business_key_fields: list[str],
    entity_name: str | None = None
) -> list[tuple[dict[str, Any], str]]:
    """
    Convenience function to generate BK_HASH for batch

    Args:
        rows: List of data rows
        business_key_fields: List of field names forming business key
        entity_name: Optional entity name as prefix

    Returns:
        List of (row, bk_hash) tuples
    """
    return BKHashGenerator.generate_batch(rows, business_key_fields, entity_name)
