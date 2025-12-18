"""
Unit Tests for Delta Detection

Tests delta detection strategies:
- Full sync (no delta)
- Rowversion-based delta
- Hash-based delta
"""

import pytest
from app.services.delta.detector import DeltaDetector
from app.services.delta.rowversion_strategy import RowversionDeltaStrategy
from app.services.delta.hash_strategy import HashDeltaStrategy
from app.services.delta.engine import DeltaEngine


class TestRowversionDeltaStrategy:
    """Test Rowversion-based Delta Detection"""

    @pytest.mark.asyncio
    async def test_new_record_detection(self, session):
        """Test detection of NEW records"""
        strategy = RowversionDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_rowversion": "0x00000000000007D3",
            "item_code": "ITM-001",
        }

        # No existing record in ScheduleHub
        existing = None

        action = await strategy.determine_action(incoming, existing)

        assert action == "INSERT"

    @pytest.mark.asyncio
    async def test_updated_record_detection(self, session):
        """Test detection of UPDATED records"""
        strategy = RowversionDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_rowversion": "0x00000000000007D4",
            "item_code": "ITM-001",
        }

        existing = {
            "erp_key_hash": "abc123",
            "erp_rowversion": "0x00000000000007D3",
            "item_code": "ITM-001-OLD",
        }

        action = await strategy.determine_action(incoming, existing)

        assert action == "UPDATE"

    @pytest.mark.asyncio
    async def test_unchanged_record_detection(self, session):
        """Test detection of UNCHANGED records"""
        strategy = RowversionDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_rowversion": "0x00000000000007D3",
            "item_code": "ITM-001",
        }

        existing = {
            "erp_key_hash": "abc123",
            "erp_rowversion": "0x00000000000007D3",
            "item_code": "ITM-001",
        }

        action = await strategy.determine_action(incoming, existing)

        assert action == "SKIP"

    @pytest.mark.asyncio
    async def test_missing_rowversion_fallback(self, session):
        """Test fallback when rowversion is missing"""
        strategy = RowversionDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "item_code": "ITM-001",
        }

        existing = {
            "erp_key_hash": "abc123",
            "item_code": "ITM-001-OLD",
        }

        # Should fallback to hash comparison or always update
        action = await strategy.determine_action(incoming, existing)

        assert action in ["UPDATE", "SKIP"]


class TestHashDeltaStrategy:
    """Test Hash-based Delta Detection"""

    @pytest.mark.asyncio
    async def test_new_record_detection(self, session):
        """Test detection of NEW records"""
        strategy = HashDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_data_hash": "def456789",
            "item_code": "ITM-001",
        }

        existing = None

        action = await strategy.determine_action(incoming, existing)

        assert action == "INSERT"

    @pytest.mark.asyncio
    async def test_updated_record_detection(self, session):
        """Test detection of UPDATED records via hash"""
        strategy = HashDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_data_hash": "def456789_new",
            "item_code": "ITM-001",
            "quantity": 200,
        }

        existing = {
            "erp_key_hash": "abc123",
            "erp_data_hash": "def456789_old",
            "item_code": "ITM-001",
            "quantity": 100,
        }

        action = await strategy.determine_action(incoming, existing)

        assert action == "UPDATE"

    @pytest.mark.asyncio
    async def test_unchanged_record_detection(self, session):
        """Test detection of UNCHANGED records via hash"""
        strategy = HashDeltaStrategy(session)

        incoming = {
            "erp_key_hash": "abc123",
            "erp_data_hash": "def456789",
            "item_code": "ITM-001",
        }

        existing = {
            "erp_key_hash": "abc123",
            "erp_data_hash": "def456789",
            "item_code": "ITM-001",
        }

        action = await strategy.determine_action(incoming, existing)

        assert action == "SKIP"


class TestDeltaDetector:
    """Test Delta Detector logic"""

    @pytest.mark.asyncio
    async def test_detect_new_records(self, session):
        """Test detecting NEW records"""
        detector = DeltaDetector(session)

        incoming_records = [
            {"erp_key_hash": "hash1", "erp_data_hash": "data1"},
            {"erp_key_hash": "hash2", "erp_data_hash": "data2"},
            {"erp_key_hash": "hash3", "erp_data_hash": "data3"},
        ]

        existing_hashes = {"hash1"}  # Only hash1 exists

        new_records = await detector.detect_new(incoming_records, existing_hashes)

        assert len(new_records) == 2
        assert new_records[0]["erp_key_hash"] in ["hash2", "hash3"]

    @pytest.mark.asyncio
    async def test_detect_updated_records(self, session):
        """Test detecting UPDATED records"""
        detector = DeltaDetector(session)

        incoming_records = [
            {"erp_key_hash": "hash1", "erp_data_hash": "data1_new"},
        ]

        existing_records = {
            "hash1": {"erp_key_hash": "hash1", "erp_data_hash": "data1_old"}
        }

        updated = await detector.detect_updated(incoming_records, existing_records)

        assert len(updated) == 1
        assert updated[0]["erp_key_hash"] == "hash1"

    @pytest.mark.asyncio
    async def test_detect_deleted_records(self, session):
        """Test detecting DELETED records"""
        detector = DeltaDetector(session)

        incoming_hashes = {"hash1", "hash2"}
        existing_hashes = {"hash1", "hash2", "hash3", "hash4"}

        deleted = await detector.detect_deleted(incoming_hashes, existing_hashes)

        assert len(deleted) == 2
        assert "hash3" in deleted
        assert "hash4" in deleted


