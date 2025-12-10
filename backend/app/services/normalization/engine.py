"""
Normalization Engine - Orchestrates 5-Layer Pipeline

Pipeline:
1. Type Coercion: Oracle → Python types
2. String Normalization: Trim, clean control chars
3. Numeric Normalization: Parse "10,000" → 10000
4. DateTime Normalization: Convert to ISO 8601
5. Field Mapping: Apply transformations and mappings
"""

from typing import Any
from loguru import logger

from app.services.normalization.layer_1_type_coercion import TypeCoercionLayer
from app.services.normalization.layer_2_string_normalization import StringNormalizationLayer
from app.services.normalization.layer_3_numeric_normalization import NumericNormalizationLayer
from app.services.normalization.layer_4_datetime_normalization import DateTimeNormalizationLayer
from app.services.normalization.layer_5_field_mapping import FieldMappingLayer


class NormalizationEngine:
    """
    5-Layer Normalization Engine

    Orchestrates the complete normalization pipeline for ERP data.
    """

    def __init__(
        self,
        field_mappings: list[dict[str, Any]] | None = None,
        oracle_metadata: dict[str, str] | None = None,
        numeric_fields: set[str] | None = None,
        datetime_fields: set[str] | None = None,
        date_fields: set[str] | None = None,
    ):
        """
        Initialize normalization engine

        Args:
            field_mappings: List of field mapping configurations
            oracle_metadata: Dict of field_name → oracle_type
            numeric_fields: Set of field names that are numeric
            datetime_fields: Set of field names that are datetime
            date_fields: Set of field names that are date only
        """
        self.oracle_metadata = oracle_metadata or {}
        self.numeric_fields = numeric_fields or set()
        self.datetime_fields = datetime_fields or set()
        self.date_fields = date_fields or set()

        # Initialize all layers
        self.layer_1 = TypeCoercionLayer()
        self.layer_2 = StringNormalizationLayer()
        self.layer_3 = NumericNormalizationLayer()
        self.layer_4 = DateTimeNormalizationLayer()
        self.layer_5 = FieldMappingLayer(field_mappings)

        logger.info("Normalization engine initialized with 5 layers")

    def normalize_row(
        self,
        row: dict[str, Any],
        track_stages: bool = False
    ) -> dict[str, Any] | dict[str, dict[str, Any]]:
        """
        Normalize a single row through all 5 layers

        Args:
            row: Raw row from APISmith
            track_stages: If True, return intermediate results for debugging

        Returns:
            Normalized row (or dict with all stages if track_stages=True)
        """
        stages = {"raw": row.copy()} if track_stages else None

        try:
            # Layer 1: Type Coercion
            row = self.layer_1.normalize_row(row, self.oracle_metadata)
            if track_stages:
                stages["after_layer_1_type_coercion"] = row.copy()

            # Layer 2: String Normalization
            row = self.layer_2.normalize_row(row)
            if track_stages:
                stages["after_layer_2_string_normalization"] = row.copy()

            # Layer 3: Numeric Normalization
            row = self.layer_3.normalize_row(row, self.numeric_fields)
            if track_stages:
                stages["after_layer_3_numeric_normalization"] = row.copy()

            # Layer 4: DateTime Normalization
            row = self.layer_4.normalize_row(row, self.datetime_fields, self.date_fields)
            if track_stages:
                stages["after_layer_4_datetime_normalization"] = row.copy()

            # Layer 5: Field Mapping
            row = self.layer_5.map_row(row)
            if track_stages:
                stages["after_layer_5_field_mapping"] = row.copy()

            if track_stages:
                stages["final"] = row
                return stages

            return row

        except Exception as e:
            logger.error(f"Normalization failed for row: {e}", exc_info=True)
            raise

    def normalize_batch(
        self,
        rows: list[dict[str, Any]],
        track_metrics: bool = True
    ) -> tuple[list[dict[str, Any]], dict[str, int]]:
        """
        Normalize a batch of rows

        Args:
            rows: List of raw rows from APISmith
            track_metrics: If True, return metrics

        Returns:
            Tuple of (normalized_rows, metrics)
        """
        normalized_rows = []
        metrics = {
            "total_rows": len(rows),
            "successful": 0,
            "failed": 0,
        }

        for i, row in enumerate(rows):
            try:
                normalized_row = self.normalize_row(row)
                normalized_rows.append(normalized_row)
                metrics["successful"] += 1
            except Exception as e:
                logger.error(f"Failed to normalize row {i}: {e}")
                metrics["failed"] += 1
                # Optionally: store failed row for retry
                # For now, we skip it

        if track_metrics:
            success_rate = (metrics["successful"] / metrics["total_rows"] * 100) if metrics["total_rows"] > 0 else 0
            metrics["success_rate"] = round(success_rate, 2)
            logger.info(
                f"Batch normalization complete: "
                f"{metrics['successful']}/{metrics['total_rows']} rows "
                f"({metrics['success_rate']}% success rate)"
            )

        return normalized_rows, metrics

    def validate_batch(
        self,
        rows: list[dict[str, Any]]
    ) -> tuple[list[dict[str, Any]], list[tuple[int, list[str]]]]:
        """
        Validate a batch of rows against mapping requirements

        Args:
            rows: List of normalized rows

        Returns:
            Tuple of (valid_rows, invalid_rows_with_errors)
                invalid_rows_with_errors: List of (row_index, error_messages)
        """
        valid_rows = []
        invalid_rows = []

        for i, row in enumerate(rows):
            is_valid, errors = self.layer_5.validate_row(row)
            if is_valid:
                valid_rows.append(row)
            else:
                invalid_rows.append((i, errors))
                logger.warning(f"Row {i} validation failed: {errors}")

        return valid_rows, invalid_rows


# Convenience function for single-shot normalization
def normalize_connector_data(
    rows: list[dict[str, Any]],
    field_mappings: list[dict[str, Any]] | None = None,
    oracle_metadata: dict[str, str] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Convenience function to normalize data from APISmith

    Args:
        rows: Raw rows from APISmith
        field_mappings: Field mapping configurations
        oracle_metadata: Oracle type metadata

    Returns:
        Tuple of (normalized_rows, metrics)
    """
    engine = NormalizationEngine(
        field_mappings=field_mappings,
        oracle_metadata=oracle_metadata,
    )
    return engine.normalize_batch(rows, track_metrics=True)
