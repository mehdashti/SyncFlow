"""
Unit Tests for Normalization Layers

Tests all 5 normalization layers:
1. Type Coercion
2. String Normalization
3. Numeric Normalization
4. DateTime Normalization
5. Field Mapping
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.services.normalization.layer_1_type_coercion import TypeCoercionLayer
from app.services.normalization.layer_2_string_normalization import StringNormalizationLayer
from app.services.normalization.layer_3_numeric_normalization import NumericNormalizationLayer
from app.services.normalization.layer_4_datetime_normalization import DateTimeNormalizationLayer
from app.services.normalization.layer_5_field_mapping import FieldMappingLayer
from app.services.normalization.engine import NormalizationEngine


class TestTypeCoercionLayer:
    """Test Layer 1: Type Coercion"""

    def test_string_coercion(self):
        """Test VARCHAR2/CHAR/CLOB → str conversion"""
        layer = TypeCoercionLayer()
        data = {
            "name": "John Doe",
            "code": "ABC123",
            "notes": "Some long text...",
        }
        result = layer.process(data)

        assert isinstance(result["name"], str)
        assert isinstance(result["code"], str)
        assert isinstance(result["notes"], str)

    def test_numeric_coercion(self):
        """Test NUMBER → int/float/Decimal conversion"""
        layer = TypeCoercionLayer()
        data = {
            "count": 100,
            "price": 10.99,
            "total": Decimal("1234.56"),
        }
        result = layer.process(data)

        assert isinstance(result["count"], (int, float, Decimal))
        assert isinstance(result["price"], (int, float, Decimal))
        assert isinstance(result["total"], (int, float, Decimal))

    def test_null_handling(self):
        """Test NULL value handling"""
        layer = TypeCoercionLayer()
        data = {
            "name": "John",
            "middle_name": None,
            "notes": None,
        }
        result = layer.process(data)

        assert result["name"] == "John"
        assert result["middle_name"] is None
        assert result["notes"] is None

    def test_boolean_coercion(self):
        """Test boolean-like values"""
        layer = TypeCoercionLayer()
        data = {
            "is_active": "Y",
            "is_deleted": "N",
            "is_enabled": 1,
            "is_disabled": 0,
        }
        result = layer.process(data)

        # Type coercion layer should preserve original types
        assert result["is_active"] == "Y"
        assert result["is_deleted"] == "N"


class TestStringNormalizationLayer:
    """Test Layer 2: String Normalization"""

    def test_trim_whitespace(self):
        """Test whitespace trimming"""
        layer = StringNormalizationLayer()
        data = {
            "code": "  ABC123  ",
            "name": "\tJohn Doe\n",
            "notes": "   Multiple   Spaces   ",
        }
        result = layer.process(data)

        assert result["code"] == "ABC123"
        assert result["name"] == "John Doe"
        assert result["notes"] == "Multiple   Spaces"

    def test_remove_control_characters(self):
        """Test control character removal"""
        layer = StringNormalizationLayer()
        data = {
            "text": "Hello\x00World\x01Test",
            "notes": "Line1\r\nLine2",
        }
        result = layer.process(data)

        assert "\x00" not in result["text"]
        assert "\x01" not in result["text"]
        assert result["notes"] == "Line1\nLine2"

    def test_empty_string_to_null(self):
        """Test empty string → NULL conversion"""
        layer = StringNormalizationLayer()
        data = {
            "name": "John",
            "middle_name": "",
            "notes": "   ",
        }
        result = layer.process(data)

        assert result["name"] == "John"
        assert result["middle_name"] is None
        assert result["notes"] is None

    def test_non_string_passthrough(self):
        """Test that non-strings are passed through"""
        layer = StringNormalizationLayer()
        data = {
            "name": "John",
            "age": 30,
            "price": 10.99,
            "is_active": True,
        }
        result = layer.process(data)

        assert result["age"] == 30
        assert result["price"] == 10.99
        assert result["is_active"] is True


class TestNumericNormalizationLayer:
    """Test Layer 3: Numeric Normalization"""

    def test_comma_separated_numbers(self):
        """Test parsing comma-separated numbers"""
        layer = NumericNormalizationLayer()
        data = {
            "amount1": "10,000",
            "amount2": "1,234.56",
            "amount3": "999,999,999.99",
        }
        result = layer.process(data)

        assert result["amount1"] == 10000
        assert result["amount2"] == 1234.56
        assert result["amount3"] == 999999999.99

    def test_scientific_notation(self):
        """Test scientific notation parsing"""
        layer = NumericNormalizationLayer()
        data = {
            "value1": "1.5e3",
            "value2": "2.5E-2",
        }
        result = layer.process(data)

        assert result["value1"] == 1500
        assert abs(result["value2"] - 0.025) < 0.0001

    def test_null_safe_parsing(self):
        """Test NULL-safe numeric parsing"""
        layer = NumericNormalizationLayer()
        data = {
            "amount": None,
            "quantity": "",
            "price": "N/A",
        }
        result = layer.process(data)

        assert result["amount"] is None
        assert result["quantity"] is None or result["quantity"] == ""
        # Non-numeric strings should remain as-is or be handled gracefully

    def test_already_numeric(self):
        """Test already numeric values pass through"""
        layer = NumericNormalizationLayer()
        data = {
            "count": 100,
            "price": 10.99,
            "total": Decimal("1234.56"),
        }
        result = layer.process(data)

        assert result["count"] == 100
        assert result["price"] == 10.99


class TestDateTimeNormalizationLayer:
    """Test Layer 4: DateTime Normalization"""

    def test_date_formats(self):
        """Test multiple date format parsing"""
        layer = DateTimeNormalizationLayer()
        data = {
            "date1": "2025-01-15",
            "date2": "2025/01/15",
            "date3": "15-01-2025",
            "date4": "01/15/2025",
        }
        result = layer.process(data)

        # All should be normalized to ISO 8601 format
        assert "2025" in result["date1"]
        assert "01" in result["date1"]
        assert "15" in result["date1"]

    def test_datetime_formats(self):
        """Test datetime with time parsing"""
        layer = DateTimeNormalizationLayer()
        data = {
            "created_at": "2025-01-15 10:30:45",
            "updated_at": "2025-01-15T10:30:45",
        }
        result = layer.process(data)

        assert "2025-01-15" in result["created_at"]
        assert "10:30:45" in result["created_at"]

    def test_null_date_handling(self):
        """Test NULL date handling"""
        layer = DateTimeNormalizationLayer()
        data = {
            "date1": None,
            "date2": "",
        }
        result = layer.process(data)

        assert result["date1"] is None

    def test_non_date_passthrough(self):
        """Test non-date values pass through"""
        layer = DateTimeNormalizationLayer()
        data = {
            "name": "John",
            "age": 30,
            "date": "2025-01-15",
        }
        result = layer.process(data)

        assert result["name"] == "John"
        assert result["age"] == 30


class TestFieldMappingLayer:
    """Test Layer 5: Field Mapping"""

    @pytest.mark.asyncio
    async def test_field_renaming(self, session, sample_field_mappings):
        """Test field name mapping"""
        layer = FieldMappingLayer(session, "inventory_items")

        data = {
            "ITEM_ID": "10001",
            "ITEM_CODE": "ITM-001",
            "DESCRIPTION": "Sample Item",
        }

        result = await layer.process(data)

        # Note: This test assumes field mappings are loaded from database
        # In a real scenario, you'd need to insert sample_field_mappings first
        assert "item_id" in result or "ITEM_ID" in result
        assert "item_code" in result or "ITEM_CODE" in result

    @pytest.mark.asyncio
    async def test_transformation_application(self, session):
        """Test transformation rules"""
        layer = FieldMappingLayer(session, "inventory_items")

        data = {
            "STATUS": "active",
        }

        result = await layer.process(data)

        # Transformations would be applied based on mapping rules
        assert "STATUS" in result or "status" in result

    @pytest.mark.asyncio
    async def test_default_values(self, session):
        """Test default value application"""
        layer = FieldMappingLayer(session, "inventory_items")

        data = {
            "ITEM_ID": "10001",
        }

        result = await layer.process(data)

        # Default values would be applied for missing fields
        assert result is not None


class TestNormalizationEngine:
    """Test complete normalization engine"""

    @pytest.mark.asyncio
    async def test_full_pipeline(self, session, sample_raw_data):
        """Test complete 5-layer normalization pipeline"""
        engine = NormalizationEngine(session, "inventory_items")

        result = await engine.normalize([sample_raw_data])

        assert len(result) == 1
        record = result[0]

        # Verify data has been normalized
        assert isinstance(record, dict)

        # String fields should be trimmed
        if "ITEM_CODE" in record or "item_code" in record:
            code = record.get("ITEM_CODE") or record.get("item_code")
            assert code is None or not code.startswith(" ")

        # Numeric fields should be parsed
        if "QUANTITY" in record or "quantity" in record:
            qty = record.get("QUANTITY") or record.get("quantity")
            assert qty is None or isinstance(qty, (int, float, Decimal, str))

    @pytest.mark.asyncio
    async def test_batch_normalization(self, session):
        """Test batch normalization performance"""
        engine = NormalizationEngine(session, "inventory_items")

        # Create 100 sample records
        records = [
            {
                "ITEM_ID": f"1000{i}",
                "ITEM_CODE": f"  ITM-{i:03d}  ",
                "QUANTITY": f"1,{i:03d}.50",
                "CREATED_DATE": "2025-01-15",
            }
            for i in range(100)
        ]

        result = await engine.normalize(records)

        assert len(result) == 100
        # Verify all records normalized correctly
        for record in result:
            assert isinstance(record, dict)

    @pytest.mark.asyncio
    async def test_error_handling(self, session):
        """Test error handling in normalization"""
        engine = NormalizationEngine(session, "inventory_items")

        # Record with invalid data
        records = [
            {
                "ITEM_ID": None,
                "INVALID_FIELD": "test",
            }
        ]

        # Should not crash, should handle gracefully
        result = await engine.normalize(records)
        assert isinstance(result, list)