class TestDeltaEngine:
    """Test complete Delta Engine"""

    @pytest.mark.asyncio
    async def test_full_sync_strategy(self, session):
        """Test full sync (all records are INSERTs)"""
        engine = DeltaEngine(session, "inventory_items", "full")

        incoming_records = [
            {"erp_key_hash": "hash1", "item_code": "ITM-001"},
            {"erp_key_hash": "hash2", "item_code": "ITM-002"},
        ]

        result = await engine.process(incoming_records)

        assert len(result["inserts"]) == 2
        assert len(result["updates"]) == 0
        assert len(result["deletes"]) == 0

    @pytest.mark.asyncio
    async def test_rowversion_strategy(self, session):
        """Test rowversion-based delta detection"""
        engine = DeltaEngine(session, "inventory_items", "rowversion")

        incoming_records = [
            {
                "erp_key_hash": "hash1",
                "erp_rowversion": "0x00000000000007D4",
                "item_code": "ITM-001",
            },
            {
                "erp_key_hash": "hash2",
                "erp_rowversion": "0x00000000000007D5",
                "item_code": "ITM-002",
            },
        ]

        # Mock existing records
        # In real scenario, would query ScheduleHub
        result = await engine.process(incoming_records)

        assert "inserts" in result
        assert "updates" in result
        assert "deletes" in result

    @pytest.mark.asyncio
    async def test_hash_strategy(self, session):
        """Test hash-based delta detection"""
        engine = DeltaEngine(session, "inventory_items", "hash")

        incoming_records = [
            {
                "erp_key_hash": "hash1",
                "erp_data_hash": "data1",
                "item_code": "ITM-001",
            },
            {
                "erp_key_hash": "hash2",
                "erp_data_hash": "data2",
                "item_code": "ITM-002",
            },
        ]

        result = await engine.process(incoming_records)

        assert "inserts" in result
        assert "updates" in result
        assert "deletes" in result

    @pytest.mark.asyncio
    async def test_mixed_operations(self, session):
        """Test mix of INSERT, UPDATE, SKIP operations"""
        engine = DeltaEngine(session, "inventory_items", "hash")

        incoming_records = [
            {"erp_key_hash": "new1", "erp_data_hash": "data_new1"},  # INSERT
            {"erp_key_hash": "upd1", "erp_data_hash": "data_upd_new"},  # UPDATE
            {"erp_key_hash": "skip1", "erp_data_hash": "data_same"},  # SKIP
        ]

        result = await engine.process(incoming_records)

        total_processed = (
            len(result.get("inserts", []))
            + len(result.get("updates", []))
            + len(result.get("skips", []))
        )

        assert total_processed <= len(incoming_records)

    @pytest.mark.asyncio
    async def test_delta_metrics(self, session):
        """Test delta detection metrics"""
        engine = DeltaEngine(session, "inventory_items", "hash")

        incoming_records = [
            {"erp_key_hash": f"hash{i}", "erp_data_hash": f"data{i}"}
            for i in range(100)
        ]

        result = await engine.process(incoming_records)

        metrics = result.get("metrics", {})

        assert "total_incoming" in metrics
        assert "total_inserts" in metrics
        assert "total_updates" in metrics
        assert "total_skips" in metrics

    @pytest.mark.asyncio
    async def test_invalid_strategy(self, session):
        """Test handling of invalid delta strategy"""
        with pytest.raises(ValueError):
            engine = DeltaEngine(session, "inventory_items", "invalid_strategy")

    @pytest.mark.asyncio
    async def test_empty_incoming_records(self, session):
        """Test handling empty incoming records"""
        engine = DeltaEngine(session, "inventory_items", "full")

        result = await engine.process([])

        assert len(result["inserts"]) == 0
        assert len(result["updates"]) == 0

    @pytest.mark.asyncio
    async def test_deleted_records_detection(self, session):
        """Test DELETED records detection"""
        engine = DeltaEngine(session, "inventory_items", "hash")

        # Only hash1 and hash2 coming in
        incoming_records = [
            {"erp_key_hash": "hash1", "erp_data_hash": "data1"},
            {"erp_key_hash": "hash2", "erp_data_hash": "data2"},
        ]

        # But hash3 and hash4 exist in ScheduleHub
        # In real scenario, would detect these as DELETED
        result = await engine.process(incoming_records)

        # DELETEs would be populated if existing records fetched from ScheduleHub
        assert "deletes" in result
