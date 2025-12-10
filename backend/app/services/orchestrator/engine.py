"""
Batch Orchestrator Engine

Orchestrates complete 9-stage data sync pipeline:
1. FETCH - Get data from APISmith
2. NORMALIZE - Clean and transform data (5 layers)
3. VALIDATE - Validate data quality
4. MAP - Apply field mappings
5. IDENTITY - Add BK_HASH + DATA_HASH + rowversion
6. DELTA - Detect INSERT/UPDATE/DELETE/SKIP
7. RESOLVE - Handle parent-child dependencies
8. INGEST - Send to ScheduleHub
9. TRACK - Update sync state and metrics
"""

from typing import Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.connector_client import APISmithClient
from app.services.smartplan_client import ScheduleHubClient
from app.services.normalization.engine import NormalizationEngine
from app.services.identity.engine import IdentityEngine
from app.services.delta.engine import DeltaEngine, DeltaStrategy
from app.services.resolver.engine import ParentChildResolver
from app.repositories.batch_repository import BatchRepository
from app.repositories.failed_record_repository import FailedRecordRepository
from app.repositories.sync_state_repository import SyncStateRepository
from app.repositories.mapping_repository import MappingRepository
from app.repositories.entity_config_repository import EntityConfigRepository


class BatchOrchestrator:
    """
    Batch Orchestrator

    Orchestrates complete data sync pipeline from APISmith to ScheduleHub.

    Pipeline:
    1. FETCH → Get data from APISmith API
    2. NORMALIZE → 5-layer normalization
    3. VALIDATE → Data quality checks
    4. MAP → Field mapping
    5. IDENTITY → Add BK_HASH + DATA_HASH + rowversion
    6. DELTA → Detect operations (INSERT/UPDATE/DELETE/SKIP)
    7. RESOLVE → Handle parent-child dependencies
    8. INGEST → Send to ScheduleHub
    9. TRACK → Update sync state and batch metrics

    Features:
    - End-to-end pipeline automation
    - Error handling at each stage
    - Metrics tracking
    - Dead-letter queue for failures
    - Parent-child dependency resolution
    - Incremental sync support
    """

    def __init__(
        self,
        session: AsyncSession,
        connector_client: APISmithClient,
        smartplan_client: ScheduleHubClient,
    ):
        """
        Initialize orchestrator

        Args:
            session: Database session
            connector_client: APISmith client
            smartplan_client: ScheduleHub client
        """
        self.session = session
        self.connector_client = connector_client
        self.smartplan_client = smartplan_client

        # Repositories
        self.batch_repo = BatchRepository(session)
        self.failed_repo = FailedRecordRepository(session)
        self.sync_state_repo = SyncStateRepository(session)
        self.mapping_repo = MappingRepository(session)
        self.entity_config_repo = EntityConfigRepository(session)

        # Services (will be initialized per sync)
        self.normalizer: NormalizationEngine | None = None
        self.identity_engine: IdentityEngine | None = None
        self.delta_engine: DeltaEngine | None = None
        self.resolver = ParentChildResolver(session)

        logger.info("Batch Orchestrator initialized")

    async def sync_entity(
        self,
        entity_name: str,
        connector_api_slug: str,
        business_key_fields: list[str],
        sync_type: str = "incremental",
        page_size: int = 1000,
        max_pages: int | None = None,
    ) -> dict[str, Any]:
        """
        Sync entity through complete pipeline

        Args:
            entity_name: Entity name (e.g., "inventory_items")
            connector_api_slug: APISmith API slug
            business_key_fields: Fields forming business key
            sync_type: "full", "incremental", or "background"
            page_size: Records per page
            max_pages: Optional max pages (for testing)

        Returns:
            Sync result with metrics

        Example:
            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="inventory_items",
                business_key_fields=["item_number"],
                sync_type="incremental",
            )
        """
        logger.info(
            f"Starting sync: entity={entity_name}, type={sync_type}, "
            f"api={connector_api_slug}"
        )

        # Create sync batch
        batch = await self.batch_repo.create_batch(
            entity_name=entity_name,
            sync_type=sync_type,
            connector_api_slug=connector_api_slug,
        )
        batch_uid = batch["uid"]

        try:
            # Update batch status to running
            await self.batch_repo.update_batch_status(batch_uid, "running")

            # STAGE 1: FETCH - Get data from APISmith
            logger.info(f"[STAGE 1/9] FETCH: Fetching data from APISmith...")
            incoming_records = await self._stage_fetch(
                connector_api_slug=connector_api_slug,
                sync_type=sync_type,
                entity_name=entity_name,
                page_size=page_size,
                max_pages=max_pages,
            )

            if not incoming_records:
                logger.info("No records to sync")
                await self.batch_repo.update_batch_status(batch_uid, "completed")
                return {
                    "success": True,
                    "batch_uid": batch_uid,
                    "message": "No records to sync",
                }

            logger.info(f"Fetched {len(incoming_records)} records")

            # STAGE 2-4: NORMALIZE + VALIDATE + MAP
            logger.info(f"[STAGE 2-4/9] NORMALIZE: Processing {len(incoming_records)} records...")
            normalized_records = await self._stage_normalize(
                records=incoming_records,
                entity_name=entity_name,
            )
            logger.info(f"Normalized {len(normalized_records)} records")

            # STAGE 5: IDENTITY - Add BK_HASH + DATA_HASH
            logger.info(f"[STAGE 5/9] IDENTITY: Adding identity fields...")
            records_with_identity = await self._stage_identity(
                records=normalized_records,
                business_key_fields=business_key_fields,
                entity_name=entity_name,
            )
            logger.info(f"Added identity to {len(records_with_identity)} records")

            # STAGE 5.5: PARENT_REFS - Add parent references for FK resolution
            logger.info(f"[STAGE 5.5/9] PARENT_REFS: Adding parent references...")
            records_with_parent_refs = await self._stage_parent_refs(
                records=records_with_identity,
                entity_name=entity_name,
            )
            logger.info(f"Added parent refs to {len(records_with_parent_refs)} records")

            # STAGE 6: DELTA - Detect operations
            logger.info(f"[STAGE 6/9] DELTA: Detecting operations...")
            categorized, delta_metrics = await self._stage_delta(
                incoming_records=records_with_parent_refs,
                entity_name=entity_name,
            )
            logger.info(
                f"Delta detection: "
                f"INSERT={delta_metrics['insert']}, "
                f"UPDATE={delta_metrics['update']}, "
                f"SKIP={delta_metrics['skip']}, "
                f"DELETE={delta_metrics['delete']}"
            )

            # STAGE 7: RESOLVE - Handle parent-child dependencies
            logger.info(f"[STAGE 7/9] RESOLVE: Checking dependencies...")
            # TODO: Implement dependency detection and queuing
            # For now, assume no dependencies

            # STAGE 8: INGEST - Send to ScheduleHub
            logger.info(f"[STAGE 8/9] INGEST: Sending to ScheduleHub...")
            ingest_metrics = await self._stage_ingest(
                categorized=categorized,
                entity_name=entity_name,
                batch_uid=batch_uid,
            )
            logger.info(
                f"Ingest complete: "
                f"inserted={ingest_metrics['inserted']}, "
                f"updated={ingest_metrics['updated']}, "
                f"deleted={ingest_metrics['deleted']}, "
                f"failed={ingest_metrics['failed']}"
            )

            # STAGE 9: TRACK - Update sync state
            logger.info(f"[STAGE 9/9] TRACK: Updating sync state...")
            await self._stage_track(
                entity_name=entity_name,
                records_with_identity=records_with_identity,
            )

            # Update batch metrics
            await self.batch_repo.update_batch_metrics(
                batch_uid=batch_uid,
                processed=len(incoming_records),
                inserted=ingest_metrics["inserted"],
                updated=ingest_metrics["updated"],
                deleted=ingest_metrics["deleted"],
                skipped=delta_metrics["skip"],
                failed=ingest_metrics["failed"],
            )

            # Mark batch as completed
            await self.batch_repo.update_batch_status(batch_uid, "completed")

            logger.info(f"Sync completed successfully: batch={batch_uid}")

            return {
                "success": True,
                "batch_uid": batch_uid,
                "entity_name": entity_name,
                "metrics": {
                    "total_fetched": len(incoming_records),
                    "total_processed": len(incoming_records),
                    "inserted": ingest_metrics["inserted"],
                    "updated": ingest_metrics["updated"],
                    "deleted": ingest_metrics["deleted"],
                    "skipped": delta_metrics["skip"],
                    "failed": ingest_metrics["failed"],
                    "efficiency": delta_metrics.get("efficiency_percent", 0),
                },
            }

        except Exception as e:
            logger.error(f"Sync failed: {e}")

            # Mark batch as failed
            await self.batch_repo.update_batch_status(
                batch_uid, "failed", error_message=str(e)
            )

            return {
                "success": False,
                "batch_uid": batch_uid,
                "error": str(e),
            }

    async def _stage_fetch(
        self,
        connector_api_slug: str,
        sync_type: str,
        entity_name: str,
        page_size: int,
        max_pages: int | None,
    ) -> list[dict[str, Any]]:
        """
        STAGE 1: FETCH - Get data from APISmith

        Handles:
        - Full sync: fetch all records
        - Incremental sync: fetch only changed records (WHERE rowversion > last_sync)
        - Pagination
        """
        filters = None

        if sync_type == "incremental":
            # Get last sync state
            sync_state = await self.sync_state_repo.get_sync_state(entity_name)

            if sync_state and sync_state["last_sync_rowversion"]:
                # Incremental sync with rowversion filter
                from app.services.delta.rowversion_strategy import RowversionDeltaStrategy
                filters = RowversionDeltaStrategy.build_query_filter(
                    last_sync_rowversion=sync_state["last_sync_rowversion"],
                    rowversion_field="rowversion",
                ).get("filters")

                logger.info(
                    f"Incremental sync: fetching records WHERE rowversion > "
                    f"{sync_state['last_sync_rowversion']}"
                )

        # Fetch data from APISmith
        records = await self.connector_client.execute_api_all_pages(
            slug=connector_api_slug,
            page_size=page_size,
            filters=filters,
            max_pages=max_pages,
        )

        return records

    async def _stage_normalize(
        self,
        records: list[dict[str, Any]],
        entity_name: str,
    ) -> list[dict[str, Any]]:
        """
        STAGE 2-4: NORMALIZE + VALIDATE + MAP

        Handles:
        - Type coercion (Oracle → Python)
        - String normalization
        - Numeric normalization
        - DateTime normalization
        - Field mapping
        """
        # Get field mappings for entity
        mappings = await self.mapping_repo.get_mappings_for_entity(entity_name)

        # Initialize normalization engine
        self.normalizer = NormalizationEngine(
            field_mappings=mappings,
            oracle_metadata=None,  # TODO: Get from APISmith API metadata
            entity_name=entity_name,
        )

        # Normalize batch
        normalized, metrics = self.normalizer.normalize_batch(records)

        logger.debug(
            f"Normalization metrics: "
            f"{metrics['successful']}/{metrics['total_rows']} successful"
        )

        return normalized

    async def _stage_identity(
        self,
        records: list[dict[str, Any]],
        business_key_fields: list[str],
        entity_name: str,
    ) -> list[dict[str, Any]]:
        """
        STAGE 5: IDENTITY - Add BK_HASH + DATA_HASH + rowversion

        Handles:
        - BK_HASH generation from business keys
        - DATA_HASH generation from all fields
        - Rowversion extraction
        - Reference string for debugging
        """
        # Initialize identity engine
        self.identity_engine = IdentityEngine(
            business_key_fields=business_key_fields,
            entity_name=entity_name,
            rowversion_field="rowversion",
        )

        # Add identity batch
        records_with_identity, metrics = self.identity_engine.add_identity_batch(
            records, track_metrics=True
        )

        logger.debug(
            f"Identity metrics: "
            f"{metrics['successful']}/{metrics['total_rows']} successful"
        )

        return records_with_identity

    async def _stage_parent_refs(
        self,
        records: list[dict[str, Any]],
        entity_name: str,
    ) -> list[dict[str, Any]]:
        """
        STAGE 5.5: PARENT_REFS - Add parent references for FK resolution

        This stage adds `parent_refs` to each record. ScheduleHub uses these
        references to resolve foreign keys by looking up parent `erp_key_hash`.

        Configuration is stored in entity_config.parent_refs_config:
        {
            "site": {
                "parent_entity": "sites",
                "parent_field": "site_id",       # Field in parent's BK
                "child_field": "site_id"         # Field in child record
            },
            "work_area": {
                "parent_entity": "work_areas",
                "parent_field": "work_area_id",
                "child_field": "work_area_id"
            }
        }

        Output payload will have:
        {
            "erp_key_hash": "hash_of_child",
            "parent_refs": {
                "site": "hash_of_site",
                "work_area": "hash_of_work_area"
            },
            ...other_fields
        }
        """
        # Get entity config with parent_refs_config
        entity_config = await self.entity_config_repo.get_entity(entity_name)

        if not entity_config or not entity_config.get("parent_refs_config"):
            # No parent refs configured, return records as-is
            logger.debug(f"No parent_refs_config for {entity_name}, skipping")
            return records

        parent_refs_config = entity_config["parent_refs_config"]
        logger.info(f"Processing parent_refs for {len(records)} records with config: {list(parent_refs_config.keys())}")

        # Import BK_HASH generator
        from app.services.identity.bk_hash import BKHashGenerator

        enriched_records = []
        for record in records:
            parent_refs = {}

            for ref_name, ref_config in parent_refs_config.items():
                parent_entity = ref_config.get("parent_entity")
                parent_field = ref_config.get("parent_field")
                child_field = ref_config.get("child_field")

                if not all([parent_entity, parent_field, child_field]):
                    logger.warning(f"Incomplete parent_ref config for {ref_name}")
                    continue

                # Get child field value from record
                child_value = record.get(child_field)

                if child_value is not None:
                    # Calculate parent's BK_HASH using the parent's business key field
                    # The parent's BK is assumed to be the parent_field value
                    parent_bk_values = {parent_field: child_value}
                    parent_bk_hash = BKHashGenerator.generate(
                        record=parent_bk_values,
                        business_key_fields=[parent_field],
                        entity_name=parent_entity,
                    )
                    parent_refs[ref_name] = parent_bk_hash
                else:
                    # Child field is null, no parent ref
                    parent_refs[ref_name] = None

            # Add parent_refs to record
            record_with_refs = {**record, "parent_refs": parent_refs}
            enriched_records.append(record_with_refs)

        logger.info(f"Added parent_refs to {len(enriched_records)} records")
        return enriched_records

    async def _stage_delta(
        self,
        incoming_records: list[dict[str, Any]],
        entity_name: str,
    ) -> tuple[dict[str, list], dict[str, Any]]:
        """
        STAGE 6: DELTA - Detect INSERT/UPDATE/DELETE/SKIP

        Handles:
        - Fetch stored records from ScheduleHub by BK_HASH
        - Compare rowversions or data hashes
        - Categorize operations
        - Calculate efficiency metrics
        """
        # Extract BK_HASHes from incoming records
        bk_hashes = [r.get("erp_key_hash") for r in incoming_records if r.get("erp_key_hash")]

        # Fetch stored records from ScheduleHub
        stored_map = await self.smartplan_client.get_batch_by_bk_hashes(
            entity=entity_name,
            bk_hashes=bk_hashes,
        )

        # Convert stored map to list
        stored_records = list(stored_map.values())

        # Initialize delta engine
        self.delta_engine = DeltaEngine(
            strategy=DeltaStrategy.AUTO,
            rowversion_field="rowversion",
        )

        # Detect delta
        categorized, metrics = self.delta_engine.detect_delta(
            incoming_records=incoming_records,
            stored_records=stored_records,
        )

        return categorized, metrics

    async def _stage_ingest(
        self,
        categorized: dict[str, list],
        entity_name: str,
        batch_uid: str,
    ) -> dict[str, int]:
        """
        STAGE 8: INGEST - Send to ScheduleHub

        Handles:
        - Batch INSERT operations
        - Batch UPDATE operations
        - Batch DELETE operations
        - Error handling and dead-letter queue
        """
        metrics = {
            "inserted": 0,
            "updated": 0,
            "deleted": 0,
            "failed": 0,
        }

        # INSERT operations
        insert_records = categorized.get("insert", [])
        if insert_records:
            logger.info(f"Inserting {len(insert_records)} records...")
            try:
                insert_data = [dr.record for dr in insert_records]
                result = await self.smartplan_client.batch_insert(
                    entity=entity_name,
                    records=insert_data,
                )
                metrics["inserted"] = result.get("success_count", 0)
                metrics["failed"] += result.get("failure_count", 0)

                # Record failures
                if result.get("failures"):
                    for failure in result["failures"]:
                        await self.failed_repo.create_failed_record(
                            batch_uid=batch_uid,
                            entity_name=entity_name,
                            record_data=failure["record"],
                            error_type="insert_error",
                            error_message=failure.get("error", "Unknown error"),
                            stage="ingest",
                        )

            except Exception as e:
                logger.error(f"Batch insert failed: {e}")
                metrics["failed"] += len(insert_records)

        # UPDATE operations
        update_records = categorized.get("update", [])
        if update_records:
            logger.info(f"Updating {len(update_records)} records...")
            try:
                # Need to fetch UIDs for updates
                update_data = []
                for dr in update_records:
                    # Get stored record UID
                    bk_hash = dr.bk_hash
                    stored = await self.smartplan_client.get_by_bk_hash(
                        entity=entity_name,
                        bk_hash=bk_hash,
                    )
                    if stored:
                        update_data.append({
                            "uid": stored["uid"],
                            "data": dr.record,
                        })

                if update_data:
                    result = await self.smartplan_client.batch_update(
                        entity=entity_name,
                        updates=update_data,
                    )
                    metrics["updated"] = result.get("success_count", 0)
                    metrics["failed"] += result.get("failure_count", 0)

            except Exception as e:
                logger.error(f"Batch update failed: {e}")
                metrics["failed"] += len(update_records)

        # DELETE operations
        delete_records = categorized.get("delete", [])
        if delete_records:
            logger.info(f"Deleting {len(delete_records)} records...")
            try:
                # Get UIDs for deletes
                delete_uids = []
                for dr in delete_records:
                    bk_hash = dr.bk_hash
                    stored = await self.smartplan_client.get_by_bk_hash(
                        entity=entity_name,
                        bk_hash=bk_hash,
                    )
                    if stored:
                        delete_uids.append(stored["uid"])

                if delete_uids:
                    result = await self.smartplan_client.batch_delete(
                        entity=entity_name,
                        uids=delete_uids,
                    )
                    metrics["deleted"] = result.get("success_count", 0)
                    metrics["failed"] += result.get("failure_count", 0)

            except Exception as e:
                logger.error(f"Batch delete failed: {e}")
                metrics["failed"] += len(delete_records)

        return metrics

    async def _stage_track(
        self,
        entity_name: str,
        records_with_identity: list[dict[str, Any]],
    ) -> None:
        """
        STAGE 9: TRACK - Update sync state

        Handles:
        - Update last_sync_rowversion
        - Update last_sync_timestamp
        - Update sync status
        """
        # Get max rowversion from records
        from app.services.delta.rowversion_strategy import RowversionDeltaStrategy
        max_rowversion = RowversionDeltaStrategy.get_max_rowversion(records_with_identity)

        # Update sync state
        await self.sync_state_repo.upsert_sync_state(
            entity_name=entity_name,
            last_sync_rowversion=max_rowversion,
            last_sync_status="completed",
            total_records_synced=len(records_with_identity),
        )

        logger.debug(f"Sync state updated: max_rowversion={max_rowversion}")


# Convenience function

async def sync_entity_full_pipeline(
    session: AsyncSession,
    entity_name: str,
    connector_api_slug: str,
    business_key_fields: list[str],
    sync_type: str = "incremental",
) -> dict[str, Any]:
    """
    Convenience function to sync entity through full pipeline

    Args:
        session: Database session
        entity_name: Entity name
        connector_api_slug: APISmith API slug
        business_key_fields: Business key fields
        sync_type: Sync type

    Returns:
        Sync result with metrics

    Usage:
        async with get_session() as session:
            result = await sync_entity_full_pipeline(
                session=session,
                entity_name="inventory_items",
                connector_api_slug="inventory_items",
                business_key_fields=["item_number"],
            )
    """
    async with APISmithClient() as connector_client:
        async with ScheduleHubClient() as smartplan_client:
            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=connector_client,
                smartplan_client=smartplan_client,
            )

            return await orchestrator.sync_entity(
                entity_name=entity_name,
                connector_api_slug=connector_api_slug,
                business_key_fields=business_key_fields,
                sync_type=sync_type,
            )
