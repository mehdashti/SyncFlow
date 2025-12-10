"""
Identity Engine - Orchestrates BK_HASH + DATA_HASH + Rowversion

Adds identity fields to normalized data:
- erp_key_hash (BK_HASH): Business key hash for record matching
- erp_data_hash (DATA_HASH): Data hash for change detection
- erp_rowversion: Rowversion for fast delta queries
- erp_ref_str: Human-readable reference for debugging
"""

from typing import Any
from loguru import logger

from app.services.identity.bk_hash import BusinessKeyHashGenerator
from app.services.identity.data_hash import DataHashGenerator
from app.services.identity.rowversion import RowversionHandler


class IdentityEngine:
    """
    Identity Engine

    Adds identity fields to data rows for tracking and delta detection.
    """

    def __init__(
        self,
        business_key_fields: list[str],
        entity_name: str | None = None,
        rowversion_field: str | None = None,
        exclude_from_data_hash: set[str] | None = None,
    ):
        """
        Initialize identity engine

        Args:
            business_key_fields: List of fields that form the business key
            entity_name: Optional entity name (used as prefix in BK_HASH)
            rowversion_field: Optional rowversion field name
            exclude_from_data_hash: Optional set of fields to exclude from DATA_HASH
        """
        self.business_key_fields = business_key_fields
        self.entity_name = entity_name or ""
        self.rowversion_field = rowversion_field
        self.exclude_from_data_hash = exclude_from_data_hash

        self.bk_hash_generator = BusinessKeyHashGenerator()
        self.data_hash_generator = DataHashGenerator()
        self.rowversion_handler = RowversionHandler()

        logger.info(
            f"Identity engine initialized: "
            f"entity={entity_name}, "
            f"business_keys={business_key_fields}, "
            f"rowversion_field={rowversion_field}"
        )

    def add_identity(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Add identity fields to a row

        Args:
            row: Data row (should already be normalized)

        Returns:
            Row with added identity fields:
                - erp_key_hash (BK_HASH)
                - erp_data_hash (DATA_HASH)
                - erp_rowversion (if available)
                - erp_ref_str (human-readable reference)

        Raises:
            ValueError: If business key fields are missing or NULL
        """
        # Generate BK_HASH
        bk_hash = self.bk_hash_generator.generate_bk_hash(
            row, self.business_key_fields, self.entity_name
        )

        # Generate DATA_HASH
        data_hash = self.data_hash_generator.generate_data_hash(
            row, self.exclude_from_data_hash
        )

        # Extract rowversion if configured
        rowversion = None
        if self.rowversion_field:
            rowversion = self.rowversion_handler.extract_rowversion(
                row, self.rowversion_field
            )

        # Create reference string for debugging
        ref_parts = []
        for field in self.business_key_fields:
            value = row.get(field)
            if value is not None:
                ref_parts.append(f"{field}={value}")
        ref_str = "|".join(ref_parts)

        # Add identity fields to row
        row_with_identity = row.copy()
        row_with_identity["erp_key_hash"] = bk_hash
        row_with_identity["erp_data_hash"] = data_hash
        row_with_identity["erp_rowversion"] = rowversion
        row_with_identity["erp_ref_str"] = ref_str

        logger.debug(
            f"Identity added: {ref_str} → BK={bk_hash[:8]}... DATA={data_hash[:8]}..."
        )

        return row_with_identity

    def add_identity_batch(
        self, rows: list[dict[str, Any]], track_metrics: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        Add identity to a batch of rows

        Args:
            rows: List of data rows
            track_metrics: If True, return metrics

        Returns:
            Tuple of (rows_with_identity, metrics)
        """
        rows_with_identity = []
        metrics = {
            "total_rows": len(rows),
            "successful": 0,
            "failed": 0,
        }

        for i, row in enumerate(rows):
            try:
                row_with_id = self.add_identity(row)
                rows_with_identity.append(row_with_id)
                metrics["successful"] += 1
            except Exception as e:
                logger.error(f"Row {i} identity generation failed: {e}")
                metrics["failed"] += 1
                # Optionally: store failed row for retry

        if track_metrics:
            success_rate = (
                (metrics["successful"] / metrics["total_rows"] * 100)
                if metrics["total_rows"] > 0
                else 0
            )
            metrics["success_rate"] = round(success_rate, 2)
            logger.info(
                f"Identity batch complete: "
                f"{metrics['successful']}/{metrics['total_rows']} rows "
                f"({metrics['success_rate']}% success rate)"
            )

        return rows_with_identity, metrics

    def validate_identity(self, row: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate that a row has all required identity fields

        Args:
            row: Row to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required_fields = ["erp_key_hash", "erp_data_hash", "erp_ref_str"]

        for field in required_fields:
            if field not in row or row[field] is None:
                errors.append(f"Missing required identity field: {field}")

        # Validate hash formats
        if "erp_key_hash" in row:
            bk_hash = row["erp_key_hash"]
            if not self.bk_hash_generator.validate_bk_hash(bk_hash):
                errors.append(f"Invalid BK_HASH format: {bk_hash}")

        if "erp_data_hash" in row:
            data_hash = row["erp_data_hash"]
            if len(data_hash) != 64:
                errors.append(f"Invalid DATA_HASH format: {data_hash}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def get_business_key_values(self, row: dict[str, Any]) -> dict[str, Any]:
        """
        Extract business key values from row

        Args:
            row: Data row

        Returns:
            Dict of business key field -> value
        """
        bk_values = {}
        for field in self.business_key_fields:
            if field in row:
                bk_values[field] = row[field]
        return bk_values


# Convenience function

def add_identity_to_rows(
    rows: list[dict[str, Any]],
    business_key_fields: list[str],
    entity_name: str | None = None,
    rowversion_field: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Convenience function to add identity to rows

    Args:
        rows: List of normalized data rows
        business_key_fields: List of fields forming business key
        entity_name: Optional entity name
        rowversion_field: Optional rowversion field name

    Returns:
        Tuple of (rows_with_identity, metrics)
    """
    engine = IdentityEngine(
        business_key_fields=business_key_fields,
        entity_name=entity_name,
        rowversion_field=rowversion_field,
    )
    return engine.add_identity_batch(rows, track_metrics=True)
