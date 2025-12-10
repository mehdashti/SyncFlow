"""
Hash-based Delta Strategy

Delta detection using DATA_HASH comparison.
Best for: Tables without rowversion, or as fallback.
"""

from typing import Any
from loguru import logger

from app.services.delta.detector import DeltaRecord, DeltaOperation


class HashDeltaStrategy:
    """
    Hash-based delta detection strategy

    Advantages:
    - Works for any table (no rowversion required)
    - Detects any data change
    - Reliable

    Disadvantages:
    - Must fetch all records from target
    - Higher network overhead
    - Slower for large tables
    """

    @staticmethod
    def detect_batch(
        incoming_records: list[dict[str, Any]],
        stored_records_map: dict[str, dict[str, Any]],
    ) -> list[DeltaRecord]:
        """
        Detect delta operations for a batch using DATA_HASH

        Args:
            incoming_records: Records from APISmith (with identity)
            stored_records_map: Dict of BK_HASH → stored record

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

            # Force hash-based comparison (use_rowversion=False)
            delta_record = DeltaDetector.detect_operation(
                record=record,
                stored_record=stored_record,
                use_rowversion=False,
            )

            delta_records.append(delta_record)

        return delta_records

    @staticmethod
    def compare_hashes(
        current_hash: str,
        stored_hash: str | None,
    ) -> tuple[bool, str]:
        """
        Compare data hashes

        Args:
            current_hash: Current DATA_HASH
            stored_hash: Stored DATA_HASH

        Returns:
            Tuple of (changed, reason)
        """
        if stored_hash is None:
            return True, "New record"

        if current_hash != stored_hash:
            return True, f"Data changed: {stored_hash[:8]}... → {current_hash[:8]}..."

        return False, "Data unchanged"

    @staticmethod
    def build_stored_map(
        stored_records: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """
        Build lookup map: BK_HASH → stored record

        Args:
            stored_records: Records from target system

        Returns:
            Dict of BK_HASH → record
        """
        stored_map = {}

        for record in stored_records:
            bk_hash = record.get("erp_key_hash")
            if bk_hash:
                stored_map[bk_hash] = record
            else:
                logger.warning("Stored record missing erp_key_hash")

        logger.debug(f"Built stored map with {len(stored_map)} records")
        return stored_map

    @staticmethod
    def detect_unchanged_records(
        incoming_records: list[dict[str, Any]],
        stored_records_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Filter out unchanged records (optimization)

        Args:
            incoming_records: Records from APISmith
            stored_records_map: Dict of BK_HASH → stored record

        Returns:
            List of records that have changed (INSERT or UPDATE)
        """
        changed_records = []

        for record in incoming_records:
            bk_hash = record.get("erp_key_hash")
            data_hash = record.get("erp_data_hash")

            if not bk_hash or not data_hash:
                # Missing identity, include for error handling
                changed_records.append(record)
                continue

            stored_record = stored_records_map.get(bk_hash)

            # New record (INSERT)
            if stored_record is None:
                changed_records.append(record)
                continue

            # Existing record - check if changed
            stored_data_hash = stored_record.get("erp_data_hash")
            if data_hash != stored_data_hash:
                changed_records.append(record)

        skipped = len(incoming_records) - len(changed_records)
        if skipped > 0:
            logger.info(f"Skipped {skipped} unchanged records")

        return changed_records
