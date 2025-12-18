"""
Test Configuration and Fixtures

Provides shared fixtures for pytest test suite.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.db.base import metadata
from app.core.config import settings


# Test database URL (override with test database)
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/test_syncflow_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create schema
    async with engine.begin() as conn:
        await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.POSTGRES_SCHEMA}")
        await conn.run_sync(metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def sample_raw_data():
    """Sample raw data from APISmith"""
    return {
        "ITEM_ID": "10001",
        "ITEM_CODE": "  ITM-001  ",
        "DESCRIPTION": "Sample Item\r\nWith newline",
        "QUANTITY": "1,234.56",
        "PRICE": "10.50",
        "STATUS": "ACTIVE",
        "CREATED_DATE": "2025-01-15",
        "UPDATED_DATE": "2025-01-15 10:30:45",
        "IS_ACTIVE": "Y",
        "NOTES": None,
    }


@pytest.fixture
def sample_entity_config():
    """Sample entity configuration"""
    return {
        "entity_name": "inventory_items",
        "connector_api_slug": "oracle-erp-items",
        "business_key_fields": ["ITEM_ID", "ITEM_CODE"],
        "sync_enabled": True,
        "sync_schedule": "0 */6 * * *",
        "parent_refs_config": {
            "site": {
                "parent_entity": "sites",
                "parent_field": "site_id",
                "child_field": "site_id",
            }
        },
    }


@pytest.fixture
def sample_normalized_data():
    """Sample normalized data"""
    return {
        "item_id": "10001",
        "item_code": "ITM-001",
        "description": "Sample Item With newline",
        "quantity": 1234.56,
        "price": 10.50,
        "status": "ACTIVE",
        "created_date": "2025-01-15T00:00:00",
        "updated_date": "2025-01-15T10:30:45",
        "is_active": True,
        "notes": None,
    }


@pytest.fixture
def sample_field_mappings():
    """Sample field mappings configuration"""
    return [
        {
            "entity_name": "inventory_items",
            "source_field": "ITEM_ID",
            "target_field": "item_id",
            "transformation": None,
            "is_required": True,
        },
        {
            "entity_name": "inventory_items",
            "source_field": "ITEM_CODE",
            "target_field": "item_code",
            "transformation": "trim",
            "is_required": True,
        },
        {
            "entity_name": "inventory_items",
            "source_field": "DESCRIPTION",
            "target_field": "description",
            "transformation": "normalize_whitespace",
            "is_required": False,
        },
    ]


@pytest.fixture
def sample_sync_batch_data():
    """Sample sync batch data"""
    return {
        "entity_name": "inventory_items",
        "sync_type": "realtime",
        "status": "running",
        "total_records": 1000,
        "connector_api_slug": "oracle-erp-items",
    }
