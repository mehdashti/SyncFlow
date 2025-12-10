"""
Rowversion-based Delta Strategy

Fast delta detection using Oracle rowversion/timestamp.
Best for: Large tables with rowversion column.
"""

from typing import Any
from loguru import logger

from app.services.delta.detector import DeltaRecord, DeltaOperation


class RowversionDeltaStrategy:
    """
    Rowversion-based delta detection strategy

    Advantages:
    - Very fast (query only changed records)
    - Low network overhead
    - Efficient for large tables

    Requirements:
    - Source table must have rowversion column
    - Rowversion must increment on every change
    """

    @staticmethod
    def detect_batch(
        incoming_records: list[dict[str, Any]],
        stored_records_map: dict[str, dict[str, Any]],
        use_rowversion: bool = True,
    ) -> list[DeltaRecord]:
        """
        Detect delta operations for a batch using rowversion

        Args:
            incoming_records: Records from APISmith (with identity)
            stored_records_map: Dict of BK_HASH → stored record
            use_rowversion: Enable rowversion comparison

        Returns:
            List of DeltaRecord objects
        """
        from app.services.delta.detector import DeltaDetector

        delta_records = []

        for record in incoming_records:
            bk_hash = record.get("erp_key_hash")
            if not bk_hash:
                logger.warning("Record missing erp_key_hash, skipping")
                continue

            stored_record = stored_records_map.get(bk_hash)

            delta_record = DeltaDetector.detect_operation(
                record=record,
                stored_record=stored_record,
                use_rowversion=use_rowversion,
            )

            delta_records.append(delta_record)

        return delta_records

    @staticmethod
    def build_query_filter(
        last_sync_rowversion: str | None,
        rowversion_field: str = "rowversion",
    ) -> dict[str, Any]:
        """
        Build query filter for APISmith API

        Args:
            last_sync_rowversion: Last synced rowversion
            rowversion_field: Name of rowversion field

        Returns:
            Query filter dict for APISmith API
        """
        if last_sync_rowversion is None:
            # First sync: fetch all records
            return {}

        # Incremental sync: fetch only changed records
        return {
            "filters": [
                {
                    "field": rowversion_field,
                    "operator": ">",
                    "value": last_sync_rowversion,
                }
            ]
        }

    @staticmethod
    def get_max_rowversion(records: list[dict[str, Any]]) -> str | None:
        """
        Get maximum rowversion from batch

        Args:
            records: List of records with erp_rowversion

        Returns:
            Maximum rowversion or None
        """
        from app.services.identity.rowversion import RowversionHandler
        handler = RowversionHandler()

        max_rv = None
        for record in records:
            rv = record.get("erp_rowversion")
            if rv:
                if max_rv is None:
                    max_rv = rv
                elif handler.is_newer(rv, max_rv):
                    max_rv = rv

        return max_rv

    @staticmethod
    def validate_rowversion_support(
        sample_record: dict[str, Any],
        rowversion_field: str = "rowversion",
    ) -> bool:
        """
        Validate that records have rowversion support

        Args:
            sample_record: Sample record to check
            rowversion_field: Expected rowversion field name

        Returns:
            True if rowversion is available
        """
        has_rowversion = rowversion_field in sample_record
        has_erp_rowversion = "erp_rowversion" in sample_record

        if not (has_rowversion or has_erp_rowversion):
            logger.warning(
                f"Rowversion field '{rowversion_field}' not found in record. "
                "Falling back to hash-based delta."
            )
            return False

        return True
