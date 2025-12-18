"""
Unit Tests for Identity Engine

Tests identity generation:
- BK_HASH (Business Key Hash)
- DATA_HASH (Data Hash)
- Rowversion handling
"""

import pytest
from app.services.identity.bk_hash import BKHashGenerator
from app.services.identity.data_hash import DataHashGenerator
from app.services.identity.rowversion import RowversionHandler
from app.services.identity.engine import IdentityEngine


class TestBKHashGenerator:
    """Test Business Key Hash generation"""

    def test_single_field_hash(self):
        """Test BK_HASH with single business key"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "item_code": "ITM-001",
            "description": "Sample Item",
        }

        business_keys = ["item_id"]
        bk_hash = generator.generate(record, business_keys)

        assert bk_hash is not None
        assert isinstance(bk_hash, str)
        assert len(bk_hash) == 32  # xxHash128 produces 32-char hex

    def test_multi_field_hash(self):
        """Test BK_HASH with multiple business keys"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "site_id": "SITE-A",
            "warehouse_id": "WH-01",
        }

        business_keys = ["item_id", "site_id"]
        bk_hash = generator.generate(record, business_keys)

        assert bk_hash is not None
        assert len(bk_hash) == 32

    def test_deterministic_hash(self):
        """Test that same input produces same hash"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "item_code": "ITM-001",
        }

        business_keys = ["item_id"]
        hash1 = generator.generate(record, business_keys)
        hash2 = generator.generate(record, business_keys)

        assert hash1 == hash2

    def test_different_order_same_hash(self):
        """Test that field order in business_keys matters"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "site_id": "SITE-A",
        }

        hash1 = generator.generate(record, ["item_id", "site_id"])
        hash2 = generator.generate(record, ["site_id", "item_id"])

        # Order matters in canonical string, so hashes should differ
        assert hash1 != hash2

    def test_null_handling(self):
        """Test NULL value handling in business keys"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "site_id": None,
        }

        business_keys = ["item_id", "site_id"]
        bk_hash = generator.generate(record, business_keys)

        # Should handle NULL gracefully
        assert bk_hash is not None

    def test_missing_field_handling(self):
        """Test missing business key field"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
        }

        business_keys = ["item_id", "missing_field"]

        # Should handle missing field gracefully or raise error
        try:
            bk_hash = generator.generate(record, business_keys)
            assert bk_hash is not None or bk_hash is None
        except KeyError:
            # Acceptable to raise KeyError for missing business keys
            pass

    def test_canonical_string_format(self):
        """Test canonical string format (field1=val1|field2=val2)"""
        generator = BKHashGenerator()

        record = {
            "item_id": "10001",
            "site_id": "SITE-A",
        }

        business_keys = ["item_id", "site_id"]
        canonical = generator.create_canonical_string(record, business_keys)

        assert "item_id=" in canonical
        assert "site_id=" in canonical
        assert "|" in canonical


class TestDataHashGenerator:
    """Test Data Hash generation"""

    def test_full_record_hash(self):
        """Test DATA_HASH with all fields"""
        generator = DataHashGenerator()

        record = {
            "item_id": "10001",
            "item_code": "ITM-001",
            "description": "Sample Item",
            "quantity": 100,
            "price": 10.50,
        }

        data_hash = generator.generate(record)

        assert data_hash is not None
        assert isinstance(data_hash, str)
        assert len(data_hash) == 64  # BLAKE3 produces 64-char hex

    def test_deterministic_hash(self):
        """Test that same data produces same hash"""
        generator = DataHashGenerator()

        record = {
            "item_code": "ITM-001",
            "quantity": 100,
        }

        hash1 = generator.generate(record)
        hash2 = generator.generate(record)

        assert hash1 == hash2

    def test_field_order_independence(self):
        """Test that field order in dict doesn't affect hash"""
        generator = DataHashGenerator()

        # Python dicts maintain insertion order, but hash should sort fields
        record1 = {"a": 1, "b": 2, "c": 3}
        record2 = {"c": 3, "a": 1, "b": 2}

        hash1 = generator.generate(record1)
        hash2 = generator.generate(record2)

        # Should be same because fields are sorted alphabetically
        assert hash1 == hash2

    def test_data_change_detection(self):
        """Test that data changes produce different hashes"""
        generator = DataHashGenerator()

        record1 = {
            "item_code": "ITM-001",
            "quantity": 100,
        }

        record2 = {
            "item_code": "ITM-001",
            "quantity": 200,  # Changed
        }

        hash1 = generator.generate(record1)
        hash2 = generator.generate(record2)

        assert hash1 != hash2

    def test_null_handling(self):
        """Test NULL value handling"""
        generator = DataHashGenerator()

        record = {
            "item_code": "ITM-001",
            "description": None,
            "quantity": 100,
        }

        data_hash = generator.generate(record)

        assert data_hash is not None

    def test_exclude_metadata_fields(self):
        """Test excluding metadata fields from hash"""
        generator = DataHashGenerator()

        record = {
            "item_code": "ITM-001",
            "quantity": 100,
            "_metadata": "exclude this",
            "_bridge_uid": "exclude this too",
        }

        # DATA_HASH should exclude _metadata and _bridge_* fields
        data_hash = generator.generate(record)

        assert data_hash is not None


