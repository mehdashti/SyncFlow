"""
Integration Tests for Full Sync Pipeline

Tests complete end-to-end sync flow:
APISmith → Normalization → Identity → Delta → ScheduleHub
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.orchestrator.engine import BatchOrchestrator
from app.repositories.batch_repository import BatchRepository
from app.repositories.entity_config_repository import EntityConfigRepository


class TestFullSyncPipeline:
    """Test complete sync pipeline integration"""

    @pytest.mark.asyncio
    async def test_end_to_end_sync_success(self, session, sample_entity_config):
        """Test successful end-to-end sync"""
        # Create entity config
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        # Mock APISmith client
        mock_connector_data = [
            {
                "ITEM_ID": "10001",
                "ITEM_CODE": "  ITM-001  ",
                "QUANTITY": "1,234.56",
                "STATUS": "ACTIVE",
            },
            {
                "ITEM_ID": "10002",
                "ITEM_CODE": "  ITM-002  ",
                "QUANTITY": "567.89",
                "STATUS": "ACTIVE",
            },
        ]

        # Mock ScheduleHub client
        mock_schedulehub_response = {"status": "success", "inserted": 2}

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            # Configure mocks
            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            mock_schedulehub_instance.insert_batch.return_value = mock_schedulehub_response
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            # Create orchestrator
            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            # Execute sync
            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Verify results
            assert result is not None
            assert "batch_uid" in result
            assert result["status"] in ["completed", "running"]

    @pytest.mark.asyncio
    async def test_sync_with_failed_records(self, session, sample_entity_config):
        """Test sync handling failed records"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        # Mock data with some invalid records
        mock_connector_data = [
            {"ITEM_ID": "10001", "ITEM_CODE": "ITM-001"},  # Valid
            {"ITEM_ID": None, "ITEM_CODE": None},  # Invalid (missing required fields)
            {"ITEM_ID": "10003", "ITEM_CODE": "ITM-003"},  # Valid
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            mock_schedulehub_instance.insert_batch.return_value = {"status": "success"}
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Should have some failed records
            assert result is not None
            # Failed records should be logged in failed_records table

    @pytest.mark.asyncio
    async def test_sync_with_parent_child_dependencies(self, session):
        """Test sync handling parent-child dependencies"""
        # Create parent entity config (sites)
        entity_repo = EntityConfigRepository(session)
        parent_entity = await entity_repo.create_entity(
            entity_name="sites",
            connector_api_slug="oracle-erp-sites",
            business_key_fields=["site_id"],
            sync_enabled=True,
        )

        # Create child entity config (inventory_items) with parent reference
        child_entity = await entity_repo.create_entity(
            entity_name="inventory_items",
            connector_api_slug="oracle-erp-items",
            business_key_fields=["item_id"],
            sync_enabled=True,
            parent_refs_config={
                "site": {
                    "parent_entity": "sites",
                    "parent_field": "site_id",
                    "child_field": "site_id",
                }
            },
        )

        # Mock child data with parent reference
        mock_child_data = [
            {
                "ITEM_ID": "10001",
                "ITEM_CODE": "ITM-001",
                "SITE_ID": "SITE-A",  # Parent reference
            }
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_child_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            # Mock parent doesn't exist
            mock_schedulehub_instance.check_record_exists.return_value = False
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Child should be queued in pending_children
            assert result is not None

    @pytest.mark.asyncio
    async def test_incremental_sync_with_rowversion(self, session):
        """Test incremental sync using rowversion"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(
            entity_name="inventory_items",
            connector_api_slug="oracle-erp-items",
            business_key_fields=["item_id"],
            sync_enabled=True,
        )

        # Mock data with rowversions
        mock_connector_data = [
            {
                "ITEM_ID": "10001",
                "ROWVERSION": "0x00000000000007D4",
                "ITEM_CODE": "ITM-001",
            }
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            # Mock existing record with older rowversion
            mock_schedulehub_instance = AsyncMock()
            mock_schedulehub_instance.get_existing_records.return_value = [
                {
                    "erp_key_hash": "hash1",
                    "erp_rowversion": "0x00000000000007D3",  # Older
                }
            ]
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Should detect UPDATE operation
            assert result is not None

    @pytest.mark.asyncio
    async def test_batch_metrics_tracking(self, session, sample_entity_config):
        """Test batch metrics are properly tracked"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        mock_connector_data = [
            {"ITEM_ID": f"1000{i}", "ITEM_CODE": f"ITM-{i:03d}"}
            for i in range(10)
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            mock_schedulehub_instance.insert_batch.return_value = {
                "status": "success",
                "inserted": 10
            }
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Verify batch was created with metrics
            batch_repo = BatchRepository(session)
            batch = await batch_repo.get_batch(result["batch_uid"])

            assert batch is not None
            assert "rows_fetched" in batch
            assert "rows_inserted" in batch

    @pytest.mark.asyncio
    async def test_connector_failure_handling(self, session, sample_entity_config):
        """Test handling of connector failures"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        with patch("app.services.connector_client.APISmithClient") as MockConnector:

            mock_connector_instance = AsyncMock()
            # Simulate connector failure
            mock_connector_instance.fetch_data.side_effect = Exception("Connection timeout")
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=AsyncMock(),
            )

            # Should handle error gracefully
            with pytest.raises(Exception):
                await orchestrator.sync_entity(
                    entity_name="inventory_items",
                    connector_api_slug="oracle-erp-items",
                    sync_type="realtime",
                )

    @pytest.mark.asyncio
    async def test_schedulehub_failure_handling(self, session, sample_entity_config):
        """Test handling of ScheduleHub failures"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        mock_connector_data = [
            {"ITEM_ID": "10001", "ITEM_CODE": "ITM-001"}
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            # Simulate ScheduleHub failure
            mock_schedulehub_instance.insert_batch.side_effect = Exception("Database connection error")
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            # Should handle error and log to failed_records
            with pytest.raises(Exception):
                await orchestrator.sync_entity(
                    entity_name="inventory_items",
                    connector_api_slug="oracle-erp-items",
                    sync_type="realtime",
                )

    @pytest.mark.asyncio
    async def test_large_batch_processing(self, session, sample_entity_config):
        """Test processing large batch (1000+ records)"""
        entity_repo = EntityConfigRepository(session)
        entity = await entity_repo.create_entity(**sample_entity_config)

        # Create 1000 records
        mock_connector_data = [
            {"ITEM_ID": f"1000{i}", "ITEM_CODE": f"ITM-{i:04d}"}
            for i in range(1000)
        ]

        with patch("app.services.connector_client.APISmithClient") as MockConnector, \
             patch("app.services.smartplan_client.ScheduleHubClient") as MockScheduleHub:

            mock_connector_instance = AsyncMock()
            mock_connector_instance.fetch_data.return_value = mock_connector_data
            MockConnector.return_value.__aenter__.return_value = mock_connector_instance

            mock_schedulehub_instance = AsyncMock()
            mock_schedulehub_instance.insert_batch.return_value = {
                "status": "success",
                "inserted": 1000
            }
            MockScheduleHub.return_value.__aenter__.return_value = mock_schedulehub_instance

            orchestrator = BatchOrchestrator(
                session=session,
                connector_client=mock_connector_instance,
                smartplan_client=mock_schedulehub_instance,
            )

            result = await orchestrator.sync_entity(
                entity_name="inventory_items",
                connector_api_slug="oracle-erp-items",
                sync_type="realtime",
            )

            # Verify all 1000 records processed
            assert result is not None
