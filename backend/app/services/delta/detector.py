"""
Delta Detector

Core logic for detecting INSERT, UPDATE, DELETE, and SKIP operations.
"""

from typing import Any
from enum import Enum
from loguru import logger


class DeltaOperation(str, Enum):
    """Delta operation types"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    SKIP = "SKIP"


class DeltaRecord:
    """
    Represents a record with its delta operation

    Attributes:
        operation: DeltaOperation (INSERT/UPDATE/DELETE/SKIP)
        record: The data record
        bk_hash: Business key hash
        data_hash: Current data hash
        stored_data_hash: Previously stored data hash (if exists)
        rowversion: Current rowversion (if available)
        stored_rowversion: Previously stored rowversion (if exists)
        reason: Human-readable reason for the operation
    """

    def __init__(
        self,
        operation: DeltaOperation,
        record: dict[str, Any],
        bk_hash: str,
        data_hash: str,
        stored_data_hash: str | None = None,
        rowversion: str | None = None,
        stored_rowversion: str | None = None,
        reason: str = "",
    ):
        self.operation = operation
        self.record = record
        self.bk_hash = bk_hash
        self.data_hash = data_hash
        self.stored_data_hash = stored_data_hash
        self.rowversion = rowversion
        self.stored_rowversion = stored_rowversion
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary"""
        return {
            "operation": self.operation.value,
            "bk_hash": self.bk_hash,
            "data_hash": self.data_hash,
            "stored_data_hash": self.stored_data_hash,
            "rowversion": self.rowversion,
            "stored_rowversion": self.stored_rowversion,
            "reason": self.reason,
        }


class DeltaDetector:
    """
    Detects delta operations for records

    Compares incoming records with stored state to determine:
    - INSERT: Record doesn't exist in target
    - UPDATE: Record exists but data changed
    - SKIP: Record exists and data unchanged
    - DELETE: Record missing from source (detected separately)
    """

    @staticmethod
    def detect_operation(
        record: dict[str, Any],
        stored_record: dict[str, Any] | None,
        use_rowversion: bool = False,
    ) -> DeltaRecord:
        """
        Detect delta operation for a single record

        Args:
            record: Current record with identity fields
            stored_record: Previously stored record (None if not exists)
            use_rowversion: If True, use rowversion for comparison

        Returns:
            DeltaRecord with operation and metadata
        """
        bk_hash = record.get("erp_key_hash")
        data_hash = record.get("erp_data_hash")
        rowversion = record.get("erp_rowversion")

        if not bk_hash or not data_hash:
            raise ValueError("Record missing identity fields (erp_key_hash or erp_data_hash)")

        # Case 1: Record doesn't exist in target → INSERT
        if stored_record is None:
            return DeltaRecord(
                operation=DeltaOperation.INSERT,
                record=record,
                bk_hash=bk_hash,
                data_hash=data_hash,
                rowversion=rowversion,
                reason="New record (BK_HASH not found in target)",
            )

        # Extract stored values
        stored_data_hash = stored_record.get("erp_data_hash")
        stored_rowversion = stored_record.get("erp_rowversion")

        # Case 2: Use rowversion comparison (if available and enabled)
        if use_rowversion and rowversion and stored_rowversion:
            if DeltaDetector._is_rowversion_newer(rowversion, stored_rowversion):
                return DeltaRecord(
                    operation=DeltaOperation.UPDATE,
                    record=record,
                    bk_hash=bk_hash,
                    data_hash=data_hash,
                    stored_data_hash=stored_data_hash,
                    rowversion=rowversion,
                    stored_rowversion=stored_rowversion,
                    reason=f"Rowversion changed: {stored_rowversion} → {rowversion}",
                )
            else:
                return DeltaRecord(
                    operation=DeltaOperation.SKIP,
                    record=record,
                    bk_hash=bk_hash,
                    data_hash=data_hash,
                    stored_data_hash=stored_data_hash,
                    rowversion=rowversion,
                    stored_rowversion=stored_rowversion,
                    reason="Rowversion unchanged",
                )

        # Case 3: Use data hash comparison (fallback or default)
        if data_hash != stored_data_hash:
            return DeltaRecord(
                operation=DeltaOperation.UPDATE,
                record=record,
                bk_hash=bk_hash,
                data_hash=data_hash,
                stored_data_hash=stored_data_hash,
                rowversion=rowversion,
                stored_rowversion=stored_rowversion,
                reason=f"Data changed: {stored_data_hash[:8]}... → {data_hash[:8]}...",
            )
        else:
            return DeltaRecord(
                operation=DeltaOperation.SKIP,
                record=record,
                bk_hash=bk_hash,
                data_hash=data_hash,
                stored_data_hash=stored_data_hash,
                rowversion=rowversion,
                stored_rowversion=stored_rowversion,
                reason="Data unchanged",
            )

    @staticmethod
    def _is_rowversion_newer(current: str, stored: str) -> bool:
        """
        Compare rowversions

        Args:
            current: Current rowversion
            stored: Stored rowversion

        Returns:
            True if current is newer
        """
        from app.services.identity.rowversion import RowversionHandler
        handler = RowversionHandler()
        return handler.is_newer(current, stored)

    @staticmethod
    def detect_deletes(
        current_bk_hashes: set[str],
        stored_bk_hashes: set[str],
    ) -> list[str]:
        """
        Detect deleted records

        Records that exist in target but missing from source.

        Args:
            current_bk_hashes: Set of BK_HASHes from current sync
            stored_bk_hashes: Set of BK_HASHes from target system

        Returns:
            List of BK_HASHes that should be deleted
        """
        deletes = stored_bk_hashes - current_bk_hashes
        if deletes:
            logger.info(f"Detected {len(deletes)} records for deletion")
        return list(deletes)

    @staticmethod
    def categorize_records(
        delta_records: list[DeltaRecord],
    ) -> dict[str, list[DeltaRecord]]:
        """
        Categorize delta records by operation

        Args:
            delta_records: List of DeltaRecord objects

        Returns:
            Dict with keys: insert, update, skip, delete
        """
        categories = {
            "insert": [],
            "update": [],
            "skip": [],
            "delete": [],
        }

        for delta_record in delta_records:
            if delta_record.operation == DeltaOperation.INSERT:
                categories["insert"].append(delta_record)
            elif delta_record.operation == DeltaOperation.UPDATE:
                categories["update"].append(delta_record)
            elif delta_record.operation == DeltaOperation.SKIP:
                categories["skip"].append(delta_record)
            elif delta_record.operation == DeltaOperation.DELETE:
                categories["delete"].append(delta_record)

        return categories

    @staticmethod
    def get_metrics(categorized: dict[str, list[DeltaRecord]]) -> dict[str, int]:
        """
        Get delta metrics

        Args:
            categorized: Categorized delta records

        Returns:
            Dict with counts per operation
        """
        metrics = {
            "total": sum(len(records) for records in categorized.values()),
            "insert": len(categorized.get("insert", [])),
            "update": len(categorized.get("update", [])),
            "skip": len(categorized.get("skip", [])),
            "delete": len(categorized.get("delete", [])),
        }

        # Calculate efficiency
        actionable = metrics["insert"] + metrics["update"] + metrics["delete"]
        total = metrics["total"]
        if total > 0:
            metrics["efficiency_percent"] = round((actionable / total) * 100, 2)
        else:
            metrics["efficiency_percent"] = 0.0

        return metrics
