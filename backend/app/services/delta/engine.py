"""
Delta Engine - Orchestrates Delta Detection

Determines INSERT/UPDATE/DELETE/SKIP operations for sync.
Supports both rowversion-based and hash-based strategies.
"""

from typing import Any
from enum import Enum
from loguru import logger

from app.services.delta.detector import (
    DeltaDetector,
    DeltaRecord,
    DeltaOperation,
)
from app.services.delta.rowversion_strategy import RowversionDeltaStrategy
from app.services.delta.hash_strategy import HashDeltaStrategy


class DeltaStrategy(str, Enum):
    """Delta detection strategy"""
    ROWVERSION = "rowversion"
    HASH = "hash"
    AUTO = "auto"


class DeltaEngine:
    """
    Delta Engine

    Orchestrates delta detection with multiple strategies.
    """

    def __init__(
        self,
        strategy: DeltaStrategy = DeltaStrategy.AUTO,
        rowversion_field: str | None = None,
    ):
        """
        Initialize delta engine

        Args:
            strategy: Delta detection strategy
                - ROWVERSION: Use rowversion comparison (fast)
                - HASH: Use data hash comparison (reliable)
                - AUTO: Try rowversion, fallback to hash
            rowversion_field: Name of rowversion field (if available)
        """
        self.strategy = strategy
        self.rowversion_field = rowversion_field

        self.detector = DeltaDetector()
        self.rowversion_strategy = RowversionDeltaStrategy()
        self.hash_strategy = HashDeltaStrategy()

        logger.info(f"Delta engine initialized: strategy={strategy}")

    def detect_delta(
        self,
        incoming_records: list[dict[str, Any]],
        stored_records: list[dict[str, Any]],
    ) -> tuple[dict[str, list[DeltaRecord]], dict[str, Any]]:
        """
        Detect delta operations for incoming records

        Args:
            incoming_records: Records from APISmith (with identity fields)
            stored_records: Records from target system (with identity fields)

        Returns:
            Tuple of:
                - Categorized delta records (insert, update, skip, delete)
                - Metrics dict
        """
        # Build lookup map for stored records
        stored_map = self._build_stored_map(stored_records)

        # Determine which strategy to use
        use_rowversion = self._should_use_rowversion(incoming_records)

        # Detect operations for incoming records
        if use_rowversion:
            logger.info("Using ROWVERSION strategy")
            delta_records = self.rowversion_strategy.detect_batch(
                incoming_records, stored_map, use_rowversion=True
            )
        else:
            logger.info("Using HASH strategy")
            delta_records = self.hash_strategy.detect_batch(
                incoming_records, stored_map
            )

        # Detect deletes (records in target but missing from source)
        deleted_bk_hashes = self._detect_deletes(incoming_records, stored_records)
        delete_records = self._create_delete_records(deleted_bk_hashes, stored_map)
        delta_records.extend(delete_records)

        # Categorize by operation
        categorized = self.detector.categorize_records(delta_records)

        # Calculate metrics
        metrics = self.detector.get_metrics(categorized)
        metrics["strategy_used"] = "rowversion" if use_rowversion else "hash"
        metrics["total_incoming"] = len(incoming_records)
        metrics["total_stored"] = len(stored_records)

        logger.info(
            f"Delta detection complete: "
            f"INSERT={metrics['insert']}, "
            f"UPDATE={metrics['update']}, "
            f"SKIP={metrics['skip']}, "
            f"DELETE={metrics['delete']}, "
            f"efficiency={metrics['efficiency_percent']}%"
        )

        return categorized, metrics

    def _build_stored_map(
        self, stored_records: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Build BK_HASH → record lookup map"""
        stored_map = {}
        for record in stored_records:
            bk_hash = record.get("erp_key_hash")
            if bk_hash:
                stored_map[bk_hash] = record
        return stored_map

    def _should_use_rowversion(self, sample_records: list[dict[str, Any]]) -> bool:
        """Determine if rowversion strategy should be used"""
        if self.strategy == DeltaStrategy.HASH:
            return False

        if self.strategy == DeltaStrategy.ROWVERSION:
            return True

        # AUTO mode: check if rowversion is available
        if not sample_records:
            return False

        sample = sample_records[0]
        has_rowversion = "erp_rowversion" in sample and sample["erp_rowversion"] is not None

        return has_rowversion

    def _detect_deletes(
        self,
        incoming_records: list[dict[str, Any]],
        stored_records: list[dict[str, Any]],
    ) -> list[str]:
        """Detect deleted records"""
        incoming_bk_hashes = {r.get("erp_key_hash") for r in incoming_records if r.get("erp_key_hash")}
        stored_bk_hashes = {r.get("erp_key_hash") for r in stored_records if r.get("erp_key_hash")}

        return self.detector.detect_deletes(incoming_bk_hashes, stored_bk_hashes)

    def _create_delete_records(
        self,
        deleted_bk_hashes: list[str],
        stored_map: dict[str, dict[str, Any]],
    ) -> list[DeltaRecord]:
        """Create DeltaRecord objects for deleted records"""
        delete_records = []

        for bk_hash in deleted_bk_hashes:
            stored_record = stored_map.get(bk_hash)
            if stored_record:
                delete_record = DeltaRecord(
                    operation=DeltaOperation.DELETE,
                    record=stored_record,
                    bk_hash=bk_hash,
                    data_hash=stored_record.get("erp_data_hash", ""),
                    stored_data_hash=stored_record.get("erp_data_hash"),
                    reason="Record missing from source",
                )
                delete_records.append(delete_record)

        return delete_records

    def get_actionable_records(
        self, categorized: dict[str, list[DeltaRecord]]
    ) -> list[DeltaRecord]:
        """
        Get records that need action (INSERT + UPDATE + DELETE)

        Args:
            categorized: Categorized delta records

        Returns:
            List of records needing action (excludes SKIP)
        """
        actionable = []
        actionable.extend(categorized.get("insert", []))
        actionable.extend(categorized.get("update", []))
        actionable.extend(categorized.get("delete", []))
        return actionable

    def get_records_by_operation(
        self, categorized: dict[str, list[DeltaRecord]], operation: str
    ) -> list[dict[str, Any]]:
        """
        Get raw records for a specific operation

        Args:
            categorized: Categorized delta records
            operation: Operation name (insert/update/delete/skip)

        Returns:
            List of raw data records
        """
        delta_records = categorized.get(operation, [])
        return [dr.record for dr in delta_records]


# Convenience function

def detect_delta_batch(
    incoming_records: list[dict[str, Any]],
    stored_records: list[dict[str, Any]],
    strategy: DeltaStrategy = DeltaStrategy.AUTO,
    rowversion_field: str | None = None,
) -> tuple[dict[str, list[DeltaRecord]], dict[str, Any]]:
    """
    Convenience function to detect delta for a batch

    Args:
        incoming_records: Records from APISmith (with identity)
        stored_records: Records from target system (with identity)
        strategy: Delta detection strategy
        rowversion_field: Rowversion field name (optional)

    Returns:
        Tuple of (categorized_records, metrics)
    """
    engine = DeltaEngine(strategy=strategy, rowversion_field=rowversion_field)
    return engine.detect_delta(incoming_records, stored_records)