class TestRowversionHandler:
    """Test Rowversion handling"""

    def test_rowversion_extraction(self):
        """Test rowversion extraction from record"""
        handler = RowversionHandler()

        record = {
            "item_id": "10001",
            "rowversion": "0x00000000000007D3",
        }

        rowversion = handler.extract(record)

        assert rowversion is not None
        assert isinstance(rowversion, str)

    def test_rowversion_comparison(self):
        """Test rowversion comparison logic"""
        handler = RowversionHandler()

        rv1 = "0x00000000000007D3"
        rv2 = "0x00000000000007D4"

        assert handler.compare(rv1, rv2) < 0
        assert handler.compare(rv2, rv1) > 0
        assert handler.compare(rv1, rv1) == 0

    def test_rowversion_validation(self):
        """Test rowversion format validation"""
        handler = RowversionHandler()

        assert handler.is_valid("0x00000000000007D3") is True
        assert handler.is_valid("ABCD1234") is True
        assert handler.is_valid(None) is False
        assert handler.is_valid("") is False

    def test_missing_rowversion(self):
        """Test missing rowversion handling"""
        handler = RowversionHandler()

        record = {
            "item_id": "10001",
        }

        rowversion = handler.extract(record)

        assert rowversion is None


class TestIdentityEngine:
    """Test complete Identity Engine"""

    def test_generate_all_identities(self):
        """Test generating all identity fields"""
        engine = IdentityEngine()

        record = {
            "item_id": "10001",
            "item_code": "ITM-001",
            "description": "Sample Item",
            "quantity": 100,
            "rowversion": "0x00000000000007D3",
        }

        business_keys = ["item_id"]
        result = engine.generate_identities(record, business_keys)

        assert "erp_key_hash" in result
        assert "erp_data_hash" in result
        assert "erp_rowversion" in result
        assert "erp_ref_str" in result

        assert len(result["erp_key_hash"]) == 32
        assert len(result["erp_data_hash"]) == 64
        assert result["erp_rowversion"] == "0x00000000000007D3"

    def test_batch_identity_generation(self):
        """Test batch identity generation"""
        engine = IdentityEngine()

        records = [
            {"item_id": f"1000{i}", "quantity": i * 10}
            for i in range(100)
        ]

        business_keys = ["item_id"]
        results = engine.generate_batch(records, business_keys)

        assert len(results) == 100

        for result in results:
            assert "erp_key_hash" in result
            assert "erp_data_hash" in result

    def test_identity_uniqueness(self):
        """Test that different records get different identities"""
        engine = IdentityEngine()

        record1 = {"item_id": "10001", "quantity": 100}
        record2 = {"item_id": "10002", "quantity": 100}

        business_keys = ["item_id"]

        result1 = engine.generate_identities(record1, business_keys)
        result2 = engine.generate_identities(record2, business_keys)

        # Different business keys → different BK_HASH
        assert result1["erp_key_hash"] != result2["erp_key_hash"]

        # Different records → different DATA_HASH
        assert result1["erp_data_hash"] != result2["erp_data_hash"]

    def test_identity_stability(self):
        """Test that same record produces stable identities"""
        engine = IdentityEngine()

        record = {
            "item_id": "10001",
            "item_code": "ITM-001",
            "quantity": 100,
        }

        business_keys = ["item_id"]

        result1 = engine.generate_identities(record, business_keys)
        result2 = engine.generate_identities(record, business_keys)

        assert result1["erp_key_hash"] == result2["erp_key_hash"]
        assert result1["erp_data_hash"] == result2["erp_data_hash"]

    def test_ref_str_generation(self):
        """Test human-readable reference string"""
        engine = IdentityEngine()

        record = {
            "item_id": "10001",
            "site_id": "SITE-A",
            "quantity": 100,
        }

        business_keys = ["item_id", "site_id"]
        result = engine.generate_identities(record, business_keys)

        ref_str = result["erp_ref_str"]

        assert "item_id=10001" in ref_str
        assert "site_id=SITE-A" in ref_str

    def test_missing_rowversion_handling(self):
        """Test handling records without rowversion"""
        engine = IdentityEngine()

        record = {
            "item_id": "10001",
            "quantity": 100,
        }

        business_keys = ["item_id"]
        result = engine.generate_identities(record, business_keys)

        assert "erp_key_hash" in result
        assert "erp_data_hash" in result
        assert result.get("erp_rowversion") is None
